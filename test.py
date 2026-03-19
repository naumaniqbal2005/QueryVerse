import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("mydb.db")
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT * FROM Admins ")
tables = cursor.fetchall()
print("Admins in DB:", tables)  # should list all 12 tables



conn.close()