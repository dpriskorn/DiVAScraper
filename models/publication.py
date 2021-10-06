import json
import logging
from datetime import datetime
from enum import Enum
from typing import List, Dict

import requests
from dateutil.parser import isoparse

record_url = "http://www.diva-portal.org/smash/record.jsf"


class Type(Enum):
    ARTICLE_JOURNAL = "article-journal"
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


class Publication:
    abstract: str = None
    authors: List[Dict[str, str]] = None
    diva_id: str = None
    doi: str = None
    issn: str = None
    keywords: List[str] = None
    publication_date: datetime = None
    status: Status = None
    title: str = None
    type: Type = None
    urn_nbn: str = None

    def __init__(self, diva_id: str = None):
        if diva_id is None:
            raise ValueError("got no diva_id")
        else:
            self.diva_id = diva_id
            self.__fetch_json__()

    def __str__(self):
        return f"title:{self.title}\n" \
               f"diva_id:{self.diva_id}\n" \
               f"date:{self.publication_date}"

    def __fetch_json__(self):
        def parse_authors(first_result):
            if "author" in first_result.keys():
                self.authors = []
                for author in first_result["author"]:
                    author_dict = {}
                    if "family" in author.keys():
                        author_dict["family_name"] = author["family"]
                    if "given" in author.keys():
                        author_dict["given_name"] = author["given"]
                    if "ORCID" in author.keys():
                        author_dict["orcid"] = author["ORCID"]
            else:
                logger.warning("no authors found")

        def parse_identifiers(first_result):
            if "NBN" in first_result.keys():
                self.urn_nbn = first_result["NBN"]
            if "DOI" in first_result.keys():
                self.doi = first_result["DOI"]

        def parse_keywords(first_result):
            if "keyword" in first_result.keys():
                self.keywords = []
                for keyword in first_result["keyword"].split("; "):
                    self.keywords.append(keyword)

        def parse_medium(first_result):
            """Book, Academic journal, etc."""
            if "ISSN" in first_result.keys():
                self.issn = first_result["ISSN"]
            if "publisher" in first_result.keys():
                self.publisher = first_result["publisher"]
            if "published" in first_result.keys():
                self.publication_date = isoparse(first_result["published"][0]["raw"])

        def parse_response(json: dict):
            first_result = json[0]
            print(first_result.keys())
            # Always present
            self.type = Type(first_result["type"])
            if "status" in first_result.keys():
                self.status = Status(first_result["status"])
            self.title = first_result["title"]
            parse_authors(first_result)
            parse_identifiers(first_result)
            parse_keywords(first_result)
            parse_medium(first_result)

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
            # fix control character bug in www.diva-portal.org/smash/export.jsf?format=csl_json&addFilename=true&aq=[[{%22id%22:%22diva2:1600051%22}]]&aqe=[]&aq2=[[]]&onlyFullText=false&noOfRows=50&sortOrder=title_sort_asc&sortOrder2=title_sort_asc
            response_text = response_text.replace("\n", "")\
            # fix \escape bug in www.diva-portal.org/smash/export.jsf?format=csl_json&addFilename=true&aq=[[{%22id%22:%22diva2:1599119%22}]]&aqe=[]&aq2=[[]]&onlyFullText=false&noOfRows=50&sortOrder=title_sort_asc&sortOrder2=title_sort_asc
            response_text = response_text.replace("\p","p")
            # fix escape www.diva-portal.org/smash/export.jsf?format=csl_json&addFilename=true&aq=[[{%22id%22:%22diva2:1596811%22}]]&aqe=[]&aq2=[[]]&onlyFullText=false&noOfRows=50&sortOrder=title_sort_asc&sortOrder2=title_sort_asc
            response_text = response_text.replace("\%","%")
            response_text = response_text.replace("\t", " ")
            parse_response(json.loads(response_text))
        else:
            raise Exception(f"got {response.status_code} from DiVa")
