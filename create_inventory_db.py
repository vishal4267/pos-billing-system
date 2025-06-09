import sqlite3

# Connect to or create inventory.db
conn = sqlite3.connect('inventory.db')
c = conn.cursor()

# Create inventory table
c.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL
)
''')

conn.commit()
conn.close()

print("✅ Inventory database and table created successfully.")
