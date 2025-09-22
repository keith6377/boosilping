from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from decimal import Decimal
from dotenv import load_dotenv
import os
import uvicorn
import psycopg2
import json
import openai

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
openai.api_key = os.getenv("OPENAI_API_KEY")


# DB 접속 정보
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



# @app.get("/html", response_class=HTMLResponse)
# def html(request: Request):
#     cur = conn.cursor()
#     sql = """SELECT * FROM financialstatements6;"""
#         # # 쿼리 실행
#     # 임시저장소한테 실행해달라고 요청
#     cur.execute(sql)
#     data = cur.fetchall()

#     # # 변경사항 커밋
#     conn.commit()

#     return templates.TemplateResponse("test.html", {"request": request, "data": data[0]})

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)


#기업분석 페이지
# @app.get("/firm", response_class=HTMLResponse)
# def firm_dashboard(request: Request):
#     cur = conn.cursor()
#     sql = """
#         SELECT idx, name, industry, size, grade, year,
#                operating_cf_to_assets,
#                operating_cf_to_debt,
#                operating_cf_to_sales,
#                pd, score, debt_ratio, roe, roa, roic, assets,
#                sales_growth, profit_growth, current_ratio, quick_ratio,
#                inventory_turnover, receivables_turnover, asset_turnover,
#                fixed_asset_turnover, operating_cf, industry_avg_pd, industry_avg_roe,
#                industry_avg_roa, industry_avg_debt_ratio, gdp_growth,
#                inflation, unemployment, interest_rate,
#                company_code, stock_code, established_date, ceo
#         FROM financialstatements6;
#     """
#     cur.execute(sql)
#     rows = cur.fetchall()
#     colnames = [desc[0] for desc in cur.description]
#     cur.close()

#     def convert(value):
#         if isinstance(value, Decimal):
#             return float(value)
#         return value

#     data = [dict(zip(colnames, (convert(v) for v in row))) for row in rows]

#     firms = {}
#     for row in data:
#         key = row["idx"]
#         if key not in firms:
#             firms[key] = row.copy()
#             firms[key]["cashflow"] = {"years": [], "operating": [], "investing": [], "financing": []}
#         firms[key]["cashflow"]["years"].append(row["year"])
#         firms[key]["cashflow"]["operating"].append(row.get("operating_cf_to_assets", 0))
#         firms[key]["cashflow"]["investing"].append(row.get("operating_cf_to_debt", 0))
#         firms[key]["cashflow"]["financing"].append(row.get("operating_cf_to_sales", 0))

#         firms[key]["inventory_turnover"] = row.get("inventory_turnover") or 0
#         firms[key]["receivables_turnover"] = row.get("receivables_turnover") or 0
#         firms[key]["asset_turnover"] = row.get("asset_turnover") or 0
#         firms[key]["fixed_asset_turnover"] = row.get("fixed_asset_turnover") or 0

#     return templates.TemplateResponse(
#         "firm.html",
#         {"request": request, "companies": json.dumps(list(firms.values()), ensure_ascii=False, default=str)}
#     )

@app.get("/firm", response_class=HTMLResponse)
def firm_dashboard(request: Request):
    cur = conn.cursor()
    sql = """
        SELECT idx,name,industry,size,grade,year,operating_cf_to_assets,operating_cf_to_debt,operating_cf_to_sales,pd,score,debt_ratio,roe,roa,roic,assets,sales_growth,profit_growth,current_ratio,quick_ratio,inventory_turnover,receivables_turnover,asset_turnover,fixed_asset_turnover,operating_cf,industry_avg_pd,industry_avg_roe,industry_avg_roa,industry_avg_debt_ratio,company_code,established_date,ceo,division,employee_growth_rate,optl,ffoeq,oeneg,cfoint,accounts_payable_turnover,interest_coverage_ratio,noncurrent_asset_turnover
        FROM financialstatements6;
    """
    cur.execute(sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()

    def convert(value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    data = [dict(zip(colnames, (convert(v) for v in row))) for row in rows]

    firms = {}
    for row in data:
        key = row["idx"]
        if key not in firms:
            firms[key] = row.copy()
            firms[key]["cashflow"] = {"years": [], "operating": [], "investing": [], "financing": []}
        firms[key]["cashflow"]["years"].append(row["year"])
        firms[key]["cashflow"]["operating"].append(row.get("operating_cf_to_assets", 0))
        firms[key]["cashflow"]["investing"].append(row.get("operating_cf_to_debt", 0))
        firms[key]["cashflow"]["financing"].append(row.get("operating_cf_to_sales", 0))

        firms[key]["inventory_turnover"] = row.get("inventory_turnover") or 0
        firms[key]["receivables_turnover"] = row.get("receivables_turnover") or 0
        firms[key]["asset_turnover"] = row.get("asset_turnover") or 0
        firms[key]["fixed_asset_turnover"] = row.get("fixed_asset_turnover") or 0

    return templates.TemplateResponse(
        "firm.html",
        {"request": request, "companies": json.dumps(list(firms.values()), ensure_ascii=False, default=str)}
    )




from fastapi.responses import JSONResponse



# 기업 기본정보 (연도별)
@app.get("/api/company-info")
def get_company_info(year: str, company_id: int):
    cur = conn.cursor()
    sql = """
        SELECT name, company_code, established_date, ceo, size, industry
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """
    cur.execute(sql, (int(year), company_id))
    row = cur.fetchone()
    cur.close()

    if not row:
        return JSONResponse({})

    name, company_code, established_date, ceo, size, industry = row

    return JSONResponse({
        "name": name,
        "code": company_code,
        "established_date": str(established_date) if established_date else None,
        "ceo": ceo,
        "size": size,
        "industry": industry
    })



# 신용점수 (기업)
@app.get("/api/credit-score")
def get_credit_score(year: str, company_id: int):
    cur = conn.cursor()
    sql = 'SELECT grade, score FROM financialstatements6 WHERE "year" = %s AND idx = %s LIMIT 1;'
    cur.execute(sql, (int(year), company_id))
    row = cur.fetchone()
    cur.close()

    if row:
        grade, score = row
        if isinstance(score, Decimal):
            score = float(score)
        delta = "등급 안정" if grade == "A" else "변동 있음"
        return JSONResponse({"grade": grade, "delta": delta, "score": score})
    else:
        return JSONResponse({"grade": "-", "delta": "-", "score": 0})


# 신용점수 (업종평균)
@app.get("/api/credit-score-avg")
def get_credit_score_avg(year: str, company_id: int):
    cur = conn.cursor()
    sql = """
        -- 기업
        SELECT '기업' as label, ROUND(AVG(score),2) as value
        FROM financialstatements6
        WHERE "year" = %s AND idx = %s

        UNION ALL

        -- 업종 평균
        SELECT '업종 평균', ROUND(AVG(score),2)
        FROM financialstatements6
        WHERE "year" = %s
          AND industry = (
            SELECT industry FROM financialstatements6 
            WHERE idx = %s
            LIMIT 1
          )

        UNION ALL

        -- 규모 평균
        SELECT '규모 평균', ROUND(AVG(score),2)
        FROM financialstatements6
        WHERE "year" = %s
          AND size = (
            SELECT size FROM financialstatements6 
            WHERE idx = %s
            LIMIT 1
          )

        UNION ALL

        -- 전체 평균
        SELECT '전체 평균', ROUND(AVG(score),2)
        FROM financialstatements6
        WHERE "year" = %s
    """
    cur.execute(sql, (
        int(year), company_id,   # 기업
        int(year), company_id,   # 업종 평균
        int(year), company_id,   # 규모 평균
        int(year)                # 전체 평균
    ))
    rows = cur.fetchall()
    cur.close()

    result = [{"label": r[0], "value": float(r[1]) if r[1] is not None else 0} for r in rows]
    return JSONResponse(result)



# 부실확률 (기업별, 연도별)
@app.get("/api/pd")
def get_pd(year: str, company_id: int):
    cur = conn.cursor()

    # 기업 PD
    cur.execute("""
        SELECT pd, industry
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """, (int(year), company_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        return JSONResponse({"pd": 0.0, "industry_avg": 0.0})

    pd, industry = row

    # 업종 평균
    cur.execute("""
        SELECT AVG(pd)
        FROM financialstatements6
        WHERE year = %s AND industry = %s
    """, (int(year), industry))
    ind_pd = cur.fetchone()[0] or 0.0
    cur.close()

    return JSONResponse({
        "pd": float(pd) if pd is not None else 0.0,
        "industry_avg": float(ind_pd)
    })



# 부실확률 (기업 vs 업종 평균 vs 규모 평균, 연도별)
@app.get("/api/pd-avg")
def get_pd_avg(year: str, company_id: int):
    cur = conn.cursor()
    sql = """
        -- 기업
        SELECT '기업' as label, ROUND(AVG(pd),2) as value
        FROM financialstatements6
        WHERE year = %s AND idx = %s

        UNION ALL

        -- 업종 평균
        SELECT '업종 평균', ROUND(AVG(pd),2)
        FROM financialstatements6
        WHERE year = %s
          AND industry = (
            SELECT industry FROM financialstatements6 
            WHERE idx = %s AND year = %s
            LIMIT 1
          )

        UNION ALL

        -- 규모 평균
        SELECT '규모 평균', ROUND(AVG(pd),2)
        FROM financialstatements6
        WHERE year = %s
          AND size = (
            SELECT size FROM financialstatements6 
            WHERE idx = %s AND year = %s
            LIMIT 1
          )
    """
    cur.execute(sql, (
        int(year), company_id,      # 기업
        int(year), company_id, int(year),  # 업종 평균
        int(year), company_id, int(year)   # 규모 평균
    ))
    rows = cur.fetchall()
    cur.close()

    result = [{"label": r[0], "value": float(r[1]) if r[1] is not None else 0} for r in rows]
    return JSONResponse(result)


# 동종업계 비교 (연도별 ROE vs 부채비율)
@app.get("/api/peers")
def get_peers(year: str, company_id: int):
    cur = conn.cursor()

    # 기준 기업의 업종 가져오기 (해당 연도)
    cur.execute("""
        SELECT industry FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """, (int(year), company_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        return JSONResponse({"peers": []})
    industry = row[0]

    # 해당 연도의 같은 업종 기업들 조회 (ROE, 부채비율만)
    sql = """
        SELECT idx, name, roe, debt_ratio
        FROM financialstatements6
        WHERE year = %s AND industry = %s
    """
    cur.execute(sql, (int(year), industry))
    rows = cur.fetchall()
    cur.close()

    peers = []
    for r in rows:
        peers.append({
            "idx": r[0],
            "name": r[1],
            "roe": float(r[2]) if r[2] is not None else 0,
            "debt_ratio": float(r[3]) if r[3] is not None else 0
        })
    return JSONResponse({"peers": peers})


# 수익성·성장성 (개별기업, 연도별)
@app.get("/api/profit-growth")
def get_profit_growth(year: str, company_id: int):
    cur = conn.cursor()
    sql = """
        SELECT sales_growth, profit_growth, roe, roa, roic
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """
    cur.execute(sql, (int(year), company_id))
    row = cur.fetchone()
    cur.close()

    if not row:
        return JSONResponse({
            "sales_growth": 0, "profit_growth": 0,
            "roe": 0, "roa": 0, "roic": 0
        })

    sales_growth, profit_growth, roe, roa, roic = row
    def conv(v): return float(v) if v is not None else 0

    return JSONResponse({
        "sales_growth": conv(sales_growth),
        "profit_growth": conv(profit_growth),
        "roe": conv(roe),
        "roa": conv(roa),
        "roic": conv(roic)
    })


# 수익성·성장성 (업종평균, 연도별)
@app.get("/api/profit-growth-industry")
def get_profit_growth_industry(year: str, company_id: int):
    cur = conn.cursor()

    # 먼저 기업의 업종 찾기
    cur.execute("""
        SELECT industry
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """, (int(year), company_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        return JSONResponse({
            "sales_growth": 0, "profit_growth": 0,
            "roe": 0, "roa": 0, "roic": 0,
            "industry": None
        })
    industry = row[0]

    # 업종 평균 구하기
    sql = """
        SELECT
          AVG(sales_growth),
          AVG(profit_growth),
          AVG(roe),
          AVG(roa),
          AVG(roic)
        FROM financialstatements6
        WHERE year = %s AND industry = %s
    """
    cur.execute(sql, (int(year), industry))
    row = cur.fetchone()
    cur.close()

    sales_growth, profit_growth, roe, roa, roic = row
    def conv(v): return float(v) if v is not None else 0

    return JSONResponse({
        "sales_growth": conv(sales_growth),
        "profit_growth": conv(profit_growth),
        "roe": conv(roe),
        "roa": conv(roa),
        "roic": conv(roic),
        "industry": industry
    })


# 안정성 지표 (기업 vs 업종평균, 연도별)
@app.get("/api/solvency")
def get_solvency(year: str, company_id: int):
    cur = conn.cursor()

    # 기업 데이터
    cur.execute("""
        SELECT debt_ratio, current_ratio, quick_ratio, industry
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """, (int(year), company_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        return JSONResponse({
            "company": {"debt_ratio": 0, "current_ratio": 0, "quick_ratio": 0},
            "industry": {"debt_ratio": 0, "current_ratio": 0, "quick_ratio": 0},
            "industry_name": None
        })

    debt_ratio, current_ratio, quick_ratio, industry = row
    company_data = {
        "debt_ratio": float(debt_ratio) if debt_ratio is not None else 0,
        "current_ratio": float(current_ratio) if current_ratio is not None else 0,
        "quick_ratio": float(quick_ratio) if quick_ratio is not None else 0
    }

    # 업종 평균
    cur.execute("""
        SELECT AVG(debt_ratio), AVG(current_ratio), AVG(quick_ratio)
        FROM financialstatements6
        WHERE year = %s AND industry = %s
    """, (int(year), industry))
    row = cur.fetchone()
    cur.close()

    industry_data = {
        "debt_ratio": float(row[0]) if row[0] is not None else 0,
        "current_ratio": float(row[1]) if row[1] is not None else 0,
        "quick_ratio": float(row[2]) if row[2] is not None else 0
    }

    return JSONResponse({
        "company": company_data,
        "industry": industry_data,
        "industry_name": industry
    })

# 활동성 지표 (기업 vs 업종 평균, 연도별)
@app.get("/api/activity")
def get_activity(year: str, company_id: int):
    cur = conn.cursor()

    # 1) 해당 연도의 기업 값 + 업종 추출
    cur.execute("""
        SELECT
          inventory_turnover,       -- 재고회전
          receivables_turnover,     -- 채권회전
          asset_turnover,           -- 총자산회전
          fixed_asset_turnover,     -- 비유동회전
          industry, name
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """, (int(year), company_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        return JSONResponse({
            "company":  {"inventory_turnover": 0, "receivables_turnover": 0, "asset_turnover": 0, "fixed_asset_turnover": 0, "name": None},
            "industry": {"inventory_turnover": 0, "receivables_turnover": 0, "asset_turnover": 0, "fixed_asset_turnover": 0, "name": None}
        })

    inv, recv, asset, fixed_asset, industry, cname = row
    company = {
        "inventory_turnover": float(inv) if inv is not None else 0.0,
        "receivables_turnover": float(recv) if recv is not None else 0.0,
        "asset_turnover": float(asset) if asset is not None else 0.0,
        "fixed_asset_turnover": float(fixed_asset) if fixed_asset is not None else 0.0,
        "name": cname,
    }

    # 2) 해당 연도의 업종 평균
    cur.execute("""
        SELECT
          AVG(inventory_turnover),
          AVG(receivables_turnover),
          AVG(asset_turnover),
          AVG(fixed_asset_turnover)
        FROM financialstatements6
        WHERE year = %s AND industry = %s
    """, (int(year), industry))
    avg_row = cur.fetchone()
    cur.close()

    industry_data = {
        "inventory_turnover": float(avg_row[0]) if avg_row and avg_row[0] is not None else 0.0,
        "receivables_turnover": float(avg_row[1]) if avg_row and avg_row[1] is not None else 0.0,
        "asset_turnover": float(avg_row[2]) if avg_row and avg_row[2] is not None else 0.0,
        "fixed_asset_turnover": float(avg_row[3]) if avg_row and avg_row[3] is not None else 0.0,
        "name": industry
    }

    return JSONResponse({"company": company, "industry": industry_data})


# 기업 리스트 (연도별, 최대 500개)
@app.get("/api/companies")
def get_companies(year: str):
    cur = conn.cursor()
    sql = """
        SELECT idx, name, industry, size, pd, grade, score, debt_ratio, roe, assets
        FROM financialstatements6
        WHERE year = %s
        ORDER BY idx
        LIMIT 1500
    """
    cur.execute(sql, (int(year),))
    rows = cur.fetchall()
    cur.close()

    result = []
    for r in rows:
        result.append({
            "idx": r[0],
            "name": r[1],
            "industry": r[2],
            "size": r[3],
            "pd": float(r[4]) if r[4] is not None else 0,
            "grade": r[5],
            "score": float(r[6]) if r[6] is not None else 0,
            "debt_ratio": float(r[7]) if r[7] is not None else 0,
            "roe": float(r[8]) if r[8] is not None else 0,
            "assets": float(r[9]) if r[9] is not None else 0
        })
    return JSONResponse(result)



# @app.get("/industry", response_class=HTMLResponse)
# def firm_dashboard(request: Request):
#     cur = conn.cursor()
#     sql = """SELECT idx,name,industry,size,grade,year,pd,score,debt_ratio,roe,roa,roic,assets,sales_growth,profit_growth,current_ratio,quick_ratio,inventory_turnover,receivables_turnover,asset_turnover,fixed_asset_turnover,operating_cf,operating_cf_to_assets,operating_cf_to_debt,operating_cf_to_sales,industry_avg_pd,industry_avg_roe,industry_avg_roa,industry_avg_debt_ratio,gdp_growth,inflation,unemployment,interest_rate,company_code,established_date,ceo
#              FROM financialstatements6;"""
#     cur.execute(sql)
#     rows = cur.fetchall()
#     colnames = [desc[0] for desc in cur.description]
#     cur.close()

#     # Decimal → float 변환
#     def convert(value):
#         if isinstance(value, Decimal):
#             return float(value)
#         return value

#     data = [dict(zip(colnames, (convert(v) for v in row))) for row in rows]

#     return templates.TemplateResponse(
#         "industry.html",
#         {"request": request, "companies": json.dumps(data, ensure_ascii=False, default=str)}
#     )


@app.get("/firm_filter", response_class=HTMLResponse)
def firm_dashboard(request: Request):
    cur = conn.cursor()
    sql = """SELECT idx,name,industry,size,grade,year,operating_cf_to_assets,operating_cf_to_debt,operating_cf_to_sales,pd,score,debt_ratio,roe,roa,roic,assets,sales_growth,profit_growth,current_ratio,quick_ratio,inventory_turnover,receivables_turnover,asset_turnover,fixed_asset_turnover,operating_cf,industry_avg_pd,industry_avg_roe,industry_avg_roa,industry_avg_debt_ratio,company_code,established_date,ceo,division,employee_growth_rate,optl,ffoeq,oeneg,cfoint,accounts_payable_turnover,interest_coverage_ratio,noncurrent_asset_turnover
             FROM financialstatements6;"""
    cur.execute(sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()

    # Decimal → float 변환
    def convert(value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    data = [dict(zip(colnames, (convert(v) for v in row))) for row in rows]

    return templates.TemplateResponse(
        "firm_filter.html",
        {"request": request, "companies": json.dumps(data, ensure_ascii=False, default=str)}
    )


@app.get("/main", response_class=HTMLResponse)
def firm_dashboard(request: Request):
    cur = conn.cursor()
    sql = """SELECT idx,name,company_code,industry,size,year,established_date,ceo,debt_ratio,assets,sales_growth,current_ratio,quick_ratio,inventory_turnover,receivables_turnover,asset_turnover,fixed_asset_turnover,operating_cf,operating_cf_to_assets,operating_cf_to_debt,industry_avg_roe,industry_avg_roa,industry_avg_debt_ratio,roa,roic,division,employee_growth_rate,roe,operating_cf_to_sales,profit_growth,optl,ffoeq,oeneg,cfoint,accounts_payable_turnover,interest_coverage_ratio,noncurrent_asset_turnover,industry_avg_pd,pd,score,grade
             FROM financialstatements6;"""
    cur.execute(sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()

    # Decimal → float 변환
    def convert(value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    data = [dict(zip(colnames, (convert(v) for v in row))) for row in rows]

    return templates.TemplateResponse(
        "main.html",
        {"request": request, "companies": json.dumps(data, ensure_ascii=False, default=str)}
    )


# @app.get("/main", response_class=HTMLResponse)
# def get_sidebar(request: Request):
#     return templates.TemplateResponse("main.html", {"request": request})


@app.get("/sidebar", response_class=HTMLResponse)
def get_sidebar(request: Request):
    return templates.TemplateResponse("sidebar.html", {"request": request})








import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/generate-report")
async def generate_report(request: Request):
    data = await request.json()
    firm = data.get("firm") or {}

    prompt = f"""
    다음 기업의 주요 재무 및 신용 데이터를 분석하여 리포트를 작성해 주세요.

    기업명: {firm.get('name')}
    업종: {firm.get('industry')}
    기업규모: {firm.get('size')}
    대출등급: {firm.get('grade')}
    부실확률(PD): {firm.get('pd')}
    ROE: {firm.get('roe')}
    ROA: {firm.get('roa')}
    매출 성장률: {firm.get('sales_growth')}
    영업이익 성장률: {firm.get('profit_growth')}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # gpt-4o-mini 또는 gpt-3.5-turbo 권장
        messages=[{"role": "user", "content": prompt}]
    )
    return {"report": response.choices[0].message.content}




@app.get("/report", response_class=HTMLResponse)
async def report_page(request: Request):
    return templates.TemplateResponse("report.html", {"request": request})




@app.get("/api/drivers")
def get_drivers(year: int, company_id: int):
    cur = conn.cursor()
    # 1) 기업 값 + 업종 가져오기
    cur.execute("""
        SELECT
            roe,
            optl,
            ffoeq,
            profit_growth,
            accounts_payable_turnover,
            interest_coverage_ratio,
            industry
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """, (year, company_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        return JSONResponse({"labels": [], "effects": [], "industry_avgs": []})

    # 기업 값
    roe, optl, ffoeq, profit_growth, ap_turnover, icr, industry = row
    effects = [
        float(roe) if roe is not None else 0.0,
        float(optl) if optl is not None else 0.0,
        float(ffoeq) if ffoeq is not None else 0.0,
        float(profit_growth) if profit_growth is not None else 0.0,
        float(ap_turnover) if ap_turnover is not None else 0.0,
        float(icr) if icr is not None else 0.0
    ]

    # 2) 업종 평균 값
    cur.execute("""
        SELECT
            AVG(roe),
            AVG(optl),
            AVG(ffoeq),
            AVG(profit_growth),
            AVG(accounts_payable_turnover),
            AVG(interest_coverage_ratio)
        FROM financialstatements6
        WHERE year = %s AND industry = %s
    """, (year, industry))
    avg_row = cur.fetchone()
    cur.close()

    industry_avgs = [float(v) if v is not None else 0.0 for v in avg_row]

    labels = [
        "자기자본이익률(ROE)",
        "영업이익/총부채(OPTL)",
        "운영현금흐름/자기자본(FFOEQ)",
        "영업손익증가율",
        "매입채무회전율",
        "재무보상비율"
    ]

    return JSONResponse({
        "labels": labels,
        "effects": effects,
        "industry_avgs": industry_avgs
    })



from difflib import get_close_matches

@app.post("/chat")
async def chat_with_ai(request: Request):
    data = await request.json()
    message = data.get("message", "")

    # --- 1) 사용자 질문에서 기업명 추출 ---
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT name FROM financialstatements6;")
    firm_names = [r[0] for r in cur.fetchall()]
    cur.close()

    target_firm = None
    if message:
        matches = get_close_matches(message, firm_names, n=1, cutoff=0.6)
        if matches:
            target_firm = matches[0]

    firm = {}
    if target_firm:
        cur = conn.cursor()
        cur.execute("SELECT name, industry, size, grade, pd, roe, roa, sales_growth, profit_growth \
             FROM financialstatements6 WHERE name LIKE %s ORDER BY year DESC LIMIT 1",
            (f"%{message}%",))
        row = cur.fetchone()
        cur.close()
        if row:
            firm = {
                "name": row[0], "industry": row[1], "size": row[2],
                "grade": row[3], "pd": float(row[4]) if row[4] else None,
                "roe": float(row[5]) if row[5] else None,
                "roa": float(row[6]) if row[6] else None,
                "sales_growth": float(row[7]) if row[7] else None,
                "profit_growth": float(row[8]) if row[8] else None,
            }

    # --- 2) 컨텍스트 구성 ---
    if firm:
        context = f"""
        기업명: {firm['name']}
        업종: {firm['industry']}
        기업규모: {firm['size']}
        신용등급: {firm['grade']}
        부실확률(PD): {firm['pd']}
        ROE: {firm['roe']}
        ROA: {firm['roa']}
        매출 성장률: {firm['sales_growth']}
        영업이익 성장률: {firm['profit_growth']}
        """
    else:
        context = "해당 질문과 관련된 기업 정보를 DB에서 찾을 수 없습니다."

    # --- 3) 프롬프트 구성 ---
    prompt = f"""
    당신은 핑뱅크(PingBank)의 대출 상담사입니다.
    사용자의 질문에 따라 기업 재무 데이터와 신용등급, 부실확률(PD)을 활용하여
    대출 가능성을 평가하고 고객이 이해하기 쉽게 설명하세요.
    사용자가 물어보는 회사명이나 기업명이 정확히 일치하지 않아도, 비슷한 이름의 기업에 대한 정보를 제공하면 됩니다.

    [기업 정보]
    {context}

    [지침]
    - 반드시 상담사처럼 정중하고 친절한 말투로 답하세요.
    - 대출 여부는 **가능 / 조건부 가능 / 불가능** 중 하나로 분명히 제시하세요.
    - 근거를 2~3개로 간단히 설명하세요.
    - 기업 데이터를 찾을 수 없으면, 일반적인 대출 심사 기준을 설명하세요.

    [사용자 질문]
    {message}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"reply": response.choices[0].message.content}


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7001)




