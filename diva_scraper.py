#!/usr/bin/env python3

import logging

from models import DivaScraper

logging.basicConfig(level=logging.WARNING)


if __name__ == '__main__':
    ds = DivaScraper()
    ds.start()
