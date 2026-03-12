import sqlite3
import random
from datetime import datetime, timedelta
import os

db_path = os.path.join(os.path.dirname(__file__), "sales.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS regions;

CREATE TABLE regions (
    region_id INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    email TEXT,
    region_id INTEGER,
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    total_amount REAL,
    sale_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
""")

regions = [(1,"North"),(2,"South"),(3,"East"),(4,"West")]
cur.executemany("INSERT INTO regions VALUES (?,?)", regions)

products = [
    (1,"Laptop","Electronics",999.99),
    (2,"Mouse","Electronics",29.99),
    (3,"Keyboard","Electronics",79.99),
    (4,"Desk","Furniture",349.99),
    (5,"Chair","Furniture",199.99),
    (6,"Monitor","Electronics",299.99),
    (7,"Notebook","Stationery",4.99),
    (8,"Pen Set","Stationery",9.99),
    (9,"Headphones","Electronics",149.99),
    (10,"Webcam","Electronics",89.99),
]
cur.executemany("INSERT INTO products VALUES (?,?,?,?)", products)

names = ["Alice","Bob","Charlie","Diana","Eve","Frank","Grace","Hank","Ivy","Jack",
         "Karen","Leo","Mia","Ned","Olivia","Paul","Quinn","Rose","Sam","Tina"]
customers = [(i+1, names[i], f"{names[i].lower()}@email.com", random.randint(1,4)) for i in range(20)]
cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)

random.seed(42)
base = datetime(2023,1,1)
sale_id = 1
rows = []
for _ in range(500):
    date = base + timedelta(days=random.randint(0,364))
    cid = random.randint(1,20)
    pid = random.randint(1,10)
    qty = random.randint(1,10)
    price = products[pid-1][3]
    rows.append((sale_id, cid, pid, qty, round(qty*price,2), date.strftime("%Y-%m-%d")))
    sale_id += 1

cur.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?)", rows)
conn.commit()
conn.close()
print(f"✅ sales.db created at {db_path} with 500 sales records")