"""This script downloads all links from the latest publications in DiVA

Currently a total of ~88.000 links can be fetched this way,
but they are not stable, so we only use them to download the
publication page and extract from there.

All publications in DiVA have a URN, some have DOI and none have ORCID

Next step is to parse the publication pages"""
#!/usr/bin/env python3
import logging
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from models.publication import Publication

logging.basicConfig(level=logging.INFO)

base_url = "http://www.diva-portal.org"
record_url = "http://www.diva-portal.org/smash/record.jsf"


def main():
    latest_url = "http://www.diva-portal.org/smash/latest.jsf?dswid=-9944"
    # has 1765 pages with 50 publications each.
    # &p=1 <- first page
    # &p=51 <- second page
    total_publications = 1765*50
    print(f"There are a total of {total_publications} latest publications to scrape")
    for i in range(1301,total_publications,50):
        print(i)
        response = requests.get(f"{latest_url}&p={i}")
        if response.status_code == 200:
            print(response.text[:50])
            parse_response(response)
        else:
            raise Exception(f"got {response.status_code} from DiVa")
        # if i == 1:
        #     break


def parse_response(response):
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
                print(publication)
                # break


if __name__ == '__main__':
    main()
