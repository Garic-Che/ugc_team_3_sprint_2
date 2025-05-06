import psycopg2
import backoff

from helpers import DBSettings


@backoff.on_exception(
    backoff.expo, exception=psycopg2.OperationalError, max_time=60
)
def is_pinging(connection):
    cur = connection.cursor()
    cur.execute("SELECT 1")


if __name__ == "__main__":
    db_settings = DBSettings()
    connection = psycopg2.connect(
        dbname=db_settings.pg_db,
        user=db_settings.pg_user,
        password=db_settings.pg_password,
        host=db_settings.pg_host,
        port=db_settings.pg_port,
    )
    is_pinging(connection)
