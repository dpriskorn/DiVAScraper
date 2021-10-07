import json
import logging
from datetime import datetime
from enum import Enum
from typing import List, Dict, Union

import backoff
import requests
from dateutil.parser import isoparse

record_url = "http://www.diva-portal.org/smash/record.jsf"


class Type(Enum):
    ARTICLE_JOURNAL = "article-journal"
    ARTICLE_NEWSPAPER = "article-newspaper"
    BOOK = "book"
    CHAPTER = "chapter"
    CONFERENCE_PAPER = "paper-conference"
    DATASET = "dataset"
    DISSERTATION = "dissertation"
    MANUSCRIPT = "manuscript"
    REPORT = "report"
    REVIEW = "review"
    REVIEW_BOOK = "review-book"
    SONG = "song"
    SPEECH = "speech"
    THESIS = "thesis"


class Status(Enum):
    PUBLISHED = "Published"
    EPUB_AHEAD_OF_PRINT = "Epub ahead of print"
    IN_PRESS = "In press"
    ACCEPTED = "Accepted"
    SUBMITTED = "Submitted"


class Language(Enum):
    ENGLISH = "eng"
    SWEDISH = "swe"
    DANISH = "dan"
    LATIN = "lat"
    ICELANDIC = "ice"
    FAROESE = "fao"
    GREENLANDIC = "kal"
    FINNISH = "fin"
    NORWEGIAN = "nor"
    SPANISH = "spa"
    HUNGARIAN = "hun"


class Publication:
    abstract: str = None
    affiliations: List[str] = None
    authors: List[Dict[str, Union[str, Dict]]] = None
    container_title: str = None
    diva_id: str = None
    doi: str = None
    funding_agencies: List[str] = None
    issn: str = None
    keywords: List[str] = None
    language: Language = None
    # Notes often contain information about funding.
    note: str = None
    number: str = None
    number_of_pages: str = None
    page: str = None
    pubmed_id: str = None
    publication_date: datetime = None
    publisher: str = None
    supervisor: str = None
    status: Status = None
    title: str = None
    type: Type = None
    urn_nbn: str = None
    volume: str = None

    def __init__(self, diva_id: str = None):
        if diva_id is None:
            raise ValueError("got no diva_id")
        else:
            self.diva_id = diva_id
            self.__fetch_json__()

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException)
    def __fetch_json__(self):
        logger = logging.getLogger(__name__)
        # This syntax was found via
        # http://www.diva-portal.org/smash/builder.jsf?searchType=FEED&dswid=-4917
        export_url = "http://www.diva-portal.org/smash/export.jsf"
        query = (f"?format=csl_json&addFilename=true&aq="
                 f'[[{{"id":"{self.diva_id}"}}]]'
                 f'&aqe=[]&aq2=[[]]&onlyFullText=false&noOfRows=50&'
                 f'sortOrder=title_sort_asc&sortOrder2=title_sort_asc')
        url = export_url + query
        logger.info(f"Fetching {url}")
        response = requests.get(url)
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
                self.authors = []
                for author in publication["author"]:
                    author_dict = {}
                    if "family" in author.keys():
                        author_dict["family_name"] = author["family"]
                    if "given" in author.keys():
                        author_dict["given_name"] = author["given"]
                    if "affiliation" in author.keys():
                        logger.info("Found affiliation")
                        affiliations = author["affiliation"]
                        affiliations_list = []
                        for affiliation in affiliations:
                            affiliation_dict = {}
                            if "name" in affiliation:
                                affiliation_dict["name"] = affiliation["name"]
                            # TODO find out where we can get more information on this id,
                            #  where does it come from?
                            if "id" in affiliation:
                                affiliation_dict["id"] = affiliation["id"]
                            affiliations_list.append(affiliation_dict)
                        author_dict["affiliation"] = affiliations_list
                    if "ORCID" in author.keys():
                        author_dict["orcid"] = author["ORCID"]
                    self.authors.append(author_dict)
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
                self.keywords = []
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

        logger = logging.getLogger(__name__)
        first_publication = json[0]
        if first_publication is not None:
            logger.debug(first_publication.keys())
            # Always present
            if "type" in first_publication.keys():
                self.type = Type(first_publication["type"])
            if "status" in first_publication.keys():
                self.status = Status(first_publication["status"])
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

    def __str__(self):
        def parse_authors():
            if self.authors is not None and len(self.authors) > 0:
                authors = []
                for author in self.authors:
                    author_string = ""
                    if "given_name" in author.keys():
                        author_string = author_string + author["given_name"]
                    if "family_name" in author.keys():
                        author_string = f'{author_string} {author["family_name"]}'
                    if "orcid" in author.keys():
                        author_string = f'{author_string} ({author["orcid"]})'
                    if "affiliation" in author.keys():
                        affiliations = []
                        for affiliation in author["affiliation"]:
                            affiliation_string = ""
                            if "name" in affiliation:
                                affiliation_string = f'{affiliation_string + affiliation["name"]}'
                            if "id" in affiliation:
                                affiliation_string = f'{affiliation_string} id:{affiliation["id"]}'
                            affiliations.append(affiliation_string)
                        author_string = f'{author_string} [{"; ".join(affiliations)}]'
                    authors.append(author_string)
                return "; ".join(authors)
            else:
                return None

        def parse_keywords():
            if self.keywords is not None and len(self.keywords) > 0:
                return "; ".join(self.keywords)
            else:
                # logger.warning("no keywords found")
                return None

        logger = logging.getLogger(__name__)
        # logger.debug(self.title)
        keywords = parse_keywords()
        authors = parse_authors()
        return (
            f"title:{self.title}\n"
            f"authors: {authors}\n"
            f"supervisor: {self.supervisor}\n"
            f"keywords: {keywords}\n"
            f"lang: {self.language.name}\n"
            f"doi: {self.doi_url()}\n"
            f"pubmed_id: {self.pubmed_url()}\n"
            # f"diva_id: {self.diva_id}\n"
            f"date: {self.publication_date}\n"
            f"publisher: {self.publisher}\n"
            f"volume: {self.volume} page: {self.page} number: {self.number}\n"
            f"note: {self.note}\n"
            f"abstract: {self.abstract[:50]}"
        )

    def doi_url(self):
        if self.doi is not None:
            return f"https://doi.org/{self.doi}"
        else:
            return None

    def pubmed_url(self):
        if self.pubmed_id is not None:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pubmed_id}"
        else:
            return None