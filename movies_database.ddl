CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.film_work (
    id uuid PRIMARY KEY,
    title varchar(255) NOT NULL,
    description TEXT,
    creation_date DATE,
    rating FLOAT,
    type varchar(255),
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.genre (
    id uuid PRIMARY KEY,
    name varchar(255) NOT NULL,
    description TEXT,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.person (
    id uuid PRIMARY KEY,
    full_name varchar(255) NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id uuid PRIMARY KEY,
    genre_id uuid NOT NULL REFERENCES content.genre (id) ON DELETE CASCADE,
    film_work_id uuid NOT NULL REFERENCES content.film_work (id) ON DELETE CASCADE,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX film_work_genre_idx ON content.genre_film_work (film_work_id, genre_id);

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL REFERENCES content.film_work (id) ON DELETE CASCADE,
    person_id uuid NOT NULL REFERENCES content.person (id) ON DELETE CASCADE,
    role varchar(255) NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX film_work_person_idx ON content.person_film_work (film_work_id, person_id, role);