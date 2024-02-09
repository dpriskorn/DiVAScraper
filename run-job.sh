cd ~/divascraper
python -m ensurepip --upgrade
pip install poetry
poetry install --no-interaction --no-cache
python3 diva_scraper.py