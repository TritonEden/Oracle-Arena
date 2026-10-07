from modules import *
import sqlalchemy
from sqlalchemy import text

#Env vars: again, no need for a library here
env_vars = {}
with open(".env") as f:
    for line in f:
        key, value = line.strip().split('=', 1)
        env_vars[key] = value

host = env_vars.get("POSTGRES_HOST", "localhost")
port = env_vars.get("POSTGRES_PORT", "5432")
db_name = env_vars.get("POSTGRES_DB", "oracle_arena")
user = env_vars.get("POSTGRES_USER", "postgres")
password = env_vars.get("POSTGRES_PASSWORD", "password")

#If any are defaults, print a warning
if password == "password":
    print("Warning: password is set to default value. Please change it in the .env file.")

DATABASE_URL = get_database_url(host, password, user, port, db_name)
# print(f"Connecting to database at {DATABASE_URL}")

engine = sqlalchemy.create_engine(DATABASE_URL)
connection = engine.connect()

print("Updating each and every materialized view...")

with engine.connect() as connection:
    #Get all materialized views
    result = connection.execute(text("""
        SELECT matviewname FROM pg_matviews;
    """))
    matviews = result.fetchall()

    for matview in matviews:
        matview_name = matview[0]
        print(f"Refreshing materialized view: {matview_name}")
        connection.execute(text(f"REFRESH MATERIALIZED VIEW {matview_name};"))
    connection.commit()
print("All materialized views updated.")
