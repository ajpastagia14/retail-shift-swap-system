import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS managers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT,
    skill TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS shifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    skill TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS swap_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    shift_id INTEGER,
    replacement_employee TEXT,
    reason TEXT,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (shift_id) REFERENCES shifts(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    day TEXT,
    from_time TEXT,
    to_time TEXT,
    status TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
)
""")

# Insert test employees only if they do not already exist
cursor.execute("SELECT * FROM employees WHERE email = ?", ("john@test.com",))
john = cursor.fetchone()

if not john:
    cursor.execute("""
    INSERT INTO employees (name, email, password, role, skill, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("John", "john@test.com", "123", "Cashier", "POS", "Active"))

cursor.execute("SELECT * FROM employees WHERE email = ?", ("sarah@test.com",))
sarah = cursor.fetchone()

if not sarah:
    cursor.execute("""
    INSERT INTO employees (name, email, password, role, skill, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("Sarah", "sarah@test.com", "123", "Staff", "Floor", "Active"))

cursor.execute("""
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Database and tables created successfully.")