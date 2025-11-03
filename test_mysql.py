import pymysql

# MySQL 
conn = pymysql.connect(
    host="nozomi.proxy.rlwy.net",
    user="root",
    password="hWVJzgHUIDxwUSggufvqGWBLOEEyRIYb",
    database="railway",
    port=56063
)

cur = conn.cursor()
cur.execute("SHOW TABLES;")
tables = cur.fetchall()
print("Tables in database:", tables)

conn.close()
