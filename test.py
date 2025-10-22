import sqlite3

db_path = "users.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''select * from users''')
rows = cursor.fetchall()
for row in rows:
    print(row)