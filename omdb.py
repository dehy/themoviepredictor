import requests
import os
from datetime import datetime
from movie import Movie


class OMDBApi:

    ENDPOINT = "www.omdbapi.com"
    DEFAULT_QUERY_PARAMS = {}

    def __init__(self):
        api_key = os.environ["OMDB_API_KEY"]
        self.query_params = {
            "apikey": api_key
        }
        self.query_params.update(OMDBApi.DEFAULT_QUERY_PARAMS)

    def get_movie(self, imdb_id):
        params = self.query_params
        params.update({
            "i": imdb_id
        })
        response = requests.get(f"https://{OMDBApi.ENDPOINT}/", params=params)
        print(response.url)
        print(response.content)
        if (response.status_code != 200):
            print("Error in request")
            return None
        dict_response = response.json()
        return self.movie_from_json(dict_response)

    def movie_from_json(self, dict_movie):
        title = None
        original_title = dict_movie['Title']
        duration = None
        release_date = datetime.strptime(dict_movie['Released'], '%d %B %Y')
        rating = dict_movie['Rated']
        if rating == "PG-13":
            rating = "-12"
        synopsis = dict_movie['Plot']

        movie = Movie(title, original_title, duration, release_date, rating)
        movie.synopsis = synopsis

        print(movie.__dict__)

        return movie
