# Используем pydantic для упрощения работы
# при перегонке данных из json в объекты
from typing import Optional

from pydantic import BaseModel


class FilmCommon(BaseModel):
    id: str = ""
    imdb_rating: Optional[float] = None
    title: Optional[str] = None


class FilmList(BaseModel):
    films: list[FilmCommon] = []


class GenreCommon(BaseModel):
    uuid: str = ""
    name: Optional[str] = None


class PersonCommon(BaseModel):
    id: str = ""
    full_name: Optional[str] = None


class Access(BaseModel):
    privilege: Optional[str] = None


class Genre(GenreCommon, FilmList):
    description: Optional[str] = None


class FilmOfPerson(FilmCommon):
    roles: list[str] = []


class Person(PersonCommon):
    films: list[FilmOfPerson] = []


class Film(FilmCommon):
    description: Optional[str] = None
    genres: list[GenreCommon] = []
    directors: list[PersonCommon] = []
    actors: list[PersonCommon] = []
    writers: list[PersonCommon] = []
    access: list[Access] = []


class PersonList(BaseModel):
    persons: list[Person] = []


class GenreList(BaseModel):
    genres: list[GenreCommon] = []
