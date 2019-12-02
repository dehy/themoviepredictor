#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TheMoviePredictor script
Author: Arnaud de Mouhy <arnaud@admds.net>
"""

import mysql.connector
import sys
import argparse
import csv
import os
import time
import socket
import gzip
import datetime

from movie import Movie
from person import Person
from genre import Genre
from themoviedb import TheMovieDB
from omdb import OMDBApi


def isOpen(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False


def connectToDatabase():
    host = 'localhost'
    while isOpen(host, 3306) == False:
        print("En attente de la BDD...")

    time.sleep(1)
    password = os.environ.get('MYSQL_PASSWORD', 'predictor')
    return mysql.connector.connect(
        user='predictor',
        password=password,
        host=host,
        database='predictor'
    )


def disconnectDatabase(cnx):
    cnx.close()


def createCursor(cnx):
    return cnx.cursor(dictionary=True)


def closeCursor(cursor):
    cursor.close()


def findQuery(table, id):
    return ("SELECT * FROM {} WHERE id = {} LIMIT 1".format(table, id))


def findAllQuery(table):
    return ("SELECT * FROM {}".format(table))


def insert_person_query(person):
    insert_stmt = (
        "INSERT INTO `people` (`imdb_id`, `name`) "
        "VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE `id` = `id`"
    )
    data = (person.imdb_id, person.name)
    return (insert_stmt, data)


def insert_movie_query(movie):
    insert_stmt = (
        "INSERT INTO `movies` (`imdb_id`, `original_title`, `duration`, `age_rating`, `release_date`, `synopsis`, `avg_rating`, `num_votes`) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE `id` = `id`"
    )
    data = (movie.imdb_id, movie.original_title, movie.duration, movie.rating,
            movie.release_date, movie.synopsis, movie.avg_rating, movie.num_votes)
    return (insert_stmt, data)


def find(table, id):
    global cnx
    cursor = createCursor(cnx)
    query = findQuery(table, id)
    cursor.execute(query)
    results = cursor.fetchall()

    entity = None
    if (cursor.rowcount == 1):
        row = results[0]
        if (table == "movies"):
            entity = Movie(
                row['original_title'],
                row['duration'],
                row['release_date'],
                row['rating']
            )

        if (table == "people"):
            entity = Person(
                row['imdb_id'],
                row['name']
            )

        entity.id = row['id']

    closeCursor(cursor)

    return entity


def findAll(table):
    global cnx
    cursor = createCursor(cnx)
    cursor.execute(findAllQuery(table))
    results = cursor.fetchall()  # liste de dictionnaires contenant des valeurs scalaires
    closeCursor(cursor)
    if (table == "movies"):
        movies = []
        for result in results:  # result: dictionnaire avec id, title, ...
            movie = Movie(
                original_title=result['original_title'],
                duration=result['duration'],
                release_date=result['release_date'],
                rating=result['rating']
            )
            movie.id = result['id']
            movies.append(movie)
        return movies

    if (table == "people"):
        people = []
        for result in results:  # result: dictionnaire avec id, title, ...
            person = Person(
                imdb_id=result['imdb_id'],
                name=result['name'],
            )
            person.id = result['id']
            people.append(person)
        return people

    if (table == "genres"):
        genres = {}
        for result in results:
            genre = Genre(name=result['name'])
            genre.id = result['id']
            genres[genre.name] = genre
        return genres


def findMovieByImdbId(imdb_id):
    global cnx
    cursor = createCursor(cnx)
    cursor.execute(("SELECT * FROM `movies` WHERE `imdb_id` = %s"), (imdb_id,))
    row = cursor.fetchone()
    closeCursor(cursor)
    movie = Movie()
    movie.id = row['id']
    return movie


def insert_person(person):
    global cnx
    cursor = createCursor(cnx)
    cursor.execute(insert_person_query(person))
    cnx.commit()
    last_id = cursor.lastrowid
    closeCursor(cursor)
    return last_id


def insert_people(people):
    global cnx
    print(f"Inserting {len(people)} person")
    last_ids = []
    cursor = createCursor(cnx)
    i = 0
    last_commit_i = 1
    for nconst, person in people.items():
        (insert_stmt, data) = insert_person_query(person)
        cursor.execute(insert_stmt, params=data)
        lastrowid = cursor.lastrowid
        if not lastrowid:
            person = findPersonByImdbId(person.imdb_id)
            lastrowid = person.id
        last_ids.append(lastrowid)
        i = i+1
        if i % 1000 == 0:
            print(f"Committing {last_commit_i} to {i}")
            cnx.commit()
            last_commit_i = i
    print(f"Commiting {last_commit_i} to {len(people)}")
    cnx.commit()
    closeCursor(cursor)
    return last_ids


def findPersonByImdbId(imdb_id):
    global cnx
    cursor = createCursor(cnx)
    cursor.execute(("SELECT * FROM `people` WHERE `imdb_id` = %s"), (imdb_id,))
    row = cursor.fetchone()
    closeCursor(cursor)
    person = Person()
    person.id = row['id']
    return person


def insert_movie(movie):
    global cnx
    cursor = createCursor(cnx)
    (insert_stmt, data) = insert_movie_query(movie)
    cursor.execute(insert_stmt, params=data)
    cnx.commit()
    last_id = cursor.lastrowid
    closeCursor(cursor)
    return last_id


def insert_movies(movies):
    global cnx
    print(f"Inserting {len(movies)} movies")
    last_ids = []
    cursor = createCursor(cnx)
    i = 0
    last_commit_i = 1
    for tconst, movie in movies.items():
        (insert_stmt, data) = insert_movie_query(movie)
        cursor.execute(insert_stmt, params=data)
        lastrowid = cursor.lastrowid
        if not lastrowid:
            movie = findMovieByImdbId(movie.imdb_id)
            lastrowid = movie.id
        last_ids.append(lastrowid)
        i = i+1
        if i % 1000 == 0:
            print(f"Committing {last_commit_i} to {i}")
            cnx.commit()
            last_commit_i = i
    print(f"Commiting {last_commit_i} to {len(movies)}")
    cnx.commit()
    closeCursor(cursor)
    return last_ids


def insert_genres(genres):
    global cnx
    print(f"Inserting {len(genres)} genres")
    last_ids = []
    cursor = createCursor(cnx)
    for genre_name, genre in genres.items():
        insert_stmt = (
            "INSERT INTO `genres` (`name`) "
            "VALUES (%s) "
            "ON DUPLICATE KEY UPDATE `id` = `id`"
        )
        data = (genre.name,)
        cursor.execute(insert_stmt, params=data)
        last_ids.append(cursor.lastrowid)
    cnx.commit()
    closeCursor(cursor)
    return last_ids


def insert_movies_genres(movies_genres):
    global cnx
    cursor = createCursor(cnx)
    for movie_genre in movies_genres:
        insert_stmt = (
            "INSERT INTO `movies_genres` (`movie_id`, `genre_id`) "
            "VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE `movie_id` = `movie_id`"
        )
        data = (movie_genre['movie_id'], movie_genre['genre_id'])
        cursor.execute(insert_stmt, params=data)
    cnx.commit()
    closeCursor(cursor)


def insert_roles(roles):
    global cnx
    cursor = createCursor(cnx)
    for role in roles:
        insert_stmt = (
            "INSERT INTO `movies_people` (`movie_id`, `person_id`, `role`) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE `role` = `role`"
        )
        data = (role['movie_id'], role['person_id'], role['role'])
        cursor.execute(insert_stmt, params=data)
    cnx.commit()
    closeCursor(cursor)


def printPerson(person):
    print("#{}: {}".format(person.id, person.name))


def printMovie(movie):
    print("#{}: {} released on {}".format(
        movie.id, movie.original_title, movie.release_date))


parser = argparse.ArgumentParser(description='Process MoviePredictor data')

parser.add_argument('context', choices=('people', 'movies', 'dataset'),
                    help='Le contexte dans lequel nous allons travailler')

action_subparser = parser.add_subparsers(title='action', dest='action')

list_parser = action_subparser.add_parser(
    'list', help='Liste les entitées du contexte')
list_parser.add_argument('--export', help='Chemin du fichier exporté')

find_parser = action_subparser.add_parser(
    'find', help='Trouve une entité selon un paramètre')
find_parser.add_argument('id', help='Identifant à rechercher')

import_parser = action_subparser.add_parser(
    'import', help='Importer des données')
import_parser.add_argument(
    '--csv', help='Chemin vers le fichier à importer', required=False)
import_parser.add_argument(
    '--api', help='Choix de l\'API à utiliser', required=False)
import_parser.add_argument(
    '--imdb_id', help='ID Imdb à  importer depuis une API', required=False)

import_parser.add_argument(
    '--dataset_dir', help='Chemin vers le dossier contenant les datasets IMDb', required=False, default='./imdb_datasets')
import_parser.add_argument('--year', help='Année à importer',
                           required=False, default=datetime.datetime.now().year)

insert_parser = action_subparser.add_parser(
    'insert', help='Insert une nouvelle entité')
known_args = parser.parse_known_args()[0]

if known_args.context == "people":
    insert_parser.add_argument(
        '--name', help='Nom de la nouvelle personne', required=True)

if known_args.context == "movies":
    insert_parser.add_argument(
        '--duration', help='Durée du film', type=int, required=True)
    insert_parser.add_argument(
        '--original-title', help='Titre original', required=True)
    insert_parser.add_argument(
        '--release-date', help='Date de sortie en France', required=True)
    insert_parser.add_argument(
        '--rating', help='Classification du film', choices=('TP', '-12', '-16'), required=True)


args = parser.parse_args()

cnx = connectToDatabase()

if args.context == "people":
    if args.action == "list":
        people = findAll("people")
        if args.export:
            with open(args.export, 'w', encoding='utf-8', newline='\n') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(people[0].__dict__.keys())
                for person in people:
                    writer.writerow(person.__dict__.values())
        else:
            for person in people:
                printPerson(person)
    if args.action == "find":
        peopleId = args.id
        person = find("people", peopleId)
        printPerson(person)
    if args.action == "insert":
        print(f"Insertion d'une nouvelle personne: {args.name}")
        person = Person(
            imdb_id=None,
            name=args.name
        )
        people_id = insert_people(person)
        print(f"Nouvelle personne insérée avec l'id '{people_id}'")

if args.context == "movies":
    if args.action == "list":
        movies = findAll("movies")
        for movie in movies:
            printMovie(movie)
    if args.action == "find":
        movieId = args.id
        movie = find("movies", movieId)
        if (movie == None):
            print(
                f"Aucun film avec l'id {movieId} n'a été trouvé ! Try Again!")
        else:
            printMovie(movie)
    if args.action == "insert":
        print(f"Insertion d'un nouveau film: {args.original_title}")
        movie = Movie(args.original_title, args.duration,
                      args.release_date, args.rating)
        movie_id = insert_movie(movie)
        print(f"Nouveau film inséré avec l'id '{movie_id}'")
    if args.action == "import":
        if args.csv:
            with open(args.csv, 'r', encoding='utf-8', newline='\n') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    movie = Movie(
                        original_title=row['original_title'],
                        duration=row['duration'],
                        rating=row['rating'],
                        release_date=row['release_date']
                    )
                    movie_id = insert_movie(movie)
                    print(f"Nouveau film inséré avec l'id '{movie_id}'")
        if args.api != None:
            imdb_id = args.imdb_id
            if args.api == "themoviedb":
                the_movie_db = TheMovieDB()
                movie = the_movie_db.get_movie(imdb_id)
            if args.api == "omdb":
                omdb_api = OMDBApi()
                movie = omdb_api.get_movie(imdb_id)
            if (movie):
                movie_id = insert_movie(movie)
                print(
                    f"'{movie.original_title}' importé depuis TheMovieDB ! Nouvel ID #{movie_id}")

if args.context == "dataset":
    if args.action == "import":
        print(f"Importing datas for year {args.year}")
        if args.dataset_dir:
            # Read files
            movies = {}
            genres_objects = findAll("genres")
            movies_genres_tmp = {}
            with gzip.open(f"{args.dataset_dir}/title.basics.tsv.gz", 'rt') as tsvfile:
                rows = csv.reader(tsvfile, delimiter='\t', quotechar=None)
                for (imdb_id, titleType, primaryTitle, originalTitle, isAdult, startYear, endYear, runtimeMinutes, genres) in rows:
                    # if (len(movies) >= 10):
                    #     break
                    if titleType != "movie" or startYear != args.year:
                        continue
                    if runtimeMinutes == "\\N":
                        runtimeMinutes = None
                    movie = Movie(
                        original_title=originalTitle,
                        duration=runtimeMinutes,
                        release_date=None,
                        rating=None
                    )
                    movie.imdb_id = imdb_id
                    if genres != '\\N':
                        movies_genres_tmp[imdb_id] = []
                        for genre_name in genres.split(','):
                            if genre_name not in genres_objects:
                                genre = Genre(genre_name)
                                genres_objects[genre_name] = genre
                            movies_genres_tmp[imdb_id].append(genre_name)
                    movies[movie.imdb_id] = movie
            with gzip.open(f"{args.dataset_dir}/title.ratings.tsv.gz", 'rt') as tsvfile:
                rows = csv.reader(tsvfile, delimiter='\t', quotechar=None)
                for (imdb_id, avgRating, numVotes) in rows:
                    if imdb_id in movies:
                        movies[imdb_id].avg_rating = avgRating
                        movies[imdb_id].num_votes = numVotes

            movies_ids = insert_movies(movies)
            i = 0
            for tconst, movie in movies.items():
                inserted_id = movies_ids[i]
                movies[tconst].id = inserted_id
                i = i + 1
            genres_ids = insert_genres(genres_objects)
            i = 0
            for genre_name, genre in genres_objects.items():
                if genre.id != None:
                    continue
                genres_objects[genre_name].id = genres_ids[i]
                i = i + 1

            movies_genres = []
            for tconst, genre_names in movies_genres_tmp.items():
                for genre_name in genre_names:
                    movie_genre = {
                        'movie_id': movies[tconst].id,
                        'genre_id': genres_objects[genre_name].id
                    }
                    movies_genres.append(movie_genre)
            # print(movies_genres)
            insert_movies_genres(movies_genres)

            people = {}
            people_roles = []
            with gzip.open(f"{args.dataset_dir}/title.crew.tsv.gz", 'rt') as title_crew_file, gzip.open(f"{args.dataset_dir}/name.basics.tsv.gz", 'rt') as name_basics_file:
                rows = csv.reader(
                    title_crew_file, delimiter='\t', quotechar=None)
                for (tconst, directors, writers) in rows:
                    # if len(people) >= 10:
                    #     break
                    if tconst not in movies:
                        continue
                    for nconst in directors.split(','):
                        if nconst == '\\N':
                            continue
                        if nconst not in people:
                            person = Person(imdb_id=nconst, name=None)
                            people[nconst] = person
                        people_roles.append({
                            'tconst': tconst,
                            'movie_id': None,
                            'nconst': nconst,
                            'person_id': None,
                            'role': 'director'
                        })
                    for nconst in writers.split(','):
                        if nconst == '\\N':
                            continue
                        if nconst not in people:
                            person = Person(imdb_id=nconst, name=None)
                            people[nconst] = person
                        people_roles.append({
                            'tconst': tconst,
                            'movie_id': None,
                            'nconst': nconst,
                            'person_id': None,
                            'role': 'writer'
                        })

                # print(people_roles)
                rows = csv.reader(name_basics_file,
                                  delimiter='\t', quotechar=None)
                for (nconst, primaryName, birthYear, deathYear, primaryProfession, knownForTitles) in rows:
                    if nconst not in people:
                        continue
                    if birthYear == '\\N':
                        birthYear = None
                    people[nconst].name = primaryName
                    people[nconst].birthYear = birthYear

            people_ids = insert_people(people)
            i = 0
            for nconst, person in people.items():
                inserted_id = people_ids[i]
                people[nconst].id = inserted_id
                i = i + 1

            for role in people_roles:
                movie_id = movies[role['tconst']].id
                person_id = people[role['nconst']].id
                role['movie_id'] = movie_id
                role['person_id'] = person_id
                # print(role)

            insert_roles(people_roles)

disconnectDatabase(cnx)
