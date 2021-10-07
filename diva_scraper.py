"""This script downloads all the latest publications in DiVA

Currently a total of ~1800 links can be fetched this way,
but they are not stable, so we only use them to download the
publication page and extract from there.

All publications in DiVA have a URN, some have DOI
and some authors also have ORCID
"""
#!/usr/bin/env python3
import logging
from urllib.parse import urlparse, parse_qs

import backoff as backoff
import requests
from bs4 import BeautifulSoup

from models.publication import Publication

logging.basicConfig(level=logging.WARNING)

base_url = "http://www.diva-portal.org"
record_url = "http://www.diva-portal.org/smash/record.jsf"


def scrape_latest_publications():
    latest_url = "http://www.diva-portal.org/smash/latest.jsf?dswid=-9944"
    # has 1765 pages with 50 publications each.
    # &p=1 <- first page
    # &p=51 <- second page
    total_publications = 1765
    print(f"There are a total of {total_publications} latest publications to scrape")
    for i in range(1701,total_publications,50):
        print(i)
        url = f"{latest_url}&p={i}"
        print(f"Fetching {url}")
        response = requests.get(url)
        if response.status_code == 200:
            parse_response(response)
        else:
            raise Exception(f"got {response.status_code} from DiVa")
        # if i == 1:
        #     break


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException)
def scrape_medicine_category():
    medicine_category_url = "http://www.diva-portal.org/smash/resultList.jsf?dswid=-6166&" \
                        "language=sv&searchType=SUBJECT&query=&" \
                        "af=%5B%5D&aq=%5B%5B%7B%22categoryId%22%3A%2211649%22%7D%5D%5D&aq2=%5B%5B%5D%5D&aqe=%5B%5D&" \
                        "noOfRows=250&sortOrder=author_sort_asc&sortOrder2=title_sort_asc&onlyFullText=false&sf=all"
    # has >200.000 objects.
    # &p=1 <- first page
    # &p=51 <- second page
    total_publications = 219750
    print(f"There are a total of {total_publications} medicine publications to scrape")
    for i in range(4801,total_publications,250):
        print(i)
        url = f"{medicine_category_url}&p={i}"
        print(f"Fetching {url}")
        response = requests.get(url)
        if response.status_code == 200:
            parse_response(response)
        else:
            raise Exception(f"got {response.status_code} from DiVa")
        #if i == 1:
        #    break


def main():
    scrape_medicine_category()


def parse_response(response):
    logger = logging.getLogger(__name__)
    # Parse the html response
    soup = BeautifulSoup(response.text, features="html.parser")
    search_items = soup.select("li", class_="ui-datalist-item")
    print(f"found {len(search_items)} search_items")
    for item in search_items:
        link = item.find("a", class_='titleLink')
        if link is not None:
            href = link["href"]
            # print(href)
            parsed_url = urlparse(href)
            qs = parse_qs(parsed_url.query)
            # We only care about the "pid=" part of the link
            if "pid" in qs:
                publication_id = qs["pid"]
                if len(publication_id) != 1:
                    raise ValueError(f"more than one publication_id {publication_id}")
                publication = Publication(diva_id=publication_id[0])
                if publication is None:
                    raise ValueError(f"publication object was None for {publication_id[0]}")
                # print(publication)
                try:
                    print(publication)
                except TypeError:
                    logger.error(f"could not print object for {publication_id[0]} because of TypeError")
                # break


if __name__ == '__main__':
    main()
