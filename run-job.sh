cd ~/divascraper
python3 -m ensurepip --upgrade
pip3 install poetry
poetry install --no-interaction --no-cache
python3 diva_scraper.py