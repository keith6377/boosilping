import pandas as pd
from dotenv import load_dotenv
# db connection
load_dotenv()
import os
import psycopg2

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# DB 접속 정보
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)



# db 연결 진행
cur = conn.cursor()
sql = "SELECT idx, name, grade FROM financialstatements6 LIMIT 5;"
cur.execute(sql)

rows = cur.fetchall()
for row in rows:
    print(row)

cur.close()
conn.close()
