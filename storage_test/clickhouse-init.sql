CREATE DATABASE IF NOT EXISTS mydb;

CREATE TABLE IF NOT EXISTS mydb.events (
    event_date Date,
    event_time DateTime,
    user_id UInt32,
    event_type String,
    value Float64
) ENGINE = MergeTree()
ORDER BY (event_date, event_type, user_id);