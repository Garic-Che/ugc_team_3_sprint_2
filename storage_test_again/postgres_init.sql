CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL UNIQUE,
    likes_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS likes (
    user_id INT REFERENCES users(id),
    movie_id INT REFERENCES movies(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, movie_id)
);

CREATE OR REPLACE FUNCTION update_likes_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE movies
    SET likes_count = likes_count + 1
    WHERE id = NEW.movie_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS increment_likes ON likes;
CREATE TRIGGER increment_likes
AFTER INSERT ON likes
FOR EACH ROW
EXECUTE FUNCTION update_likes_count();
