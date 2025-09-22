# main.py (전체 수정본)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from decimal import Decimal
from dotenv import load_dotenv
from openai import OpenAI

import os
import uvicorn
import psycopg2
import json
import math

# -----------------------------
# 환경/DB/클라이언트 세팅
# -----------------------------
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


# -----------------------------
# 페이지 라우트
# -----------------------------
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


# -----------------------------
# API (프론트에서 직접 호출)
# -----------------------------
# 기업 기본정보 (연도별) - 명시적 SELECT (select * 지양)
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


# -----------------------------
# OpenAI: 리포트/채팅
# -----------------------------
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


@app.post("/chat")
async def chat_with_ai(request: Request):
    data = await request.json()
    message = (data.get("message") or "").strip()

    # 기본적으로 프론트에서 firm을 주면 사용
    firm = data.get("firm") or {}

    # firm이 없을 때: 메시지가 기업코드일 가능성 우선 조회
    if not firm and message:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, company_code, industry, size, grade, pd, roe, roa, sales_growth, profit_growth
            FROM financialstatements6
            WHERE company_code = %s
            ORDER BY year DESC
            LIMIT 1
        """, (message,))
        row = cur.fetchone()

        if row:
            firm = {
                "name": row[0], "company_code": row[1], "industry": row[2], "size": row[3],
                "grade": row[4], "pd": _clean_value(row[5]),
                "roe": _clean_value(row[6]), "roa": _clean_value(row[7]),
                "sales_growth": _clean_value(row[8]), "profit_growth": _clean_value(row[9]),
            }
        else:
            # 기업명이면 fuzzy 매칭
            cur.execute("SELECT DISTINCT name FROM financialstatements6;")
            firm_names = [r[0] for r in cur.fetchall()]
            from difflib import get_close_matches
            matches = get_close_matches(message, firm_names, n=1, cutoff=0.6)
            if matches:
                target = matches[0]
                cur.execute("""
                    SELECT name, company_code, industry, size, grade, pd, roe, roa, sales_growth, profit_growth
                    FROM financialstatements6
                    WHERE name = %s
                    ORDER BY year DESC
                    LIMIT 1
                """, (target,))
                row = cur.fetchone()
                if row:
                    firm = {
                        "name": row[0], "company_code": row[1], "industry": row[2], "size": row[3],
                        "grade": row[4], "pd": _clean_value(row[5]),
                        "roe": _clean_value(row[6]), "roa": _clean_value(row[7]),
                        "sales_growth": _clean_value(row[8]), "profit_growth": _clean_value(row[9]),
                    }
        cur.close()

    context = f"""
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

    prompt = f"""
    당신은 핑뱅크(PingBank)의 대출 상담사입니다.
    기업의 재무정보(등급/PD/수익성/성장성)를 근거로 대출 가능성을 상담해 주세요.

    [기업 정보]
    {context}

    [지침]
    - 정중하고 친절한 말투.
    - 대출 여부는 **가능 / 조건부 가능 / 불가능** 중 하나로 분명히 제시.
    - 2~3개의 핵심 근거를 간단 명료하게 제시.
    - 기업 데이터를 찾지 못하면 일반적인 심사 기준을 설명.
    [사용자 질문]
    {message}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"reply": response.choices[0].message.content}


# -----------------------------
# 앱 실행
# -----------------------------
if __name__ == "__main__":
    # 필요 시 host/port 조정
    uvicorn.run(app, host="0.0.0.0", port=8000)
