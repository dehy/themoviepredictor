import requests
import os
from datetime import datetime
from movie import Movie


class TheMovieDB:

    ENDPOINT = "api.themoviedb.org/3"
    DEFAULT_QUERY_PARAMS = {
        "language": "fr-FR"
    }

    def __init__(self):
        api_key = os.environ["TMDB_API_KEY"]
        self.query_params = {
            "api_key": api_key
        }
        self.query_params.update(TheMovieDB.DEFAULT_QUERY_PARAMS)

    def get_movie(self, imdb_id):
        response = requests.get(
            f"https://{TheMovieDB.ENDPOINT}/movie/{imdb_id}", params=self.query_params)
        if (response.status_code != 200):
            print("Error in request")
            return None
        dict_response = response.json()
        return self.movie_from_json(dict_response)

    def movie_from_json(self, dict_movie):
        title = dict_movie['title']
        original_title = dict_movie['original_title']
        duration = dict_movie['runtime']
        release_date = datetime.strptime(
            dict_movie['release_date'], '%Y-%m-%d')
        rating = None
        synopsis = dict_movie['overview']
        production_budget = dict_movie['budget']

        movie = Movie(title, original_title, duration, release_date, rating)
        movie.synopsis = synopsis
        movie.production_budget = production_budget

        return movie
