import sqlite3

# This creates a SQLite DB file called 'mydb.db' in your project folder
conn = sqlite3.connect("mydb.db")
cursor = conn.cursor()

with open("refined_script.sql", "r", encoding="utf-16") as f:
    sql_script = f.read()

cursor.executescript(sql_script)
conn.commit()
conn.close()

print("SQLite DB created successfully!")