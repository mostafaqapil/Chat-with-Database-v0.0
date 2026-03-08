import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import requests
import pandasql as ps
import time
import re
import json

st.set_page_config(
    page_title="Chat with Database",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* ── App background ── */
.stApp { background: #F0F2F6 !important; }
.block-container { padding-top: 1.6rem !important; max-width: 1200px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #1C2333 !important; }
section[data-testid="stSidebar"] * { color: #CDD5DF !important; font-size: .88rem !important; }
section[data-testid="stSidebar"] h2 { color: #FFFFFF !important; font-size: 1rem !important; font-weight: 700 !important; }
section[data-testid="stSidebar"] hr { border-color: #2E3A52 !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: #2E3A52 !important; color: #CDD5DF !important;
    border: 1px solid #3D4F6E !important; border-radius: 7px !important;
    width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #3B7DDD !important; color: #FFF !important;
}
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: #253047 !important; border-radius: 6px !important;
    font-size: .78rem !important;
}
section[data-testid="stSidebar"] .streamlit-expanderContent {
    background: #1C2333 !important;
}

/* ── Typography ── */
.page-title { font-size: 1.5rem !important; font-weight: 700 !important; color: #1C2333 !important; margin-bottom: .15rem; }
.page-sub   { font-size: .87rem !important; color: #5E6E8A !important; margin-bottom: 1.3rem; }
.sec-label  { font-size: .65rem !important; font-weight: 700 !important; color: #8496B0 !important;
              letter-spacing: .9px; text-transform: uppercase; margin: 14px 0 6px; display: block; }

/* ── Cards ── */
.card { background: #FFF; border: 1px solid #DDE3EE; border-radius: 12px;
        padding: 1.2rem 1.4rem; margin-bottom: .9rem;
        box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.card-title { font-size: .7rem !important; font-weight: 700 !important; color: #5E6E8A !important;
              letter-spacing: .8px; text-transform: uppercase; margin-bottom: .7rem; }

/* ── KPI tiles ── */
.kpi-tile {
    background: #FFF; border: 1px solid #DDE3EE; border-radius: 10px;
    padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.kpi-label { font-size: .68rem !important; font-weight: 700 !important; color: #5E6E8A !important;
             text-transform: uppercase; letter-spacing: .7px; }
.kpi-value { font-size: 1.6rem !important; font-weight: 700 !important; color: #1C2333 !important; margin-top: 4px; }
.kpi-sub   { font-size: .72rem !important; color: #8496B0 !important; margin-top: 2px; }

/* ── Chat bubbles ── */
.user-row    { display: flex; justify-content: flex-end; margin: 10px 0; }
.user-bubble { background: #1C2333; color: #F5F7FA !important;
               border-radius: 16px 16px 4px 16px;
               padding: 10px 16px; max-width: 68%;
               font-size: .92rem !important; line-height: 1.55; }
.bot-row     { display: flex; align-items: flex-start; gap: 10px; margin: 10px 0; }
.bot-avatar  { width: 32px; height: 32px; background: #E8F0FE; border-radius: 50%;
               display: flex; align-items: center; justify-content: center;
               font-size: .9rem; flex-shrink: 0; margin-top: 2px; }
.bot-bubble  { background: #FFF; border: 1px solid #DDE3EE;
               border-radius: 4px 16px 16px 16px;
               padding: 10px 16px; max-width: 84%;
               font-size: .92rem !important; line-height: 1.6; color: #1C2333 !important;
               box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.bubble-lbl  { font-size: .64rem !important; font-weight: 600 !important;
               color: #9EABC0 !important; margin-bottom: 3px; letter-spacing: .4px; }

/* ── Info boxes ── */
.insight-box { background: #EEF4FF; border: 1px solid #C3D4F7;
               border-left: 4px solid #3B7DDD; border-radius: 8px;
               padding: 12px 16px; margin-top: 10px;
               font-size: .87rem !important; color: #1A3460 !important; line-height: 1.65; }
.reject-box  { background: #FFFBEA; border: 1px solid #FDE68A;
               border-left: 4px solid #F59E0B; border-radius: 8px;
               padding: 12px 16px; margin-top: 8px;
               font-size: .87rem !important; color: #78350F !important; line-height: 1.6; }
.err-box     { background: #FFF0F0; border: 1px solid #FFCDD2;
               border-left: 4px solid #E53935; border-radius: 8px;
               padding: 10px 14px; margin-top: 8px;
               font-size: .85rem !important; color: #7B1515 !important; }

/* ── SQL history ── */
.sql-box  { background: #0D1117; border-left: 3px solid #3B7DDD;
            border-radius: 4px; padding: 8px 11px;
            font-family: 'Courier New', monospace !important;
            font-size: .72rem !important; color: #79C0FF !important;
            white-space: pre-wrap; word-break: break-all; margin-top: 4px; }
.sql-meta { font-size: .65rem !important; color: #5E6E8A !important; margin-top: 4px; }

/* ── Chart feedback strip ── */
.chart-feedback { background: #F8FAFF; border: 1px solid #DDE3EE;
                  border-radius: 8px; padding: 10px 14px; margin-top: 8px;
                  font-size: .84rem !important; color: #374151 !important; }

/* ── Dashboard ── */
.dash-panel  { background: #FFF; border: 1px solid #DDE3EE; border-radius: 12px;
               padding: 1rem 1.2rem; margin-bottom: 1rem;
               box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.dash-header { font-size: .7rem !important; font-weight: 700 !important; color: #5E6E8A !important;
               text-transform: uppercase; letter-spacing: .8px;
               border-bottom: 1px solid #EEF2FA; padding-bottom: 6px; margin-bottom: 10px; }

/* ── Empty state ── */
.empty-state        { text-align: center; padding: 50px 20px; }
.empty-state .es-icon  { font-size: 2rem; margin-bottom: 10px; }
.empty-state .es-title { font-size: 1rem !important; font-weight: 600 !important; color: #4A5568 !important; margin-bottom: 6px; }
.empty-state .es-hint  { font-size: .81rem !important; line-height: 1.6; color: #7A8DA8 !important; }

/* ── Login ── */
.login-box { background: #FFF; border: 1px solid #DDE3EE; border-radius: 14px;
             padding: 2rem 2.2rem; max-width: 380px;
             box-shadow: 0 4px 18px rgba(0,0,0,.08); }

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: #1C2333 !important; color: #FFF !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
.stButton > button[kind="primary"]:hover { background: #3B7DDD !important; }

hr { border-color: #DDE3EE !important; }
</style>
""", unsafe_allow_html=True)


#  LLM helpers

def get_api_key() -> str:
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        return os.environ.get("OPENROUTER_API_KEY", "")


def call_llm(
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = 600,
) -> tuple:
    """Call OpenRouter API. Returns (content_str | None, error_str | None)."""
    key = get_api_key()
    if not key:
        return None, "API Key missing – add OPENROUTER_API_KEY to .streamlit/secrets.toml"
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=45,
        )
        d = r.json()
        if "error" in d:
            return None, f"OpenRouter error: {d['error'].get('message', str(d['error']))}"
        return d["choices"][0]["message"]["content"].strip(), None
    except requests.exceptions.Timeout:
        return None, "Request timed out (45 s). Check your connection."
    except Exception as exc:
        return None, f"Unexpected error: {exc}"


def clean_sql(raw: str) -> str:
    """Strip markdown fences and return clean SQL ending with semicolon."""
    raw = raw.strip()
    raw = re.sub(r"```sql", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw).strip()
    if ";" in raw:
        raw = raw[: raw.index(";") + 1]
    return raw.strip()


#  Data helpers  ── smart column-type detection

def detect_date_cols(df: pd.DataFrame) -> list:
    """
    Find columns that contain dates even when stored as strings.
    Tries to parse the first non-null value; keeps columns where >70% parse OK.
    """
    date_cols = []
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(50)
        if sample.empty:
            continue
        try:
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() >= 0.7:
                date_cols.append(col)
        except Exception:
            continue
    return date_cols


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of df with detected date columns cast to datetime.
    This makes the EDA and chart functions work correctly.
    """
    df = df.copy()
    for col in detect_date_cols(df):
        try:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        except Exception:
            pass
    return df


#  1. LLM Guardrail  ── reject unanswerable questions before running SQL

def validate_question(user_text: str, table_name: str, columns: list) -> tuple:
    """
    Returns (is_valid: bool, rejection_reason: str).
    Lenient validator — only rejects questions that are OBVIOUSLY unrelated.
    Fails open (returns True) if the LLM call fails or is uncertain.
    """
    prompt = f"""You are a data query validator. Your job is to decide if a user question is related to a database table.

Table name: {table_name}
Available columns: {", ".join(columns)}

User question: "{user_text}"

IMPORTANT RULES:
- Be LENIENT. If there is any reasonable way to answer the question from the columns, mark it VALID.
- Mark VALID for: aggregations, counts, totals, rankings, filters, trends, comparisons — even if the wording is vague.
- Only mark INVALID if the question is COMPLETELY unrelated (e.g. "what is the weather?" or "tell me a joke") or truly impossible from these columns.
- When in doubt → mark VALID.

Reply with ONLY this JSON, nothing else:
{{"valid": true, "reason": "ok"}}
or
{{"valid": false, "reason": "one sentence explaining what is missing"}}"""

    raw, err = call_llm([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=100)
    if err or not raw:
        return True, ""   # fail open

    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        obj = json.loads(raw)
        return bool(obj.get("valid", True)), str(obj.get("reason", ""))
    except Exception:
        return True, ""   # fail open


#  2. SQL generation & auto-fix

def generate_sql(user_text: str, table_name: str, columns: list) -> tuple:
    """Returns (sql: str | None, error: str | None)."""
    prompt = f"""You are a precise SQL generator for pandasql (SQLite dialect).

TABLE NAME : {table_name}  ← use EXACTLY this name, case-sensitive
COLUMNS    : {", ".join(columns)}

OUTPUT RULES:
- Return ONLY the raw SQL query, ending with a semicolon.
- No explanation, no markdown, no backticks, no comments.
- Use only the columns listed, exactly as spelled.
- Multiple conditions → AND in WHERE clause.
- Aggregations → GROUP BY all non-aggregated columns.
- Prefer WHERE + AND over nested subqueries.

USER REQUEST: {user_text}"""

    raw, err = call_llm([{"role": "user", "content": prompt}], temperature=0.3)
    if err:
        return None, err
    return clean_sql(raw), None


def fix_sql(broken_sql: str, error: str, table_name: str, columns: list) -> tuple:
    """Returns (fixed_sql: str | None, error: str | None)."""
    prompt = f"""Fix this pandasql (SQLite) query. Return ONLY the corrected SQL ending with a semicolon.

TABLE  : {table_name}
COLUMNS: {", ".join(columns)}
BROKEN : {broken_sql}
ERROR  : {error}"""

    raw, err = call_llm([{"role": "user", "content": prompt}], temperature=0.3)
    if err:
        return None, err
    return clean_sql(raw), None


#  3. Smart chart selection  ── LLM picks best chart; robust build_chart

# Keys the user can also pick from the feedback strip
CHART_MENU = {
    "bar":       "Bar chart – compare categories",
    "bar_h":     "Horizontal bar – ranking / many categories",
    "line":      "Line chart – trend over time",
    "pie":       "Pie chart – share / composition",
    "scatter":   "Scatter – correlation between two numeric values",
    "histogram": "Histogram – distribution of one numeric column",
}

# Internal keys (not shown in the user menu)
_INTERNAL_KEYS = {"kpi_cards", "none"}


def pick_chart_type(user_question: str, df: pd.DataFrame) -> str:
    """
    Ask LLM to choose the best chart type.
    Falls back to a heuristic if the LLM returns an invalid key.
    """
    num  = df.select_dtypes(include="number").columns.tolist()
    cat  = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date = df.select_dtypes(include="datetime").columns.tolist()

    all_keys = list(CHART_MENU.keys()) + ["kpi_cards", "none"]
    options  = "\n".join(f"  {k}: {v}" for k, v in CHART_MENU.items())
    options += "\n  kpi_cards: Large number tiles – result is 1-4 key figures"
    options += "\n  none: No chart needed – a table is sufficient"

    prompt = f"""You are a business intelligence expert choosing the best chart.

User question: "{user_question}"

Query result:
  Rows   : {len(df)}
  Columns: {list(df.columns)}
  Numeric: {num}
  Category: {cat}
  Date   : {date}
  Sample : {df.head(3).to_dict(orient="records")}

Available chart types:
{options}

Return ONLY the key (e.g. bar), nothing else."""

    raw, _ = call_llm(
        [{"role": "user", "content": prompt}], temperature=0.0, max_tokens=15
    )
    if raw:
        key = raw.strip().lower().strip('"\'')
        if key in all_keys:
            return key

    # Heuristic fallback
    if len(df) == 1 and num:
        return "kpi_cards"
    if date and num:
        return "line"
    if cat and num:
        return "bar" if len(df) <= 10 else "bar_h"
    if len(num) >= 2:
        return "scatter"
    if len(num) == 1:
        return "histogram"
    return "none"


def build_chart(chart_type: str, df: pd.DataFrame, title: str = ""):
    CLR  = px.colors.qualitative.Set2
    BASE = dict(template="plotly_white", title=title)

    num  = df.select_dtypes(include="number").columns.tolist()
    cat  = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date = df.select_dtypes(include="datetime").columns.tolist()

    if chart_type == "line":
        if num:
            x_col = date[0] if date else (cat[0] if cat else None)
            if x_col:
                return px.line(
                    df, x=x_col, y=num[0],
                    color_discrete_sequence=["#3B7DDD"], **BASE
                )
            return px.line(
                df.reset_index(), x="index", y=num[0],
                color_discrete_sequence=["#3B7DDD"], **BASE
            )

    if chart_type == "bar":
        if cat and num:
            plot = df[[cat[0], num[0]]].dropna().head(20)
            return px.bar(
                plot, x=cat[0], y=num[0],
                color=cat[0], color_discrete_sequence=CLR, **BASE
            )
        if num:
            # No category → use index
            return px.bar(
                df.reset_index(), x="index", y=num[0],
                color_discrete_sequence=CLR, **BASE
            )

    if chart_type == "bar_h":
        if cat and num:
            plot = (
                df[[cat[0], num[0]]]
                .dropna()
                .sort_values(num[0], ascending=True)
                .head(20)
            )
            return px.bar(
                plot, x=num[0], y=cat[0], orientation="h",
                color_discrete_sequence=["#3B7DDD"], **BASE
            )
        if num:
            return px.bar(
                df.reset_index(), x=num[0], y="index", orientation="h",
                color_discrete_sequence=["#3B7DDD"], **BASE
            )

    if chart_type == "pie":
        if cat and num:
            plot = df[[cat[0], num[0]]].dropna().head(8)
            return px.pie(
                plot, names=cat[0], values=num[0],
                color_discrete_sequence=CLR, title=title
            )

    if chart_type == "scatter":
        if len(num) >= 2:
            return px.scatter(
                df, x=num[0], y=num[1],
                color=cat[0] if cat else None,
                color_discrete_sequence=CLR, **BASE
            )
        if num and cat:
            # Only one numeric + one category → fall back to bar
            return build_chart("bar", df, title)

    if chart_type == "histogram":
        if num:
            return px.histogram(
                df, x=num[0],
                color_discrete_sequence=["#3B7DDD"], **BASE
            )

    return None


def render_kpi_cards(df: pd.DataFrame):
    num = df.select_dtypes(include="number").columns.tolist()
    if df.empty or not num:
        return
    row  = df.iloc[0]
    cols = st.columns(min(len(num), 4))
    for i, col_name in enumerate(num[:4]):
        val       = row[col_name]
        formatted = f"{val:,.2f}" if isinstance(val, float) else f"{val:,}"
        with cols[i]:
            st.markdown(
                f'<div class="kpi-tile">'
                f'<div class="kpi-label">{col_name}</div>'
                f'<div class="kpi-value">{formatted}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


#  4. Business insights  (executive-level, no jargon)

def generate_insights(df_result: pd.DataFrame, question: str) -> tuple:
    """Returns (insight_text: str, error: str | None)."""
    if df_result.empty:
        return "No rows were returned by this query.", None

    try:
        stats = df_result.describe(include="all").to_string()
    except Exception:
        stats = "Stats unavailable."

    prompt = f"""You are a business analyst writing for a senior executive.

User asked: "{question}"

Query result stats:
{stats}

Sample rows (up to 20):
{df_result.head(20).to_dict(orient="records")}

Write exactly 3 short sentences:
1. The direct answer to the question using actual numbers.
2. The single most important pattern or anomaly in the data.
3. One concrete business action to consider.

Rules: No bullet points. No data-science jargon. Be direct.
Respond in the same language the user used."""

    content, err = call_llm(
        [{"role": "user", "content": prompt}], temperature=0.3, max_tokens=280
    )
    return content or "Query completed.", err


#  5. Business EDA  ── smart charts based on actual column types

def business_eda(df: pd.DataFrame) -> list:
    """
    Return up to 3 (title, fig) tuples for business-meaningful charts.
    Uses prepared df (with detected datetime columns) for correct rendering.
    """
    out  = []
    CLR  = px.colors.qualitative.Set2
    BASE = dict(template="plotly_white")

    num  = df.select_dtypes(include="number").columns.tolist()
    cat  = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date = df.select_dtypes(include="datetime").columns.tolist()

    # A. Top-10 by primary category × primary numeric
    if cat and num:
        grp = (
            df.groupby(cat[0])[num[0]]
            .sum()
            .nlargest(10)
            .reset_index()
        )
        grp.columns = [cat[0], num[0]]
        fig = px.bar(
            grp, x=num[0], y=cat[0], orientation="h",
            title=f"Top 10  ·  {cat[0]}  by  {num[0]}",
            color=cat[0], color_discrete_sequence=CLR, **BASE,
        )
        fig.update_layout(showlegend=False, yaxis_title="", xaxis_title=num[0])
        out.append((f"Top 10 {cat[0]}", fig))

    # B. Monthly trend (only if a real datetime column exists)
    if date and num and len(out) < 3:
        try:
            tmp = df[[date[0], num[0]]].dropna().copy()
            tmp[date[0]] = pd.to_datetime(tmp[date[0]])
            tmp["_period"] = tmp[date[0]].dt.to_period("M").astype(str)
            trend = tmp.groupby("_period")[num[0]].sum().reset_index()
            trend.columns = ["Month", num[0]]
            fig = px.line(
                trend, x="Month", y=num[0],
                title=f"Monthly Trend  ·  {num[0]}",
                color_discrete_sequence=["#3B7DDD"], **BASE,
            )
            fig.update_layout(xaxis_title="", yaxis_title=num[0])
            out.append(("Monthly Trend", fig))
        except Exception:
            pass

    # C. Composition by second category (only if ≥ 2 cat columns)
    if len(cat) >= 2 and num and len(out) < 3:
        share = (
            df.groupby(cat[1])[num[0]]
            .sum()
            .nlargest(7)
            .reset_index()
        )
        share.columns = [cat[1], num[0]]
        fig = px.pie(
            share, names=cat[1], values=num[0],
            title=f"Share  ·  {cat[1]}",
            color_discrete_sequence=CLR,
        )
        out.append(("Composition", fig))

    # D. Numeric-only summary bar (no category, no date)
    if not cat and not date and num and len(out) < 3:
        summary = df[num[:5]].sum().reset_index()
        summary.columns = ["Metric", "Value"]
        fig = px.bar(
            summary, x="Metric", y="Value",
            title="Key Metrics Summary",
            color="Metric", color_discrete_sequence=CLR, **BASE,
        )
        fig.update_layout(showlegend=False)
        out.append(("Key Metrics", fig))

    return out[:3]


def business_eda_text(df: pd.DataFrame, table_name: str) -> str:
    """
    Ask the LLM for a 2–3 sentence executive summary of the dataset.
    Feeds real stats so the answer is accurate for THIS specific table.
    """
    num = df.select_dtypes(include="number").columns.tolist()
    cat = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date = df.select_dtypes(include="datetime").columns.tolist()

    # Build a concise stats block
    stats_lines = []
    for c in num[:4]:
        stats_lines.append(
            f"  {c}: total={df[c].sum():,.0f}  avg={df[c].mean():,.2f}"
            f"  max={df[c].max():,.2f}  min={df[c].min():,.2f}"
        )

    # Top value per category column
    cat_info = []
    for c in cat[:3]:
        top_val = df[c].value_counts().idxmax() if not df[c].dropna().empty else "—"
        unique  = df[c].nunique()
        cat_info.append(f"  {c}: {unique} unique values, most common = '{top_val}'")

    prompt = f"""You are a business analyst writing for a senior executive.

Dataset name : {table_name}
Total rows   : {df.shape[0]:,}
Columns      : {", ".join(df.columns.tolist())}
Date columns : {date if date else "none detected"}

Numeric column stats:
{chr(10).join(stats_lines) if stats_lines else "  No numeric columns."}

Category column info:
{chr(10).join(cat_info) if cat_info else "  No category columns."}

Write exactly 3 short sentences for a business executive:
1. What this dataset is about (mention the table name and scale).
2. The single most important number or fact visible in the stats above.
3. One specific business question this data can answer immediately.

Be concrete. Use actual numbers. No jargon. No bullet points."""

    text, _ = call_llm(
        [{"role": "user", "content": prompt}], temperature=0.3, max_tokens=220
    )
    return text or "Dataset loaded successfully."


#  Utilities

def load_df(selected: str) -> pd.DataFrame:
    if st.session_state.get("uploaded_df") is not None:
        return st.session_state["uploaded_df"]
    path = f"data/{selected}"
    if os.path.exists(path):
        return pd.read_csv(path)
    st.error(f"File not found: {path}")
    return pd.DataFrame()


def safe_tbl(raw: str) -> str:
    """Convert a file name to a valid SQL table identifier."""
    return re.sub(r"[^A-Za-z0-9_]", "_", raw.replace(".csv", ""))


#  Sidebar
with st.sidebar:
    st.markdown("## 🗄️ Chat with DB")
    st.markdown("---")

    st.markdown('<span class="sec-label">Navigation</span>', unsafe_allow_html=True)
    pages = ["Login", "Select Table", "Chat & Visuals", "📊 My Dashboard"]
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Login"
    page = st.radio("", pages, index=pages.index(st.session_state["current_page"]))
    st.session_state["current_page"] = page

    st.markdown("---")
    st.markdown('<span class="sec-label">SQL History</span>', unsafe_allow_html=True)

    if "sql_history" not in st.session_state:
        st.session_state["sql_history"] = []

    if st.session_state["sql_history"]:
        for i, entry in enumerate(reversed(st.session_state["sql_history"][-6:])):
            idx   = len(st.session_state["sql_history"]) - i
            short = entry["question"][:26] + ("…" if len(entry["question"]) > 26 else "")
            with st.expander(f"Q{idx}: {short}", expanded=(i == 0)):
                st.markdown(
                    f'<div class="sql-box">{entry["sql"]}</div>',
                    unsafe_allow_html=True,
                )
                note = " · auto-fixed" if entry.get("fixed") else ""
                st.markdown(
                    f'<div class="sql-meta">'
                    f'{entry["exec_time"]:.2f}s · {entry["rows"]} rows{note}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.caption("SQL queries will appear here.")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state["messages"]    = []
            st.session_state["sql_history"] = []
            st.rerun()
    with c2:
        if st.button("Clear Dash", use_container_width=True):
            st.session_state["dashboard"] = []
            st.rerun()


#  PAGE: Login
if page == "Login":
    st.markdown('<div class="page-title">Welcome</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Enter your name to start using Chat with Database</div>',
        unsafe_allow_html=True,
    )
    col, _ = st.columns([1, 2])
    with col:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="e.g. Ahmed")
        if st.button("Login", use_container_width=True, type="primary"):
            if username.strip():
                st.session_state.setdefault("session_counter", 0)
                st.session_state["session_counter"] += 1
                st.session_state["username"]     = username.strip()
                st.session_state["current_page"] = "Select Table"
                st.rerun()
            else:
                st.warning("Please enter your name.")
        st.markdown("</div>", unsafe_allow_html=True)
    if "username" in st.session_state:
        st.info(f"Logged in as **{st.session_state['username']}**")


#  PAGE: Select Table
elif page == "Select Table":
    if "username" not in st.session_state:
        st.warning("Please log in first.")
        st.stop()

    st.markdown('<div class="page-title">Select Data Source</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Choose a local CSV or upload your own</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(
            '<div class="card"><div class="card-title">Local Files</div>',
            unsafe_allow_html=True,
        )
        files = (
            [f for f in os.listdir("data") if f.endswith(".csv")]
            if os.path.exists("data") else []
        )
        if files:
            chosen = st.selectbox("Choose from data/:", files)
            if st.button("Load File", use_container_width=True, type="primary"):
                st.session_state.update(
                    selected_table=chosen,
                    uploaded_df=None,
                    messages=[],
                    sql_history=[],
                    current_page="Chat & Visuals",
                )
                st.rerun()
        else:
            st.info("No CSV files found in the data/ folder.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown(
            '<div class="card"><div class="card-title">Upload File</div>',
            unsafe_allow_html=True,
        )
        up = st.file_uploader("Upload a CSV:", type="csv")
        if up:
            try:
                preview = pd.read_csv(up)
                st.success(
                    f"{up.name} — {preview.shape[0]:,} rows × {preview.shape[1]} cols"
                )
                st.dataframe(preview.head(5), use_container_width=True)
                if st.button("Use This File", use_container_width=True, type="primary"):
                    st.session_state.update(
                        selected_table=up.name.replace(".csv", ""),
                        uploaded_df=preview,
                        messages=[],
                        sql_history=[],
                        current_page="Chat & Visuals",
                    )
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not read file: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)


#  PAGE: Chat & Visuals
elif page == "Chat & Visuals":
    if "selected_table" not in st.session_state:
        st.warning("Please select a table first.")
        st.stop()

    # Load raw df and a date-aware prepared version for EDA
    raw_df     = load_df(st.session_state["selected_table"])
    table_name = safe_tbl(st.session_state["selected_table"])

    if raw_df.empty:
        st.stop()

    # Prepared df: same data but with detected datetime columns cast properly
    prep_key = f"prep_df_{table_name}"
    if prep_key not in st.session_state:
        st.session_state[prep_key] = prepare_df(raw_df)
    df = st.session_state[prep_key]

    # Session state init
    st.session_state.setdefault("messages",  [])
    st.session_state.setdefault("dashboard", [])

    st.markdown(
        f'<div class="page-title">Chat with {table_name}</div>',
        unsafe_allow_html=True,
    )
    col_preview = ", ".join(df.columns[:8].tolist())
    if len(df.columns) > 8:
        col_preview += "…"
    st.markdown(
        f'<div class="page-sub">'
        f'{df.shape[0]:,} rows · {df.shape[1]} columns · Columns: {col_preview}'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.expander("📊 Business Overview", expanded=True):

        # KPI tiles: total + avg for each numeric column (max 4)
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            kpi_cols = st.columns(min(len(num_cols), 4))
            for i, c in enumerate(num_cols[:4]):
                total = df[c].sum()
                avg   = df[c].mean()
                with kpi_cols[i]:
                    st.markdown(
                        f'<div class="kpi-tile">'
                        f'<div class="kpi-label">{c}</div>'
                        f'<div class="kpi-value">{total:,.0f}</div>'
                        f'<div class="kpi-sub">avg {avg:,.2f}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("---")

        # Business charts (max 3, computed from prepared df)
        biz_key = f"biz_charts_{table_name}"
        if biz_key not in st.session_state:
            st.session_state[biz_key] = business_eda(df)

        biz_charts = st.session_state[biz_key]
        if biz_charts:
            chart_cols = st.columns(len(biz_charts))
            for (title, fig), col in zip(biz_charts, chart_cols):
                col.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough columns to generate business charts automatically.")

        st.markdown("---")

        # LLM business overview (cached per table)
        eda_text_key = f"biz_eda_text_{table_name}"
        if eda_text_key not in st.session_state:
            with st.spinner("Generating business overview…"):
                st.session_state[eda_text_key] = business_eda_text(df, table_name)
        st.markdown(
            f'<div class="insight-box">📌 {st.session_state[eda_text_key]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if not st.session_state["messages"]:
        st.markdown(
            f"""<div class="empty-state">
                <div class="es-icon">💬</div>
                <div class="es-title">Ask anything about {table_name}</div>
                <div class="es-hint">
                    "Show top 10 customers by revenue"<br>
                    "Which product had the highest sales last month?"<br>
                    "How many orders were placed per region?"
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    for msg in st.session_state["messages"]:

        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-row"><div>'
                f'<div class="bubble-lbl" style="text-align:right">You</div>'
                f'<div class="user-bubble">{msg["content"]}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            continue

        st.markdown(
            f'<div class="bot-row">'
            f'<div class="bot-avatar">🤖</div>'
            f'<div><div class="bubble-lbl">Assistant</div>'
            f'<div class="bot-bubble">{msg["content"]}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Rejection notice
        if msg.get("rejected"):
            st.markdown(
                f'<div class="reject-box">⚠️ <strong>Cannot answer from this dataset.</strong>'
                f'<br>{msg["rejected"]}</div>',
                unsafe_allow_html=True,
            )

        # Error notice
        if msg.get("error"):
            st.markdown(
                f'<div class="err-box">⛔ {msg["error"]}</div>',
                unsafe_allow_html=True,
            )

        # Result: KPI tiles or data table
        if msg.get("chart_type") == "kpi_cards" and msg.get("dataframe") is not None:
            render_kpi_cards(msg["dataframe"])
        elif msg.get("dataframe") is not None:
            st.dataframe(msg["dataframe"], use_container_width=True)

        # Chart
        msg_id = msg.get("id", id(msg))
        if msg.get("chart") is not None:
            st.plotly_chart(
                msg["chart"],
                use_container_width=True,
                key=f"ch_{msg_id}",
            )

        # Insight
        if msg.get("insight"):
            st.markdown(
                f'<div class="insight-box">💡 {msg["insight"]}</div>',
                unsafe_allow_html=True,
            )

        # ── Chart feedback strip ──────────────────────────────────────────────
        # Shown whenever there is a chart and the question was not rejected
        if msg.get("chart") is not None and not msg.get("rejected"):
            st.markdown(
                '<div class="chart-feedback">'
                '📊 <strong>Change chart type or save to dashboard:</strong>'
                '</div>',
                unsafe_allow_html=True,
            )

            fc1, fc2, fc3, fc4, fc5 = st.columns([1.6, 0.9, 0.9, 0.9, 1.6])

            # Add to Dashboard
            with fc1:
                if st.button("✅ Add to Dashboard", key=f"add_{msg_id}",
                             use_container_width=True):
                    st.session_state["dashboard"].append({
                        "title":   msg["content"],
                        "chart":   msg["chart"],
                        "insight": msg.get("insight", ""),
                    })
                    st.toast("Added to dashboard ✓", icon="✅")

            # Try Bar
            with fc2:
                if st.button("📊 Bar", key=f"bar_{msg_id}",
                             use_container_width=True):
                    df_r = msg.get("_df_for_regen")
                    if df_r is not None:
                        new_fig = build_chart("bar", df_r, msg["content"])
                        if new_fig:
                            msg["chart"]      = new_fig
                            msg["chart_type"] = "bar"
                            st.rerun()

            # Try Horizontal Bar
            with fc3:
                if st.button("📉 H-Bar", key=f"barh_{msg_id}",
                             use_container_width=True):
                    df_r = msg.get("_df_for_regen")
                    if df_r is not None:
                        new_fig = build_chart("bar_h", df_r, msg["content"])
                        if new_fig:
                            msg["chart"]      = new_fig
                            msg["chart_type"] = "bar_h"
                            st.rerun()

            # Try Line
            with fc4:
                if st.button("📈 Line", key=f"line_{msg_id}",
                             use_container_width=True):
                    df_r = msg.get("_df_for_regen")
                    if df_r is not None:
                        new_fig = build_chart("line", df_r, msg["content"])
                        if new_fig:
                            msg["chart"]      = new_fig
                            msg["chart_type"] = "line"
                            st.rerun()

            # Other chart types via selectbox + Apply button
            with fc5:
                other_key  = f"other_sel_{msg_id}"
                apply_key  = f"other_apply_{msg_id}"
                other_opts = [""] + [k for k in CHART_MENU if k not in ("bar", "bar_h", "line")]
                choice = st.selectbox(
                    "Other type",
                    other_opts,
                    key=other_key,
                    label_visibility="collapsed",
                )
                if choice:
                    if st.button("Apply", key=apply_key, use_container_width=True):
                        df_r = msg.get("_df_for_regen")
                        if df_r is not None:
                            new_fig = build_chart(choice, df_r, msg["content"])
                            if new_fig:
                                msg["chart"]      = new_fig
                                msg["chart_type"] = choice
                                st.rerun()

    user_input = st.chat_input(f"Ask about {table_name}…")

    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})

        # Step 1: Guardrail validation
        with st.spinner("Checking your question…"):
            is_valid, reject_reason = validate_question(
                user_input, table_name, raw_df.columns.tolist()
            )

        if not is_valid:
            st.session_state["messages"].append({
                "role":     "assistant",
                "content":  "I can't answer that from this dataset.",
                "rejected": reject_reason,
            })
            st.rerun()

        # Step 2: Generate SQL  (uses raw_df column names for SQL correctness)
        with st.spinner("Generating SQL…"):
            sql, sql_err = generate_sql(user_input, table_name, raw_df.columns.tolist())

        if sql_err or not sql:
            st.session_state["messages"].append({
                "role":    "assistant",
                "content": "Could not generate SQL for your question.",
                "error":   sql_err or "Model returned an empty response.",
            })
            st.rerun()

        # Step 3: Execute SQL (pandasql uses raw_df — avoids datetime edge-cases)
        t0        = time.time()
        local_env = {table_name: raw_df}
        result_df = None
        used_sql  = sql
        fixed     = False
        run_error = None

        try:
            result_df = ps.sqldf(sql, local_env)
        except Exception as e1:
            with st.spinner("Auto-fixing SQL…"):
                fixed_sql, fix_err = fix_sql(
                    sql, str(e1), table_name, raw_df.columns.tolist()
                )
            if fixed_sql and not fix_err:
                try:
                    result_df = ps.sqldf(fixed_sql, local_env)
                    used_sql  = fixed_sql
                    fixed     = True
                except Exception as e2:
                    run_error = f"Original error: {e1} | After fix: {e2}"
            else:
                run_error = str(e1) + (f" | Fix error: {fix_err}" if fix_err else "")

        exec_time = time.time() - t0

        st.session_state["sql_history"].append({
            "question":  user_input,
            "sql":       used_sql,
            "exec_time": exec_time,
            "rows":      len(result_df) if result_df is not None else 0,
            "fixed":     fixed,
        })

        if run_error or result_df is None:
            st.session_state["messages"].append({
                "role":    "assistant",
                "content": "The query could not be executed.",
                "error":   run_error or "Unknown execution error.",
            })
            st.rerun()

        # Step 4: Smart chart selection (prepare result_df for better type detection)
        result_df_prep = prepare_df(result_df)

        with st.spinner("Choosing best visualization…"):
            chart_type = pick_chart_type(user_input, result_df_prep)

        fig = build_chart(chart_type, result_df_prep, title=user_input[:60])

        # Step 5: Business insights
        with st.spinner("Generating business insight…"):
            insight, ins_err = generate_insights(result_df, user_input)

        note = " *(auto-corrected)*" if fixed else ""
        st.session_state["messages"].append({
            "role":          "assistant",
            "content":       f"**{len(result_df):,} rows** returned in {exec_time:.2f}s{note}",
            "dataframe":     result_df.head(500) if not result_df.empty else None,
            "chart":         fig,
            "chart_type":    chart_type,
            "_df_for_regen": result_df_prep,   # prepared df for chart rebuilding
            "insight":       insight,
            "error":         ins_err,
            "id":            len(st.session_state["messages"]),
        })
        st.rerun()


#  PAGE: My Dashboard
elif page == "📊 My Dashboard":
    st.markdown('<div class="page-title">📊 My Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Charts you confirmed as useful — '
        'add them from the Chat page</div>',
        unsafe_allow_html=True,
    )

    st.session_state.setdefault("dashboard", [])
    dash = st.session_state["dashboard"]

    if not dash:
        st.markdown(
            """<div class="empty-state">
                <div class="es-icon">📋</div>
                <div class="es-title">Your dashboard is empty</div>
                <div class="es-hint">
                    Go to <strong>Chat &amp; Visuals</strong>, ask a question,<br>
                    then click <strong>✅ Add to Dashboard</strong> below any chart.
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"**{len(dash)} chart(s) saved**")
        st.markdown("---")
        for i in range(0, len(dash), 2):
            row_cols = st.columns(2)
            for j, col in enumerate(row_cols):
                idx = i + j
                if idx >= len(dash):
                    break
                item = dash[idx]
                with col:
                    st.markdown(
                        f'<div class="dash-panel">'
                        f'<div class="dash-header">{item["title"][:70]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(
                        item["chart"],
                        use_container_width=True,
                        key=f"dash_{idx}",
                    )
                    if item.get("insight"):
                        st.markdown(
                            f'<div class="insight-box" style="font-size:.82rem">'
                            f'💡 {item["insight"]}</div>',
                            unsafe_allow_html=True,
                        )
                    if st.button("🗑️ Remove", key=f"del_{idx}"):
                        st.session_state["dashboard"].pop(idx)
                        st.rerun()