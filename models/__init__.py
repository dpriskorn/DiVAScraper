import logging
from pprint import pprint
from typing import Set

from pydantic import BaseModel
from urllib.parse import urlparse, parse_qs

import backoff as backoff
import requests
from bs4 import BeautifulSoup

import config
from models.publication import Publication

logger = logging.getLogger(__name__)


class DivaScraper(BaseModel):
    """This class handles scraping of DiVA

    All publications in DiVA have a URN, some have DOI
    and some authors also have ORCID
    """
    base_url: str = "http://www.diva-portal.org"
    record_url: str = "http://www.diva-portal.org/smash/record.jsf"
    type_error_count: int = 0
    publication_count: int = 0
    institutions: Set[str] = set()

    def scrape_latest_publications(self):
        latest_url = "http://www.diva-portal.org/smash/latest.jsf?dswid=-9944"
        # has 1765 pages with 50 publications each.
        # &p=1 <- first page
        # &p=51 <- second page
        total_publications = 1765
        print(f"There are a total of {total_publications} latest publications to scrape")
        for i in range(1701, total_publications, 50):
            print(i)
            url = f"{latest_url}&p={i}"
            print(f"Fetching {url}")
            response = requests.get(url)
            if response.status_code == 200:
                self.parse_response(response)
            else:
                raise Exception(f"got {response.status_code} from DiVa")
            # if i == 1:
            #     break

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException)
    def scrape_medicine_category(self):
        # medicine_category_url = "http://www.diva-portal.org/smash/resultList.jsf?dswid=-6166&" \
        #                     "language=sv&searchType=SUBJECT&query=&" \
        #                     "af=%5B%5D&aq=%5B%5B%7B%22categoryId%22%3A%2211649%22%7D%5D%5D&aq2=%5B%5B%5D%5D&aqe=%5B%5D&" \
        #                     "noOfRows=250&sortOrder=author_sort_asc&sortOrder2=title_sort_asc&onlyFullText=false&sf=all"
        # has >200.000 objects.
        # &p=1 <- first page
        # &p=51 <- second page
        total_publications = 219750
        print(f"There are a total of {total_publications} medicine publications to scrape")
        for i in range(4801, total_publications, 250):
            print(i)
            params = {
                'aq2': '[[]]',
                'af': '[]',
                'searchType': 'SUBJECT',
                'sortOrder2': 'title_sort_asc',
                'language': 'sv',
                'aq': '[[{"categoryId":"11649"}]]',
                'p': f'{i}',
                'sf': 'all',
                'aqe': '[]',
                'sortOrder': 'author_sort_asc',
                'onlyFullText': 'false',
                'noOfRows': '250',
                'dswid': '1530',
            }

            response = requests.get('http://www.diva-portal.org/smash/resultList.jsf', params=params,
                                    headers=config.headers)
            print(f"Fetching {response.url}")
            if response.status_code == 200:
                self.parse_response(response)
                exit()
            else:
                raise Exception(f"got {response.status_code} from DiVa")
            # if i == 1:
            #    break

    def start(self):
        self.scrape_medicine_category()

    def parse_response(self, response):
        # Parse the html response
        soup = BeautifulSoup(response.text, features="html.parser")
        search_items = soup.select("li", class_="ui-datalist-item")
        print(f"found {len(search_items)} search_items")
        # exit()
        for item in search_items:
            link = item.find("a", class_='titleLink')
            if link:
                href = link["href"]
                # print(href)
                parsed_url = urlparse(href)
                qs = parse_qs(parsed_url.query)
                # We only care about the "pid=" part of the link
                if "pid" in qs:
                    publication_id = qs["pid"]
                    if len(publication_id) != 1:
                        raise ValueError(f"more than one publication_id: {publication_id}")
                    publication = Publication(diva_id=publication_id[0])
                    publication.start()
                    # if publication is None:
                    #     raise ValueError(f"publication object was None for {publication_id[0]}")
                    self.publication_count += 1
                    pprint(publication.model_dump())
                    # try:
                    #     pprint(publication.model_dump())
                    # except TypeError:
                    #     self.type_error_count += 1
                    #     logger.error(f"could not print object for {publication_id[0]} "
                    #                  f"because of TypeError, "
                    #                  f"count: {self.type_error_count}/{self.publication_count}")
                    if publication.authors:
                        for author in publication.authors:
                            if author.affiliations:
                                for affiliation in author.affiliations:
                                    self.institutions.add(affiliation.name)
                    print(
                        f"Number of institutions found: {len(self.institutions)} "
                        f"from a total of {self.publication_count} publications")
                    # pprint(institutions)

