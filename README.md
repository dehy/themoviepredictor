# The Move Predictor

Machine Learning Project

## Pre-requesites

- Docker
- Python 3 with pip

## Usage

1. Download all the datasets at https://datasets.imdbws.com and
   put them as-is in imdb_datasets/ directory
2. Install Python 3
3. Install required modules with `pip install -r requirements.txt`
4. Execute a MySQL/MariaDB server locally with following command: `docker-compose up`
5. Execute the script: `python app.py dataset import --year <year>` with `<year>` of your choice
