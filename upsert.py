import chardet
import pandas as pd
from dotenv import load_dotenv

# 먼저 파일의 인코딩을 감지
with open('pd_output2_adjusted.csv', 'rb') as f:
    result = chardet.detect(f.read())
    print(result)

# 감지된 인코딩으로 읽기
df = pd.read_csv('pd_output2_adjusted.csv', encoding=result['encoding'])
print(df.head())

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

# data to list in dict
data = df.to_dict(orient='records')

# sql query 
sql = """INSERT INTO public.financialstatements6 (
    idx, name, company_code, industry, size, year, established_date, ceo,
    debt_ratio, assets, sales_growth, current_ratio, quick_ratio,
    inventory_turnover, receivables_turnover, asset_turnover, fixed_asset_turnover,
    operating_cf, operating_cf_to_assets, operating_cf_to_debt,
    industry_avg_roe, industry_avg_roa, industry_avg_debt_ratio,
    roa, roic, division, employee_growth_rate, roe,
    operating_cf_to_sales, profit_growth, optl, ffoeq, oeneg, cfoint,
    accounts_payable_turnover, interest_coverage_ratio, noncurrent_asset_turnover,
    industry_avg_pd, pd, score, grade
) VALUES (
    %(idx)s, %(name)s, %(company_code)s, %(industry)s, %(size)s, %(year)s, %(established_date)s, %(ceo)s,
    %(debt_ratio)s, %(assets)s, %(sales_growth)s, %(current_ratio)s, %(quick_ratio)s,
    %(inventory_turnover)s, %(receivables_turnover)s, %(asset_turnover)s, %(fixed_asset_turnover)s,
    %(operating_cf)s, %(operating_cf_to_assets)s, %(operating_cf_to_debt)s,
    %(industry_avg_roe)s, %(industry_avg_roa)s, %(industry_avg_debt_ratio)s,
    %(roa)s, %(roic)s, %(division)s, %(employee_growth_rate)s, %(roe)s,
    %(operating_cf_to_sales)s, %(profit_growth)s, %(optl)s, %(ffoeq)s, %(oeneg)s, %(cfoint)s,
    %(accounts_payable_turnover)s, %(interest_coverage_ratio)s, %(noncurrent_asset_turnover)s,
    %(industry_avg_pd)s, %(pd)s, %(score)s, %(grade)s
);"""

# db 연결 진행
cur = conn.cursor()
cur.executemany(sql, data)
conn.commit()
cur.close()
conn.close()
