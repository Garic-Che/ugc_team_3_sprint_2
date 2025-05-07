from typing import Optional

from pydantic import BaseModel


class FilmCommon(BaseModel):
    uuid: str = ""
    imdb_rating: Optional[float] = None
    title: Optional[str] = None


class GenreCommon(BaseModel):
    uuid: str = ""
    name: Optional[str] = None


class PersonCommon(BaseModel):
    uuid: str = ""
    full_name: Optional[str] = None


class Film(FilmCommon):
    description: Optional[str] = None
    genre: list[GenreCommon] = []
    directors: list[PersonCommon] = []
    actors: list[PersonCommon] = []
    writers: list[PersonCommon] = []


class Genre(GenreCommon):
    films: list[FilmCommon] = []


class FilmOfPerson(BaseModel):
    uuid: str
    roles: list[str]


class Person(PersonCommon):
    films: list[FilmOfPerson] = []
