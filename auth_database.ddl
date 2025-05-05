CREATE EXTENSION IF NOT EXISTS pg_partman;
CREATE SCHEMA IF NOT EXISTS content;
ALTER SCHEMA content OWNER TO postgres;
-- psql -U postgres -W secret -h localhost -p 5434 -d auth