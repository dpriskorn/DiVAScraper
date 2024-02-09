import json
import logging
from datetime import datetime
from typing import List
from urllib.parse import quote

import backoff
import requests
from dateutil.parser import isoparse
from jsonlines import jsonlines
from pydantic import BaseModel

import config
from models.affiliation import Affiliation
from models.author import Author
from models.enums import Language, PublicationStatus, PublicationType

record_url = "http://www.diva-portal.org/smash/record.jsf"
logger = logging.getLogger(__name__)


class Publication(BaseModel):
    abstract: str = ""
    affiliations: List[str] = list()
    authors: List[Author] = list()
    container_title: str = ""
    diva_id: str = ""
    doi: str = ""
    funding_agencies: List[str] = list()
    issn: str = ""
    keywords: List[str] = list()
    language: Language = None
    # Notes often contain information about funding.
    note: str = ""
    number: str = ""
    number_of_pages: str = ""
    page: str = ""
    pubmed_id: str = ""
    publication_date: datetime = None
    publisher: str = ""
    supervisor: str = ""
    status: PublicationStatus = None
    title: str = ""
    type: PublicationType = None
    urn_nbn: str = ""
    volume: str = ""

    # def __init__(self, diva_id: str = None):
    #     if diva_id is None:
    #         raise ValueError("got no diva_id")
    #     else:
    #         self.diva_id = diva_id
    #         self.__fetch_json__()

    def fetch_and_store(self):
        self.__fetch_json__()
        self.__append_to_jsonl()
        # exit()

    def __append_to_jsonl(self):
        with jsonlines.open(config.file_path, mode='a') as writer:
            writer.write(self.model_dump(mode="json"))

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException)
    def __fetch_json__(self):
        # This syntax was found via
        # http://www.diva-portal.org/smash/builder.jsf?searchType=FEED&dswid=-4917
        export_url = "http://www.diva-portal.org/smash/export.jsf"
        query = (f"?format=csl_json&addFilename=true&aq="
                 f'[[{{"id":"{self.diva_id}"}}]]'
                 f'&aqe=[]&aq2=[[]]&onlyFullText=false&noOfRows=50&'
                 f'sortOrder=title_sort_asc&sortOrder2=title_sort_asc')
        url = export_url + query
        logger.info(f"Fetching {url}")
        response = requests.get(url, headers=config.headers)
        if response.status_code == 200:
            response_text = response.text
            # fix control character bug in
            # www.diva-portal.org/smash/export.jsf?format=csl_json&addFilename=true&aq=[[{%22id%22:%22diva2:1600051%22}]]&aqe=[]&aq2=[[]]&onlyFullText=false&noOfRows=50&sortOrder=title_sort_asc&sortOrder2=title_sort_asc
            response_text = response_text.replace("\n", "") \
                # fixescape bug in
            # www.diva-portal.org/smash/export.jsf?format=csl_json&addFilename=true&aq=[[{%22id%22:%22diva2:1599119%22}]]&aqe=[]&aq2=[[]]&onlyFullText=false&noOfRows=50&sortOrder=title_sort_asc&sortOrder2=title_sort_asc
            response_text = response_text.replace("\p", "p")
            # fix escape
            # www.diva-portal.org/smash/export.jsf?format=csl_json&addFilename=true&aq=[[{%22id%22:%22diva2:1596811%22}]]&aqe=[]&aq2=[[]]&onlyFullText=false&noOfRows=50&sortOrder=title_sort_asc&sortOrder2=title_sort_asc
            response_text = response_text.replace("\\%", "%")
            response_text = response_text.replace("\o", " o")
            response_text = response_text.replace("\t", " ")
            self.__parse_response__(json.loads(response_text))
        else:
            raise Exception(f"got {response.status_code} from DiVa")

    def __parse_response__(self, json: dict):
        def parse_authors(publication):
            if "author" in publication.keys():
                logger.debug(f'author found:{publication["author"]}')
                for author_json in publication["author"]:
                    author = Author()
                    if "given" in author_json.keys():
                        author.given_name = author_json["given"]
                    if "family" in author_json.keys():
                        author.family_name = author_json["family"]
                    if "orcid" in author_json.keys():
                        author.orcid = author_json["orcid"]
                    if "affiliation" in author_json.keys():
                        logger.info("Found affiliation")
                        for affiliation_json in author_json["affiliation"]:
                            affiliation = Affiliation()
                            if "name" in affiliation_json:
                                affiliation.name = affiliation_json["name"].replace("^, ", "").strip()
                            # TODO find out where we can get more information on this id,
                            #  where does it come from?
                            if "id" in affiliation_json:
                                affiliation.id = int(affiliation_json["id"])
                            author.affiliations.append(affiliation)
                    self.authors.append(author)
            else:
                logger.warning("no authors found")

        def parse_identifiers(publication):
            if "NBN" in publication.keys():
                self.urn_nbn = publication["NBN"]
            if "DOI" in publication.keys():
                self.doi = publication["DOI"]
            if "PMID" in publication.keys():
                self.pubmed_id = publication["PMID"]

        def parse_keywords(publication):
            if "keyword" in publication.keys():
                logger.debug("parsing keywords")
                for keyword in publication["keyword"].split("; "):
                    self.keywords.append(keyword)

        def parse_abstract(publication):
            if "abstract" in publication.keys():
                self.abstract = publication["abstract"]

        def parse_medium(publication):
            """Book, Academic journal, etc."""
            if "ISSN" in publication.keys():
                self.issn = publication["ISSN"]
            if "publisher" in publication.keys():
                self.publisher = publication["publisher"]
            if "volume" in publication.keys():
                self.volume = publication["volume"]
            if "number" in publication.keys():
                self.number = publication["number"]
            if "page" in publication.keys():
                self.page = publication["page"]
            if "number-of-pages" in publication.keys():
                self.number_of_pages = publication["number-of-pages"]
            if "container-title" in publication.keys():
                self.container_title = publication["container-title"]
            if "note" in publication.keys():
                self.note = publication["note"]
            if "published" in publication.keys():
                self.publication_date = isoparse(publication["published"][0]["raw"])

        first_publication = json[0]
        if first_publication:
            logger.debug(first_publication.keys())
            # Always present
            if "type" in first_publication.keys():
                self.type = PublicationType(first_publication["type"])
            if "status" in first_publication.keys():
                self.status = PublicationStatus(first_publication["status"])
            if "language" in first_publication.keys():
                self.language = Language(first_publication["language"])
            if "title" in first_publication.keys():
                self.title = first_publication["title"]
            parse_authors(first_publication)
            parse_identifiers(first_publication)
            parse_keywords(first_publication)
            parse_medium(first_publication)
            parse_abstract(first_publication)
        else:
            raise ValueError("no publication found in the json")

    @property
    def doi_url(self):
        if self.doi:
            return f"https://doi.org/{self.doi}"
        else:
            return ""

    @property
    def pubmed_url(self):
        if self.pubmed_id:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pubmed_id}"
        else:
            return ""

    @property
    def kb_urn_url(self) -> str:
        return f"https://urn.kb.se/resolve?urn={quote(self.urn_nbn)}" if self.urn_nbn else ""
