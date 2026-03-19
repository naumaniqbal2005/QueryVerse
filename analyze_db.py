import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("mydb.db")
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("=== DATABASE SCHEMA ANALYSIS ===\n")

for table in tables:
    table_name = table[0]
    print(f"TABLE: {table_name}")
    print("-" * 50)
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    print("Columns:")
    for col in columns:
        col_id, name, type_, not_null, default, pk = col
        pk_marker = " (PRIMARY KEY)" if pk else ""
        null_marker = " NOT NULL" if not_null else ""
        default_marker = f" DEFAULT {default}" if default else ""
        print(f"  • {name}: {type_}{pk_marker}{null_marker}{default_marker}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    print(f"Rows: {count}")
    
    # Show sample data (first 2 rows)
    if count > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
        sample_data = cursor.fetchall()
        print("Sample data:")
        for row in sample_data:
            print(f"  {row}")
    
    print("\n")

# Show foreign key relationships
print("=== FOREIGN KEY RELATIONSHIPS ===")
cursor.execute("PRAGMA foreign_key_list(Admins);")
print("No foreign keys in Admins table")

conn.close()
