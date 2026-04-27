import sqlite3
from pathlib import Path


db_path = Path(__file__).resolve().parent / "episodes.db"
conn = sqlite3.connect(db_path)
try:
    tables = [row[0] for row in conn.execute("select name from sqlite_master where type='table' order by name")]
    print(tables)
finally:
    conn.close()
