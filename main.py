from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from decimal import Decimal
from dotenv import load_dotenv
import os
import uvicorn
import psycopg2
import json
import openai
import math

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

# -----------------------------
# 공통 유틸: 안전 변환 (NaN/Inf/Decimal)
# -----------------------------
def _to_none_if_nan_inf(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v

def _clean_value(v):
    if v is None:
        return None
    if isinstance(v, Decimal):
        v = float(v)
    if isinstance(v, float):
        return _to_none_if_nan_inf(v)
    return v

def _clean_dict(d: dict):
    return {k: _clean_value(v) for k, v in d.items()}

def _json_dumps_safe(obj) -> str:
    # allow_nan=False 로 NaN 직렬화 방지 (즉시 에러로 파악 가능)
    return json.dumps(obj, ensure_ascii=False, default=str, allow_nan=False)



@app.get("/firm", response_class=HTMLResponse)
def firm_dashboard(request: Request):
    """
    firm.html에 주입되는 SERVER_COMPANIES 데이터를 구성.
    차트/보고서에서 쓰는 모든 주요 지표 포함 + NaN 방지.
    """
    cur = conn.cursor()
    sql = """
        SELECT
            idx, name, industry, size, grade, year,
            company_code, established_date, ceo,
            pd, score, debt_ratio, roe, roa, roic, assets,
            sales_growth, profit_growth,
            current_ratio, quick_ratio,
            inventory_turnover, receivables_turnover, asset_turnover, fixed_asset_turnover,
            operating_cf,
            operating_cf_to_assets, operating_cf_to_debt, operating_cf_to_sales,
            -- 중요 6대 요인
            optl, ffoeq, accounts_payable_turnover, interest_coverage_ratio,
            -- 참고 지표
            noncurrent_asset_turnover
        FROM financialstatements6;
    """
    cur.execute(sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()

    data = []
    for row in rows:
        rec = dict(zip(colnames, row))
        data.append(_clean_dict(rec))

    # 동일 idx(기업) 기준으로 캐시플로우 타임라인 묶기
    firms = {}
    for row in data:
        key = row["idx"]
        if key not in firms:
            firms[key] = {**row}
            firms[key]["cashflow"] = {"years": [], "operating": [], "investing": [], "financing": []}
        # 타임시리즈 축적
        firms[key]["cashflow"]["years"].append(row.get("year"))
        firms[key]["cashflow"]["operating"].append(row.get("operating_cf_to_assets") or 0)
        firms[key]["cashflow"]["investing"].append(row.get("operating_cf_to_debt") or 0)
        firms[key]["cashflow"]["financing"].append(row.get("operating_cf_to_sales") or 0)

        # 활동성 최신값 보정(빈 데이터일 경우 0)
        for k in ("inventory_turnover", "receivables_turnover", "asset_turnover", "fixed_asset_turnover"):
            if k in row and row[k] is not None:
                firms[key][k] = row[k]

    # Jinja에 JSON 문자열로 주입 (NaN 금지)
    companies_json = _json_dumps_safe(list(firms.values()))
    return templates.TemplateResponse("firm.html", {
        "request": request,
        "companies": companies_json
    })


@app.get("/main", response_class=HTMLResponse)
def main_dashboard(request: Request):
    """
    main.html에 필요한 리스트(필터/서치 등) 주입.
    """
    cur = conn.cursor()
    sql = """
        SELECT
            idx, name, company_code, industry, size, year, established_date, ceo,
            debt_ratio, assets, sales_growth, current_ratio, quick_ratio,
            inventory_turnover, receivables_turnover, asset_turnover, fixed_asset_turnover,
            operating_cf, operating_cf_to_assets, operating_cf_to_debt, operating_cf_to_sales,
            industry_avg_roe, industry_avg_roa, industry_avg_debt_ratio,
            roa, roic, division, employee_growth_rate, roe, profit_growth,
            optl, ffoeq, oeneg, cfoint, accounts_payable_turnover, interest_coverage_ratio,
            noncurrent_asset_turnover, industry_avg_pd, pd, score, grade
        FROM financialstatements6;
    """
    cur.execute(sql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()

    data = []
    for row in rows:
        data.append(_clean_dict(dict(zip(colnames, row))))

    return templates.TemplateResponse("main.html", {
        "request": request,
        "companies": _json_dumps_safe(data)
    })

@app.get("/sidebar", response_class=HTMLResponse)
def get_sidebar(request: Request):
    return templates.TemplateResponse("sidebar.html", {"request": request})


# 기업 기본정보 (연도별)
@app.get("/api/company-info")
def get_company_info(year: str, company_id: int):
    cur = conn.cursor()
    sql = """
        SELECT
            name, company_code, established_date, ceo, size, industry,
            grade, pd, score, assets,
            roe, roa, roic,
            sales_growth, profit_growth,
            debt_ratio, current_ratio, quick_ratio,
            inventory_turnover, receivables_turnover, asset_turnover, fixed_asset_turnover,
            operating_cf, operating_cf_to_assets, operating_cf_to_debt, operating_cf_to_sales,
            optl, ffoeq, accounts_payable_turnover, interest_coverage_ratio, noncurrent_asset_turnover
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """
    cur.execute(sql, (int(year), company_id))
    row = cur.fetchone()
    cur.close()

    if not row:
        return JSONResponse({})

    (
        name, company_code, established_date, ceo, size, industry,
        grade, pd, score, assets,
        roe, roa, roic,
        sales_growth, profit_growth,
        debt_ratio, current_ratio, quick_ratio,
        inventory_turnover, receivables_turnover, asset_turnover, fixed_asset_turnover,
        operating_cf, operating_cf_to_assets, operating_cf_to_debt, operating_cf_to_sales,
        optl, ffoeq, accounts_payable_turnover, interest_coverage_ratio, noncurrent_asset_turnover
    ) = row

    payload = {
        "name": name,
        "company_code": company_code,                       # 서버 리스트(SERVER_COMPANIES)와 정합성 유지
        "code": company_code,                               # 혹시 프론트에서 code로도 참조하면 대비
        "established_date": str(established_date) if established_date else None,
        "ceo": ceo,
        "size": size,
        "industry": industry,
        "grade": grade,
        "pd": _clean_value(pd),
        "score": _clean_value(score),
        "assets": _clean_value(assets),
        "roe": _clean_value(roe),
        "roa": _clean_value(roa),
        "roic": _clean_value(roic),
        "sales_growth": _clean_value(sales_growth),
        "profit_growth": _clean_value(profit_growth),
        "debt_ratio": _clean_value(debt_ratio),
        "current_ratio": _clean_value(current_ratio),
        "quick_ratio": _clean_value(quick_ratio),
        "inventory_turnover": _clean_value(inventory_turnover),
        "receivables_turnover": _clean_value(receivables_turnover),
        "asset_turnover": _clean_value(asset_turnover),
        "fixed_asset_turnover": _clean_value(fixed_asset_turnover),
        "operating_cf": _clean_value(operating_cf),
        "operating_cf_to_assets": _clean_value(operating_cf_to_assets),
        "operating_cf_to_debt": _clean_value(operating_cf_to_debt),
        "operating_cf_to_sales": _clean_value(operating_cf_to_sales),
        "optl": _clean_value(optl),
        "ffoeq": _clean_value(ffoeq),
        "accounts_payable_turnover": _clean_value(accounts_payable_turnover),
        "interest_coverage_ratio": _clean_value(interest_coverage_ratio),
        "noncurrent_asset_turnover": _clean_value(noncurrent_asset_turnover),
    }
    return JSONResponse(payload)


# 신용점수 (기업)
@app.get("/api/credit-score")
def get_credit_score(year: str, company_id: int):
    cur = conn.cursor()
    sql = 'SELECT grade, score FROM financialstatements6 WHERE "year" = %s AND idx = %s LIMIT 1;'
    cur.execute(sql, (int(year), company_id))
    row = cur.fetchone()
    cur.close()

    if not row:
        return JSONResponse({"grade": "-", "delta": "-", "score": 0})

    grade, score = row
    score = _clean_value(score) or 0
    delta = "등급 안정" if grade == "A" else "변동 있음"
    return JSONResponse({"grade": grade, "delta": delta, "score": score})


# 점수 비교 (기업/업종/규모/전체)
@app.get("/api/score-avg")
def get_score_avg(year: str, company_id: int):
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
          AND industry = (SELECT industry FROM financialstatements6 WHERE idx = %s LIMIT 1)

        UNION ALL
        -- 규모 평균
        SELECT '규모 평균', ROUND(AVG(score),2)
        FROM financialstatements6
        WHERE "year" = %s
          AND size = (SELECT size FROM financialstatements6 WHERE idx = %s LIMIT 1)

        UNION ALL
        -- 전체 평균
        SELECT '전체 평균', ROUND(AVG(score),2)
        FROM financialstatements6
        WHERE "year" = %s
    """
    cur.execute(sql, (
        int(year), company_id,
        int(year), company_id,
        int(year), company_id,
        int(year)
    ))
    rows = cur.fetchall()
    cur.close()

    result = [{"label": r[0], "value": float(r[1]) if r[1] is not None else 0} for r in rows]
    return JSONResponse(result)

@app.get("/api/credit-score-avg")
def get_credit_score_avg(year: str, company_id: int):
    return get_score_avg(year, company_id)


# 부실확률 (기업별, 연도별)
@app.get("/api/pd")
def get_pd(year: str, company_id: int):
    cur = conn.cursor()

    # 기업 PD + 업종
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
        "pd": float(pd) if pd is not None and not math.isnan(pd) and not math.isinf(pd) else 0.0,
        "industry_avg": float(ind_pd) if ind_pd is not None else 0.0
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

    # 기준 기업의 업종 정보 가져오기
    cur.execute("""
        SELECT industry, size 
        FROM financialstatements6
        WHERE year = %s AND idx = %s
        LIMIT 1
    """, (int(year), company_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        return JSONResponse({"peers": []})

    industry, size = row[0], row[1]

    peers = []
    if industry:  # ✅ 업종 값이 있으면 업종 전체 불러오기
        sql = """
            SELECT idx, name, roe, debt_ratio
            FROM financialstatements6
            WHERE year = %s AND industry = %s
        """
        cur.execute(sql, (int(year), industry))
        rows = cur.fetchall()

        for r in rows:
            peers.append({
                "idx": r[0],
                "name": r[1],
                "roe": float(r[2]) if r[2] is not None else 0,
                "debt_ratio": float(r[3]) if r[3] is not None else 0
            })

    else:  # ✅ 업종 값이 NULL이면 fallback 처리
        # 1) 같은 규모(size)로 fallback
        if size:
            sql = """
                SELECT idx, name, roe, debt_ratio
                FROM financialstatements6
                WHERE year = %s AND size = %s
            """
            cur.execute(sql, (int(year), size))
            rows = cur.fetchall()

            for r in rows:
                peers.append({
                    "idx": r[0],
                    "name": r[1],
                    "roe": float(r[2]) if r[2] is not None else 0,
                    "debt_ratio": float(r[3]) if r[3] is not None else 0
                })

        # 2) 그래도 못 찾으면 자기 자신만 반환
        if not peers:
            sql = """
                SELECT idx, name, roe, debt_ratio
                FROM financialstatements6
                WHERE year = %s AND idx = %s
            """
            cur.execute(sql, (int(year), company_id))
            r = cur.fetchone()
            if r:
                peers.append({
                    "idx": r[0],
                    "name": r[1],
                    "roe": float(r[2]) if r[2] is not None else 0,
                    "debt_ratio": float(r[3]) if r[3] is not None else 0
                })

    cur.close()
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
        SELECT *
        FROM financialstatements6
        WHERE year = %s
        ORDER BY idx
        LIMIT 1500
    """
    cur.execute(sql, (int(year),))
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()

    def clean_value(v):
        """NaN, Decimal, None → 안전하게 변환"""
        if v is None:
            return 0
        try:
            return float(v)
        except Exception:
            return str(v)

    result = []
    for row in rows:
        rec = {col: clean_value(val) for col, val in zip(colnames, row)}
        result.append(rec)

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




import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/generate-report")
async def generate_report(request: Request):
    """
    프론트에서 보내는 firm 객체(= SERVER_COMPANIES에서 선택 or /api/company-info 결과)를 그대로 사용.
    JS 키와 동일한 이름을 유지해 프롬프트에 반영.
    """
    data = await request.json()
    firm = data.get("firm") or {}

    prompt = f"""
    다음 기업의 주요 재무 및 신용 데이터를 분석하여 종합 리포트를 작성해 주세요.
    대출등급은 A,B일 경우 대출 승인, C,D일 경우 대출 거절입니다.
    대출 거절 시 반드시 사유와 개선 방향을 제시해 주세요.

    [기업 기본 정보]
    기업명: {firm.get('name')}
    기업코드: {firm.get('company_code') or firm.get('code')}
    업종: {firm.get('industry')}
    기업규모: {firm.get('size')}
    설립일: {firm.get('established_date')}
    대표자: {firm.get('ceo')}
    대출등급: {firm.get('grade')}
    부실확률(PD): {firm.get('pd')}
    신용점수: {firm.get('score')}
    총자산: {firm.get('assets')}

    [재무 지표]
    ROE: {firm.get('roe')}
    ROA: {firm.get('roa')}
    ROIC: {firm.get('roic')}
    매출 성장률: {firm.get('sales_growth')}
    영업이익 성장률: {firm.get('profit_growth')}
    부채비율: {firm.get('debt_ratio')}
    유동비율: {firm.get('current_ratio')}
    당좌비율: {firm.get('quick_ratio')}
    재고회전율: {firm.get('inventory_turnover')}
    매출채권회전율: {firm.get('receivables_turnover')}
    총자산회전율: {firm.get('asset_turnover')}
    고정자산회전율: {firm.get('fixed_asset_turnover')}
    영업현금흐름: {firm.get('operating_cf')}
    영업현금흐름/총자산: {firm.get('operating_cf_to_assets')}
    영업현금흐름/부채: {firm.get('operating_cf_to_debt')}
    영업현금흐름/매출: {firm.get('operating_cf_to_sales')}

    [특히 중요하게 평가할 요인]
    - ROE: {firm.get('roe')}
    - 영업이익/총부채(OPTL): {firm.get('optl')}
    - 운영현금흐름/자기자본(FFOEQ): {firm.get('ffoeq')}
    - 영업손익증가율(= 영업이익 성장/변화): {firm.get('profit_growth')}
    - 매입채무회전율: {firm.get('accounts_payable_turnover')}
    - 재무보상비율(ICR): {firm.get('interest_coverage_ratio')}

    --- 작성 지침 ---
    1) 재무 건전성·수익성·성장성·활동성·현금흐름을 종합 평가.
    2) 위 6개 요인은 부실 가능성 영향이 크므로 반드시 강조 분석.
    3) 대출 여부를 **가능 / 조건부 가능 / 불가능**으로 명확히 제시.
    4) 핵심 근거 2~3개 제시, 필요 시 개선 방향 제안.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"report": response.choices[0].message.content}



@app.get("/report", response_class=HTMLResponse)
async def report_page(request: Request):
    return templates.TemplateResponse("report.html", {"request": request})




import math

def safe_number(v):
    try:
        if v is None:
            return 0.0
        n = float(v)
        if math.isnan(n) or math.isinf(n):
            return 0.0
        return n
    except Exception:
        return 0.0


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

    # 기업 값 안전 변환
    roe, optl, ffoeq, profit_growth, ap_turnover, icr, industry = row
    effects = [
        safe_number(roe),
        safe_number(optl),
        safe_number(ffoeq),
        safe_number(profit_growth),
        safe_number(ap_turnover),
        safe_number(icr)
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

    # 업종 평균 안전 변환
    industry_avgs = [safe_number(v) for v in (avg_row or [])]

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




# from difflib import get_close_matches

# @app.post("/chat")
# async def chat_with_ai(request: Request):
#     data = await request.json()
#     message = (data.get("message") or "").strip()

#     # 기본적으로 프론트에서 firm을 주면 사용
#     firm = data.get("firm") or {}

#     # firm이 없을 때: 메시지가 기업코드일 가능성 우선 조회
#     if not firm and message:
#         cur = conn.cursor()
#         cur.execute("""
#             SELECT name, company_code, industry, size, grade, pd, roe, roa, sales_growth, profit_growth
#             FROM financialstatements6
#             WHERE company_code = %s
#             ORDER BY year DESC
#             LIMIT 1
#         """, (message,))
#         row = cur.fetchone()

#         if row:
#             firm = {
#                 "name": row[0], "company_code": row[1], "industry": row[2], "size": row[3],
#                 "grade": row[4], "pd": _clean_value(row[5]),
#                 "roe": _clean_value(row[6]), "roa": _clean_value(row[7]),
#                 "sales_growth": _clean_value(row[8]), "profit_growth": _clean_value(row[9]),
#             }
#         else:
#             # 기업명이면 fuzzy 매칭
#             cur.execute("SELECT DISTINCT name FROM financialstatements6;")
#             firm_names = [r[0] for r in cur.fetchall()]
#             from difflib import get_close_matches
#             matches = get_close_matches(message, firm_names, n=1, cutoff=0.6)
#             if matches:
#                 target = matches[0]
#                 cur.execute("""
#                     SELECT name, company_code, industry, size, grade, pd, roe, roa, sales_growth, profit_growth
#                     FROM financialstatements6
#                     WHERE name = %s
#                     ORDER BY year DESC
#                     LIMIT 1
#                 """, (target,))
#                 row = cur.fetchone()
#                 if row:
#                     firm = {
#                         "name": row[0], "company_code": row[1], "industry": row[2], "size": row[3],
#                         "grade": row[4], "pd": _clean_value(row[5]),
#                         "roe": _clean_value(row[6]), "roa": _clean_value(row[7]),
#                         "sales_growth": _clean_value(row[8]), "profit_growth": _clean_value(row[9]),
#                     }
#         cur.close()

#     context = f"""
#     기업명: {firm.get('name')}
#     업종: {firm.get('industry')}
#     기업규모: {firm.get('size')}
#     대출등급: {firm.get('grade')}
#     부실확률(PD): {firm.get('pd')}
#     ROE: {firm.get('roe')}
#     ROA: {firm.get('roa')}
#     매출 성장률: {firm.get('sales_growth')}
#     영업이익 성장률: {firm.get('profit_growth')}
#     """

#     prompt = f"""
#     당신은 핑뱅크(PingBank)의 대출 상담사입니다.
#     기업의 재무정보(등급/PD/수익성/성장성)를 근거로 대출 가능성을 상담해 주세요.

#     [기업 정보]
#     {context}

#     [지침]
#     - 정중하고 친절한 말투.
#     - 대출 여부는 **가능 / 조건부 가능 / 불가능** 중 하나로 분명히 제시.
#     - 2~3개의 핵심 근거를 간단 명료하게 제시.
#     - 기업 데이터를 찾지 못하면 일반적인 심사 기준을 설명.
#     [사용자 질문]
#     {message}
#     """

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return {"reply": response.choices[0].message.content}






from difflib import get_close_matches

@app.post("/chat")
async def chat_with_ai(request: Request):
    data = await request.json()
    message = (data.get("message") or "").strip()

    # 프론트에서 firm 객체를 주는 경우 우선 사용
    firm = data.get("firm") or {}

    # firm이 없으면 DB에서 조회 (기업코드 → 기업명 fuzzy 매칭 순서)
    if not firm and message:
        cur = conn.cursor()

        # 1) 기업코드로 조회
        cur.execute("""
            SELECT name, company_code, industry, size, grade, pd, score, assets,
                   roe, roa, roic,
                   sales_growth, profit_growth,
                   debt_ratio, current_ratio, quick_ratio,
                   inventory_turnover, receivables_turnover, asset_turnover, fixed_asset_turnover,
                   operating_cf, operating_cf_to_assets, operating_cf_to_debt, operating_cf_to_sales,
                   optl, ffoeq,
                   accounts_payable_turnover, interest_coverage_ratio
            FROM financialstatements6
            WHERE company_code = %s
            ORDER BY year DESC
            LIMIT 1
        """, (message,))
        row = cur.fetchone()

        if not row:
            # 2) fuzzy 매칭으로 기업명 찾기
            cur.execute("SELECT DISTINCT name FROM financialstatements6;")
            firm_names = [r[0] for r in cur.fetchall()]
            matches = get_close_matches(message, firm_names, n=1, cutoff=0.6)
            if matches:
                target = matches[0]
                cur.execute("""
                    SELECT name, company_code, industry, size, grade, pd, score, assets,
                           roe, roa, roic,
                           sales_growth, profit_growth,
                           debt_ratio, current_ratio, quick_ratio,
                           inventory_turnover, receivables_turnover, asset_turnover, fixed_asset_turnover,
                           operating_cf, operating_cf_to_assets, operating_cf_to_debt, operating_cf_to_sales,
                           optl, ffoeq,
                           accounts_payable_turnover, interest_coverage_ratio
                    FROM financialstatements6
                    WHERE name = %s
                    ORDER BY year DESC
                    LIMIT 1
                """, (target,))
                row = cur.fetchone()

        if row:
            firm = {
                "name": row[0], "company_code": row[1], "industry": row[2], "size": row[3],
                "grade": row[4], "pd": _clean_value(row[5]), "score": _clean_value(row[6]), "assets": _clean_value(row[7]),
                "roe": _clean_value(row[8]), "roa": _clean_value(row[9]), "roic": _clean_value(row[10]),
                "sales_growth": _clean_value(row[11]), "profit_growth": _clean_value(row[12]),
                "debt_ratio": _clean_value(row[13]), "current_ratio": _clean_value(row[14]), "quick_ratio": _clean_value(row[15]),
                "inventory_turnover": _clean_value(row[16]), "receivables_turnover": _clean_value(row[17]),
                "asset_turnover": _clean_value(row[18]), "fixed_asset_turnover": _clean_value(row[19]),
                "operating_cf": _clean_value(row[20]), "operating_cf_to_assets": _clean_value(row[21]),
                "operating_cf_to_debt": _clean_value(row[22]), "operating_cf_to_sales": _clean_value(row[23]),
                "optl": _clean_value(row[24]), "ffoeq": _clean_value(row[25]),
                "accounts_payable_turnover": _clean_value(row[26]), "interest_coverage_ratio": _clean_value(row[27]),
            }
        cur.close()

    # --- 프롬프트 컨텍스트 ---
    context = f"""
    기업명: {firm.get('name')}
    업종: {firm.get('industry')}
    기업규모: {firm.get('size')}
    대출등급: {firm.get('grade')}
    부실확률(PD): {firm.get('pd')}
    신용점수: {firm.get('score')}
    총자산: {firm.get('assets')}
    ROE: {firm.get('roe')}
    ROA: {firm.get('roa')}
    ROIC: {firm.get('roic')}
    매출 성장률: {firm.get('sales_growth')}
    영업이익 성장률: {firm.get('profit_growth')}
    부채비율: {firm.get('debt_ratio')}
    유동비율: {firm.get('current_ratio')}
    당좌비율: {firm.get('quick_ratio')}
    재고회전율: {firm.get('inventory_turnover')}
    매출채권회전율: {firm.get('receivables_turnover')}
    총자산회전율: {firm.get('asset_turnover')}
    고정자산회전율: {firm.get('fixed_asset_turnover')}
    영업현금흐름: {firm.get('operating_cf')}
    영업현금흐름/총자산: {firm.get('operating_cf_to_assets')}
    영업현금흐름/부채: {firm.get('operating_cf_to_debt')}
    영업현금흐름/매출: {firm.get('operating_cf_to_sales')}
    영업이익/총부채(OPTL): {firm.get('optl')}
    운영현금흐름/자기자본(FFOEQ): {firm.get('ffoeq')}
    매입채무회전율: {firm.get('accounts_payable_turnover')}
    재무보상비율(ICR): {firm.get('interest_coverage_ratio')}
    """

    # --- GPT 프롬프트 ---
    prompt = f"""
    당신은 핑뱅크(PingBank)의 대출 상담사입니다.
    기업의 재무정보를 종합하여 대출 가능성을 상담해 주세요.

    [기업 정보]
    {context}

    [지침]
    - 정중하고 친절한 말투.
    - 대출 여부는 **가능 / 조건부 가능 / 불가능** 중 하나로 명확히 제시.
    - 2~3개의 핵심 근거를 간단히 설명.
    - 기업 데이터를 찾지 못하면 일반적인 심사 기준을 설명.
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




