import streamlit as st
import pandas as pd
import os
import plotly.express as px
import requests
import pandasql as ps
import time
import re

st.set_page_config(
    page_title="Chat with Database",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"], .stApp, .block-container,
p, span, div, label, li, td, th, h1, h2, h3, h4 {
    font-family: 'Inter', sans-serif !important;
    color: #1C2333;
}
.stApp { background: #EEF1F7 !important; }
.block-container { padding-top: 1.6rem !important; max-width: 1200px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1C2333 !important;
    border-right: 1px solid #2E3A52;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] li {
    color: #C8D3E6 !important;
    font-size: .88rem !important;
}
section[data-testid="stSidebar"] h2 {
    color: #FFFFFF !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] hr { border-color: #2E3A52 !important; }
section[data-testid="stSidebar"] .stRadio > div { gap: 4px !important; }
section[data-testid="stSidebar"] .stRadio label {
    color: #C8D3E6 !important;
    background: transparent !important;
    padding: 6px 10px !important;
    border-radius: 7px !important;
    transition: background .15s;
}
section[data-testid="stSidebar"] .stRadio label:hover { background: #2E3A52 !important; }
section[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
    background: #3B7DDD !important;
    border-color: #3B7DDD !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: #2E3A52 !important;
    color: #C8D3E6 !important;
    border: 1px solid #3D4F6E !important;
    border-radius: 8px !important;
    font-size: .85rem !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #3B7DDD !important;
    color: #FFFFFF !important;
    border-color: #3B7DDD !important;
}
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: #253047 !important;
    color: #C8D3E6 !important;
    border-radius: 6px !important;
    font-size: .78rem !important;
}
section[data-testid="stSidebar"] .streamlit-expanderContent {
    background: #1C2333 !important;
}

/* ── Main content cards ── */
.card {
    background: #FFFFFF;
    border: 1px solid #D5DCE8;
    border-radius: 12px;
    padding: 1.3rem 1.6rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
}
.card-title {
    font-size: .72rem !important;
    font-weight: 700 !important;
    color: #5E6E8A !important;
    letter-spacing: .8px;
    text-transform: uppercase;
    margin-bottom: .75rem;
}

/* ── Page typography ── */
.page-title {
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    color: #1C2333 !important;
    margin-bottom: .15rem;
}
.page-sub {
    font-size: .88rem !important;
    color: #5E6E8A !important;
    margin-bottom: 1.4rem;
}
.sec-label {
    font-size: .68rem !important;
    font-weight: 700 !important;
    color: #8496B0 !important;
    letter-spacing: .9px;
    text-transform: uppercase;
    margin: 14px 0 6px;
    display: block;
}

/* ── Metrics ── */
div[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #D5DCE8 !important;
    border-radius: 10px !important;
    padding: 14px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.05) !important;
}
div[data-testid="metric-container"] label {
    color: #5E6E8A !important;
    font-size: .78rem !important;
    font-weight: 600 !important;
}
div[data-testid="stMetricValue"] > div {
    color: #1C2333 !important;
    font-weight: 700 !important;
    font-size: 1.4rem !important;
}

/* ── Streamlit expander (main area) ── */
.streamlit-expanderHeader {
    background: #FFFFFF !important;
    border: 1px solid #D5DCE8 !important;
    border-radius: 10px !important;
    color: #1C2333 !important;
    font-weight: 600 !important;
    font-size: .92rem !important;
    padding: 10px 16px !important;
}
.streamlit-expanderContent {
    background: #FFFFFF !important;
    border: 1px solid #D5DCE8 !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    padding: 1rem 1.4rem !important;
}

/* ── Dataframe / table ── */
.stDataFrame, [data-testid="stDataFrame"] {
    border: 1px solid #D5DCE8 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
.stDataFrame thead th {
    background: #F0F2F6 !important;
    color: #1C2333 !important;
    font-weight: 600 !important;
}
.stDataFrame tbody td { color: #1C2333 !important; }

/* ── Selectbox / input / file uploader ── */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    background: #FFFFFF !important;
    border: 1px solid #C5CFDF !important;
    border-radius: 8px !important;
    color: #1C2333 !important;
}
.stSelectbox label, .stTextInput label, .stFileUploader label {
    color: #1C2333 !important;
    font-weight: 600 !important;
    font-size: .88rem !important;
}
[data-baseweb="select"] { background: #FFFFFF !important; }
[data-baseweb="select"] span,
[data-baseweb="select"] div { color: #1C2333 !important; }
[data-baseweb="popover"] { background: #FFFFFF !important; }
[data-baseweb="menu"] li { color: #1C2333 !important; background: #FFFFFF !important; }
[data-baseweb="menu"] li:hover { background: #EEF1F7 !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #FFFFFF !important;
    border: 2px dashed #C5CFDF !important;
    border-radius: 10px !important;
    padding: 12px !important;
}
[data-testid="stFileUploader"] span { color: #5E6E8A !important; }

/* ── Chat input ── */
[data-testid="stChatInput"] > div {
    background: #FFFFFF !important;
    border: 1px solid #C5CFDF !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.06) !important;
}
[data-testid="stChatInput"] textarea {
    color: #1C2333 !important;
    background: transparent !important;
    font-size: .92rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #9EABC0 !important; }

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: #1C2333 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    transition: background .2s;
}
.stButton > button[kind="primary"]:hover { background: #3B7DDD !important; }
.stButton > button:not([kind="primary"]) {
    background: #FFFFFF !important;
    color: #1C2333 !important;
    border: 1px solid #C5CFDF !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

/* ── Alerts ── */
.stSuccess > div { background: #F0FFF4 !important; color: #1A5C35 !important; border-color: #86EFAC !important; }
.stWarning > div { background: #FFFBEB !important; color: #78350F !important; border-color: #FCD34D !important; }
.stError   > div { background: #FFF0F0 !important; color: #7B1515 !important; border-color: #FFCDD2 !important; }
.stInfo    > div { background: #EEF4FF !important; color: #1A3460 !important; border-color: #BFDBFE !important; }
.stSuccess p, .stWarning p, .stError p, .stInfo p { color: inherit !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #3B7DDD !important; }

/* ── Chat bubbles ── */
.user-row  { display:flex; justify-content:flex-end; margin:10px 0; }
.user-bub  {
    background: #1C2333; color: #F5F7FA !important;
    border-radius: 16px 16px 4px 16px;
    padding: 10px 16px; max-width: 66%;
    font-size: .91rem !important; line-height: 1.55;
}
.bot-row   { display:flex; align-items:flex-start; gap:10px; margin:10px 0; }
.bot-av    {
    width:34px; height:34px; background:#E8F0FE;
    border-radius:50%; display:flex; align-items:center;
    justify-content:center; font-size:.95rem; flex-shrink:0; margin-top:2px;
}
.bot-bub   {
    background:#FFFFFF; border:1px solid #D5DCE8;
    border-radius:4px 16px 16px 16px;
    padding:10px 16px; max-width:82%;
    font-size:.91rem !important; line-height:1.6; color:#1C2333 !important;
    box-shadow:0 1px 3px rgba(0,0,0,.05);
}
.bub-lbl   {
    font-size:.64rem !important; font-weight:600 !important;
    color:#9EABC0 !important; margin-bottom:3px; letter-spacing:.4px;
}

/* ── Insight / error boxes ── */
.insight-box {
    background:#EEF4FF; border:1px solid #C3D4F7;
    border-left:4px solid #3B7DDD; border-radius:8px;
    padding:12px 16px; margin-top:10px;
    font-size:.88rem !important; color:#1A3460 !important; line-height:1.65;
}
.err-box {
    background:#FFF0F0; border:1px solid #FFCDD2;
    border-left:4px solid #E53935; border-radius:8px;
    padding:10px 14px; margin-top:8px;
    font-size:.85rem !important; color:#7B1515 !important;
}

/* ── SQL box (sidebar) ── */
.sql-box {
    background:#0D1117; border-left:3px solid #3B7DDD;
    border-radius:4px; padding:8px 11px;
    font-family:'Courier New',monospace;
    font-size:.72rem !important; color:#79C0FF !important;
    white-space:pre-wrap; word-break:break-all; margin-top:4px;
}
.sql-meta { font-size:.65rem !important; color:#8496B0 !important; margin-top:4px; }

/* ── Empty state ── */
.empty-state { text-align:center; padding:50px 20px; }
.es-icon  { font-size:2rem; margin-bottom:10px; }
.es-title { font-size:1rem !important; font-weight:600 !important; color:#4A5568 !important; margin-bottom:6px; }
.es-hint  { font-size:.81rem !important; line-height:1.6; color:#7A8DA8 !important; }

/* ── Login box ── */
.login-box {
    background:#FFFFFF; border:1px solid #D5DCE8;
    border-radius:14px; padding:2rem 2.2rem; max-width:380px;
    box-shadow:0 4px 18px rgba(0,0,0,.09);
}

hr { border-color:#D5DCE8 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def get_api_key() -> str:
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        return os.environ.get("OPENROUTER_API_KEY", "")


def call_llm(messages: list, temperature: float = 0.0) -> tuple[str | None, str | None]:
    key = get_api_key()
    if not key:
        return None, "API Key missing — add OPENROUTER_API_KEY to .streamlit/secrets.toml"
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "openai/gpt-4o-mini", "messages": messages,
                  "temperature": temperature, "max_tokens": 600},
            timeout=45,
        )
        data = r.json()
        if "error" in data:
            return None, f"OpenRouter: {data['error'].get('message', data['error'])}"
        return data["choices"][0]["message"]["content"].strip(), None
    except requests.exceptions.Timeout:
        return None, "Request timed out (45 s). Check your internet."
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach OpenRouter. Check your internet connection."
    except Exception as e:
        return None, f"Unexpected error: {e}"


def clean_sql(raw: str) -> str:
    raw = re.sub(r"```sql", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw).strip()
    if ";" in raw:
        raw = raw[: raw.index(";") + 1]
    return raw.strip()


def generate_sql(question: str, tbl: str, cols: list) -> tuple[str | None, str | None]:
    prompt = f"""You are an expert SQL generator for pandasql (SQLite dialect).

TABLE NAME : {tbl}   ← use EXACTLY this, case-sensitive
COLUMNS    : {", ".join(cols)}

RULES (follow strictly):
- Output ONLY the raw SQL query, ending with a semicolon
- No explanation, no markdown, no backticks, no comments
- Use the EXACT table name and column names above
- Multiple conditions → use AND in WHERE clause
- Aggregations → GROUP BY all non-aggregated columns
- Numeric comparisons: use >, <, >=, <=, = directly on column names

USER REQUEST: {question}"""
    raw, err = call_llm([{"role": "user", "content": prompt}], temperature=0.0)
    if err:
        return None, err
    return clean_sql(raw), None


def fix_sql(broken: str, error: str, tbl: str, cols: list) -> tuple[str | None, str | None]:
    prompt = f"""Fix this pandasql (SQLite) query. Return ONLY corrected SQL ending with semicolon.

TABLE  : {tbl}
COLUMNS: {", ".join(cols)}
BROKEN : {broken}
ERROR  : {error}"""
    raw, err = call_llm([{"role": "user", "content": prompt}], temperature=0.0)
    if err:
        return None, err
    return clean_sql(raw), None


def generate_insights(df_r: pd.DataFrame, question: str) -> tuple[str, str | None]:
    if df_r.empty:
        return "No rows returned by this query.", None
    try:
        stats = df_r.describe(include="all").to_string()
    except Exception:
        stats = "N/A"
    prompt = f"""You are a senior data analyst.
User asked: "{question}"
Stats:
{stats}
Sample (first 20 rows): {df_r.head(20).to_dict(orient="records")}

Provide:
1. A 2-sentence summary of what the data shows
2. 2-3 specific insights with actual numbers
3. One actionable recommendation
Be concise. Reply in the same language as the user's question."""
    content, err = call_llm([{"role": "user", "content": prompt}], temperature=0.3)
    return content or "Query executed successfully.", err


def auto_visualize(df: pd.DataFrame, title: str = "Result"):
    if df.empty or df.shape[1] < 1:
        return None
    num  = df.select_dtypes(include="number").columns.tolist()
    cat  = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date = df.select_dtypes(include="datetime").columns.tolist()
    CLR  = px.colors.qualitative.Set2
    if date and num:
        return px.line(df, x=date[0], y=num[0], title=title,
                       template="plotly_white", color_discrete_sequence=["#3B7DDD"])
    if cat and num:
        p = df[[cat[0], num[0]]].dropna().head(25)
        if len(p) <= 14:
            return px.bar(p, x=cat[0], y=num[0], title=title, color=cat[0],
                          template="plotly_white", color_discrete_sequence=CLR)
        return px.bar(p.sort_values(num[0], ascending=True),
                      x=num[0], y=cat[0], orientation="h", title=title,
                      template="plotly_white", color_discrete_sequence=["#3B7DDD"])
    if len(num) >= 2:
        return px.scatter(df, x=num[0], y=num[1], color=cat[0] if cat else None,
                          title=title, template="plotly_white",
                          color_discrete_sequence=CLR)
    if len(num) == 1:
        return px.histogram(df, x=num[0], title=title,
                            template="plotly_white",
                            color_discrete_sequence=["#3B7DDD"])
    return None


def eda_charts(df: pd.DataFrame) -> list:
    figs = []
    num = df.select_dtypes(include="number").columns.tolist()
    cat = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if num:
        figs.append(px.histogram(df, x=num[0], nbins=30,
            title=f"Distribution — {num[0]}", template="plotly_white",
            color_discrete_sequence=["#3B7DDD"]))
    if len(num) >= 2:
        figs.append(px.box(df, y=num[1], title=f"Spread — {num[1]}",
            template="plotly_white", color_discrete_sequence=["#6366F1"]))
    if cat:
        vc = df[cat[0]].value_counts().head(15).reset_index()
        vc.columns = [cat[0], "count"]
        figs.append(px.bar(vc, x=cat[0], y="count",
            title=f"Top values — {cat[0]}", template="plotly_white",
            color_discrete_sequence=["#10B981"]))
    if cat and num:
        grp = df.groupby(cat[0])[num[0]].mean().reset_index().head(15)
        grp.columns = [cat[0], f"avg_{num[0]}"]
        figs.append(px.bar(grp, x=cat[0], y=f"avg_{num[0]}",
            title=f"Avg {num[0]} by {cat[0]}", template="plotly_white",
            color=cat[0], color_discrete_sequence=px.colors.qualitative.Pastel))
    if len(num) >= 2:
        figs.append(px.scatter(df, x=num[0], y=num[1],
            color=cat[0] if cat else None, opacity=.7,
            title=f"{num[0]} vs {num[1]}", template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Set2))
    if len(num) >= 3:
        corr = df[num[:8]].corr().round(2)
        figs.append(px.imshow(corr, text_auto=True, title="Correlation Heatmap",
            template="plotly_white", color_continuous_scale="Blues"))
    return figs


def load_df(selected: str) -> pd.DataFrame:
    if st.session_state.get("uploaded_df") is not None:
        return st.session_state["uploaded_df"]
    path = f"data/{selected}"
    if os.path.exists(path):
        return pd.read_csv(path)
    st.error(f"File not found: {path}")
    return pd.DataFrame()


def safe_tbl(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", raw.replace(".csv", ""))


# ─────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗄️ Chat with DB")
    st.markdown("---")

    st.markdown('<span class="sec-label">Navigation</span>', unsafe_allow_html=True)
    pages = ["Login", "Select Table", "Chat & Visuals"]
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
                st.markdown(f'<div class="sql-box">{entry["sql"]}</div>',
                            unsafe_allow_html=True)
                note = " · auto-fixed" if entry.get("fixed") else ""
                st.markdown(
                    f'<div class="sql-meta">{entry["exec_time"]:.2f}s · '
                    f'{entry["rows"]} rows{note}</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.caption("SQL queries will appear here.")

    st.markdown("---")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state["messages"]   = []
        st.session_state["sql_history"] = []
        st.rerun()

#  PAGE: Login
if page == "Login":
    st.markdown('<p class="page-title">Welcome</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Enter your name to start using Chat with Database</p>',
                unsafe_allow_html=True)

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
        st.markdown('</div>', unsafe_allow_html=True)

    if "username" in st.session_state:
        st.info(f"Logged in as **{st.session_state['username']}**")

#  PAGE: Select Table
elif page == "Select Table":
    if "username" not in st.session_state:
        st.warning("Please log in first.")
        st.stop()

    st.markdown('<p class="page-title">Select Data Source</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Choose a local CSV file or upload your own</p>',
                unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="card"><div class="card-title">Local Files</div>',
                    unsafe_allow_html=True)
        files = (
            [f for f in os.listdir("data") if f.endswith(".csv")]
            if os.path.exists("data") else []
        )
        if files:
            chosen = st.selectbox("Choose a CSV from data/ folder:", files)
            if st.button("Load File", use_container_width=True, type="primary"):
                st.session_state.update(
                    selected_table=chosen, uploaded_df=None,
                    messages=[], sql_history=[],
                    current_page="Chat & Visuals"
                )
                st.rerun()
        else:
            st.info("No CSV files found in the data/ folder.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="card"><div class="card-title">Upload File</div>',
                    unsafe_allow_html=True)
        up = st.file_uploader("Upload a CSV:", type="csv")
        if up:
            try:
                prev = pd.read_csv(up)
                st.success(f"{up.name} — {prev.shape[0]:,} rows {prev.shape[1]} cols")
                st.dataframe(prev.head(5), use_container_width=True)
                if st.button("Use This File", use_container_width=True, type="primary"):
                    st.session_state.update(
                        selected_table=up.name.replace(".csv", ""),
                        uploaded_df=prev,
                        messages=[], sql_history=[],
                        current_page="Chat & Visuals"
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"Could not read file: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

#  PAGE: Chat & Visuals
elif page == "Chat & Visuals":
    if "selected_table" not in st.session_state:
        st.warning("Please select a table first.")
        st.stop()

    df  = load_df(st.session_state["selected_table"])
    tbl = safe_tbl(st.session_state["selected_table"])

    if df.empty:
        st.stop()

    st.markdown(f'<p class="page-title">Chat with {tbl}</p>', unsafe_allow_html=True)
    col_preview = ", ".join(df.columns[:7].tolist()) + ("…" if len(df.columns) > 7 else "")
    st.markdown(
        f'<p class="page-sub">{df.shape[0]:,} rows · {df.shape[1]} columns · '
        f'Columns: {col_preview}</p>',
        unsafe_allow_html=True,
    )

    # Dataset Overview
    with st.expander("Dataset Overview & Exploratory Charts", expanded=True):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rows",           f"{df.shape[0]:,}")
        m2.metric("Columns",        df.shape[1])
        m3.metric("Missing Values", int(df.isna().sum().sum()))
        m4.metric("Memory",         f"{df.memory_usage(deep=True).sum()/1024:.1f} KB")

        st.markdown("---")
        charts = eda_charts(df)
        for r in range(0, len(charts), 3):
            row = charts[r: r+3]
            for col, fig in zip(st.columns(len(row)), row):
                col.plotly_chart(fig, use_container_width=True)

        eda_key = f"eda_{tbl}"
        if eda_key not in st.session_state:
            with st.spinner("Generating dataset overview..."):
                prompt = f"""Dataset: {tbl}
Shape  : {df.shape[0]} rows, {df.shape[1]} columns
Columns: {dict(df.dtypes.astype(str))}
Missing: {df.isna().sum().to_dict()}
Stats  :
{df.describe(include='number').to_string()}
Write 3-4 factual sentences: what this dataset represents, key ranges, quality notes."""
                text, _ = call_llm([{"role": "user", "content": prompt}], temperature=0.3)
                st.session_state[eda_key] = text or "Dataset loaded."
        st.markdown(f'<div class="insight-box">{st.session_state[eda_key]}</div>',
                    unsafe_allow_html=True)

        st.markdown("---")
        col_df = pd.DataFrame({
            "Column":   df.columns,
            "Type":     df.dtypes.astype(str).values,
            "Non-Null": df.notnull().sum().values,
            "Null %":   (df.isnull().mean()*100).round(1).astype(str) + "%",
            "Sample":   [str(df[c].dropna().iloc[0]) if not df[c].dropna().empty else "—"
                         for c in df.columns],
        })
        st.dataframe(col_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Chat ────────────────────────────────
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if not st.session_state["messages"]:
        st.markdown(
            f"""<div class="empty-state">
                <div class="es-icon">💬</div>
                <div class="es-title">Ask anything about {tbl}</div>
                <div class="es-hint">
                    "Show top 10 customers by revenue"<br>
                    "Find customers with overage_charges &gt; 50 AND call_minutes &gt; 100 AND payment_delay &gt; 5"<br>
                    "What is the average monthly fee per plan type?"
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-row"><div>'
                f'<div class="bub-lbl" style="text-align:right">You</div>'
                f'<div class="user-bub">{msg["content"]}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="bot-row"><div class="bot-av">🤖</div><div>'
                f'<div class="bub-lbl">Assistant</div>'
                f'<div class="bot-bub">{msg["content"]}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            if msg.get("error"):
                st.markdown(f'<div class="err-box">{msg["error"]}</div>',
                            unsafe_allow_html=True)
            if msg.get("dataframe") is not None:
                st.dataframe(msg["dataframe"], use_container_width=True)
            if msg.get("chart") is not None:
                st.plotly_chart(msg["chart"], use_container_width=True,
                                key=f"ch_{msg.get('id', id(msg))}")
            if msg.get("insight"):
                st.markdown(f'<div class="insight-box">{msg["insight"]}</div>',
                            unsafe_allow_html=True)

    # Input
    user_input = st.chat_input(f"Ask about {tbl}...")

    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})

        with st.spinner("Generating SQL..."):
            sql, sql_err = generate_sql(user_input, tbl, df.columns.tolist())

        if sql_err or not sql:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": "Could not generate SQL for your question.",
                "error": sql_err or "Model returned empty response.",
            })
            st.rerun()

        t0        = time.time()
        env       = {tbl: df}
        result_df = None
        used_sql  = sql
        fixed     = False
        run_err   = None

        try:
            result_df = ps.sqldf(sql, env)
        except Exception as e1:
            with st.spinner("Auto-fixing SQL..."):
                fsql, ferr = fix_sql(sql, str(e1), tbl, df.columns.tolist())
            if fsql:
                try:
                    result_df = ps.sqldf(fsql, env)
                    used_sql  = fsql
                    fixed     = True
                except Exception as e2:
                    run_err = f"Original: {e1} | After fix: {e2}"
            else:
                run_err = f"{e1}" + (f" | Fix error: {ferr}" if ferr else "")

        exec_time = time.time() - t0
        st.session_state["sql_history"].append({
            "question": user_input, "sql": used_sql,
            "exec_time": exec_time,
            "rows": len(result_df) if result_df is not None else 0,
            "fixed": fixed,
        })

        if run_err or result_df is None:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": "The query could not be executed.",
                "error": run_err or "Unknown execution error.",
            })
            st.rerun()

        with st.spinner("Analyzing results..."):
            insight, ins_err = generate_insights(result_df, user_input)

        fig  = auto_visualize(result_df, title=user_input[:60])
        note = " *(auto-corrected)*" if fixed else ""

        st.session_state["messages"].append({
            "role":      "assistant",
            "content":   f"**{len(result_df):,} rows** returned in {exec_time:.2f}s{note}",
            "dataframe": result_df.head(500) if not result_df.empty else None,
            "chart":     fig,
            "insight":   insight,
            "error":     ins_err,
            "id":        len(st.session_state["messages"]),
        })
        st.rerun()