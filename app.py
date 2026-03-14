import streamlit as st
import pandas as pd
import os
import re
import json
import time
import requests

import plotly.express as px
import plotly.graph_objects as go
import pandasql as ps

try:
    import sqlalchemy
    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False


DEFAULT_BACKEND = "ollama"
DEFAULT_MODEL   = "mistral"

OLLAMA_MODELS = {
    "mistral":       "Mistral 7B",
    "qwen2.5":       "Qwen 2.5 7B",
    "llama3.2":      "Llama 3.2 3B",
    "phi3":          "Phi-3 Mini",
    "gemma2":        "Gemma 2 9B",
    "qwen2.5:14b":   "Qwen 2.5 14B",
    "mistral:7b-instruct": "Mistral 7B Instruct",
}

OPENROUTER_MODELS = {
    "openai/gpt-4o-mini":          "GPT-4o Mini",
    "anthropic/claude-3-haiku":    "Claude 3 Haiku",
    "mistralai/mistral-7b-instruct":"Mistral 7B (cloud)",
    "qwen/qwen-2-7b-instruct":     "Qwen 2 7B (cloud)",
}

OLLAMA_HOST = "http://localhost:11434"

TOKENS_DEFAULT   = 600
TOKENS_SQL       = 700
TOKENS_CHART     = 15
TOKENS_INSIGHTS  = 350
TOKENS_GUARDRAIL = 100
TOKENS_EDA_TEXT  = 250

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

.stApp { background: #F0F2F6 !important; }
.block-container { padding-top: 1.6rem !important; max-width: 1240px; }

/* ── Main area text — targets only direct Streamlit elements, not custom boxes ── */
.stApp p:not(.insight-box p):not(.reject-box p):not(.err-box p),
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #1C2333; }

/* ── KPI tile text ── (defined separately in KPI section below) ── */

/* ── Labels ── */
label, .stTextInput label, .stSelectbox label,
.stTextInput > label, .stSelectbox > label,
.stFileUploader label, .stRadio label,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p {
    color: #1C2333 !important; font-size: .88rem !important; font-weight: 500 !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextInput textarea,
input[type="text"], input[type="password"], input[type="number"], textarea {
    color: #1C2333 !important; background: #FFFFFF !important;
    border: 1px solid #C5CFDF !important; border-radius: 8px !important;
}
.stTextInput input::placeholder { color: #9EABC0 !important; }
.stTextInput input:focus, input:focus {
    border-color: #3B7DDD !important;
    box-shadow: 0 0 0 2px rgba(59,125,221,.15) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #FFFFFF !important; border: 1px solid #C5CFDF !important;
    border-radius: 8px !important; color: #1C2333 !important;
}

/* ── Radio ── */
.stRadio > div label { color: #1C2333 !important; font-size: .9rem !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #1C2333 !important; }
section[data-testid="stSidebar"] > div { background: #1C2333 !important; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] li, section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] .stMarkdown p {
    color: #CDD5DF !important; font-size: .88rem !important;
}
section[data-testid="stSidebar"] h2 {
    color: #FFFFFF !important; font-size: 1rem !important; font-weight: 700 !important;
}
section[data-testid="stSidebar"] hr { border-color: #2E3A52 !important; }
section[data-testid="stSidebar"] .stRadio label { color: #CDD5DF !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: #2E3A52 !important; color: #CDD5DF !important;
    border: 1px solid #3D4F6E !important; border-radius: 7px !important; width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #3B7DDD !important; color: #FFF !important;
}
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: #253047 !important; border-radius: 6px !important;
    font-size: .78rem !important; color: #CDD5DF !important;
}
section[data-testid="stSidebar"] .streamlit-expanderContent { background: #1C2333 !important; }

/* ── Typography ── */
.page-title { font-size: 1.5rem !important; font-weight: 700 !important;
              color: #1C2333 !important; margin-bottom: .15rem; }
.page-sub   { font-size: .87rem !important; color: #5E6E8A !important; margin-bottom: 1.3rem; }
.sec-label  { font-size: .65rem !important; font-weight: 700 !important; color: #8496B0 !important;
              letter-spacing: .9px; text-transform: uppercase; margin: 14px 0 6px; display: block; }

/* ── Cards ── */
.card { background: #FFF; border: 1px solid #DDE3EE; border-radius: 12px;
        padding: 1.2rem 1.4rem; margin-bottom: .9rem; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.card-title { font-size: .7rem !important; font-weight: 700 !important; color: #5E6E8A !important;
              letter-spacing: .8px; text-transform: uppercase; margin-bottom: .7rem; }

/* ── Section header inside overview ── */
.ov-section { font-size: .72rem !important; font-weight: 700 !important;
              color: #8496B0 !important; text-transform: uppercase;
              letter-spacing: .8px; margin: 18px 0 8px; border-bottom: 1px solid #EEF2FA;
              padding-bottom: 4px; }

/* ── Chat bubbles ── */
.user-row    { display: flex; justify-content: flex-end; margin: 10px 0; }
.user-bubble { background: #1C2333; color: #F5F7FA !important;
               border-radius: 16px 16px 4px 16px;
               padding: 10px 16px; max-width: 68%; font-size: .92rem !important; line-height: 1.55; }
.bot-row     { display: flex; align-items: flex-start; gap: 10px; margin: 10px 0; }
.bot-avatar  { width: 32px; height: 32px; background: #E8F0FE; border-radius: 50%;
               display: flex; align-items: center; justify-content: center;
               font-size: .9rem; flex-shrink: 0; margin-top: 2px; }
.bot-bubble  { background: #FFF; border: 1px solid #DDE3EE;
               border-radius: 4px 16px 16px 16px;
               padding: 10px 16px; max-width: 84%; font-size: .92rem !important;
               line-height: 1.6; color: #1C2333 !important;
               box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.bubble-lbl  { font-size: .64rem !important; font-weight: 600 !important;
               color: #9EABC0 !important; margin-bottom: 3px; letter-spacing: .4px; }
.ctx-badge   { display: inline-block; background: #EEF4FF; color: #3B7DDD !important;
               border: 1px solid #C3D4F7; border-radius: 12px; font-size: .68rem !important;
               padding: 2px 10px; margin-bottom: 6px; font-weight: 600 !important; }

/* ── Info boxes — text always visible regardless of global color overrides ── */
.insight-box {
    background: #EEF4FF; border: 1px solid #C3D4F7; border-left: 4px solid #3B7DDD;
    border-radius: 8px; padding: 12px 16px; margin-top: 10px;
    font-size: .87rem !important; color: #1A3460 !important; line-height: 1.65;
}
.insight-box, .insight-box * {
    color: #1A3460 !important;
}

.reject-box {
    background: #FFFBEA; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B;
    border-radius: 8px; padding: 12px 16px; margin-top: 8px;
    font-size: .87rem !important; color: #78350F !important; line-height: 1.6;
}
.reject-box, .reject-box * {
    color: #78350F !important;
}

.err-box {
    background: #FFF0F0; border: 1px solid #FFCDD2; border-left: 4px solid #E53935;
    border-radius: 8px; padding: 10px 14px; margin-top: 8px;
    font-size: .85rem !important; color: #7B1515 !important;
}
.err-box, .err-box * {
    color: #7B1515 !important;
}

.chart-feedback, .chart-feedback * {
    color: #374151 !important;
}

.model-badge {
    display: inline-block; background: #F0FFF4; color: #1A5C35 !important;
    border: 1px solid #9AE6B4; border-radius: 10px; font-size: .7rem !important;
    padding: 2px 10px; font-weight: 600 !important; margin-left: 6px;
}

/* ── KPI tiles — force all child text colors ── */
.kpi-tile { background: #FFF; border: 1px solid #DDE3EE; border-radius: 10px;
            padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.kpi-label { font-size: .68rem !important; font-weight: 700 !important;
             color: #5E6E8A !important; text-transform: uppercase; letter-spacing: .7px; }
.kpi-value { font-size: 1.6rem !important; font-weight: 700 !important;
             color: #1C2333 !important; margin-top: 4px; }
.kpi-sub   { font-size: .72rem !important; color: #8496B0 !important; margin-top: 2px; }

/* ── Dashboard boxes ── */
.dash-panel, .dash-panel * { color: #1C2333 !important; }
.dash-header { font-size: .7rem !important; font-weight: 700 !important;
               color: #5E6E8A !important; text-transform: uppercase; letter-spacing: .8px;
               border-bottom: 1px solid #EEF2FA; padding-bottom: 6px; margin-bottom: 10px; }

/* ── Empty state — force text visibility ── */
.empty-state .es-icon  { font-size: 2rem; margin-bottom: 10px; }
.empty-state .es-title { font-size: 1rem !important; font-weight: 600 !important;
                         color: #4A5568 !important; margin-bottom: 6px; }
.empty-state .es-hint  { font-size: .81rem !important; line-height: 1.6;
                         color: #7A8DA8 !important; }

/* ── SQL history ── */
.sql-box  { background: #0D1117; border-left: 3px solid #3B7DDD; border-radius: 4px;
            padding: 8px 11px; font-family: 'Courier New', monospace !important;
            font-size: .72rem !important; color: #79C0FF !important;
            white-space: pre-wrap; word-break: break-all; margin-top: 4px; }
.sql-meta { font-size: .65rem !important; color: #5E6E8A !important; margin-top: 4px; }

/* ── Chart feedback ── */
.chart-feedback { background: #F8FAFF; border: 1px solid #DDE3EE; border-radius: 8px;
                  padding: 10px 14px; margin-top: 8px;
                  font-size: .84rem !important; }

/* ── Dashboard panel ── */
.dash-panel { background: #FFF; border: 1px solid #DDE3EE; border-radius: 12px;
              padding: 1rem 1.2rem; margin-bottom: 1rem;
              box-shadow: 0 1px 4px rgba(0,0,0,.05); }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 50px 20px; }

/* ── Login ── */
.login-box { background: #FFF; border: 1px solid #DDE3EE; border-radius: 14px;
             padding: 2rem 2.2rem; max-width: 380px; box-shadow: 0 4px 18px rgba(0,0,0,.08); }

/* ── Buttons — ALL buttons get explicit text color ── */
.stButton > button {
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
.stButton > button[kind="primary"] {
    background: #1C2333 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover { background: #3B7DDD !important; }

/* Secondary buttons (non-primary) — light background + dark text */
.stButton > button:not([kind="primary"]) {
    background: #2E3A52 !important;
    color: #FFFFFF !important;
    border: 1px solid #4A5568 !important;
    border-radius: 8px !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: #3B7DDD !important;
    color: #FFFFFF !important;
    border-color: #3B7DDD !important;
}

/* Button text spans inside buttons */
.stButton > button p,
.stButton > button span,
.stButton > button div {
    color: #FFFFFF !important;
}

/* ── Selectbox — force visible text ── */
.stSelectbox > div > div,
.stSelectbox > div > div > div,
.stSelectbox [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div {
    color: #1C2333 !important;
    background: #FFFFFF !important;
}
/* Selectbox dropdown options */
[data-baseweb="popover"] li,
[data-baseweb="menu"] li,
[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"] [role="option"] {
    color: #1C2333 !important;
    background: #FFFFFF !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"]:hover {
    background: #EEF4FF !important;
}

/* ── Alerts ── */
.stSuccess > div { background: #F0FFF4 !important; color: #1A5C35 !important; }
.stWarning > div { background: #FFFBEB !important; color: #78350F !important; }
.stError   > div { background: #FFF0F0 !important; color: #7B1515 !important; }
.stInfo    > div { background: #EEF4FF !important; color: #1A3460 !important; }
hr { border-color: #DDE3EE !important; }
</style>
""", unsafe_allow_html=True)


#  LLM LAYER  —  runtime model switching via session state

def _active_backend() -> str:
    """Return the currently selected backend (from session state or default)."""
    return st.session_state.get("llm_backend", DEFAULT_BACKEND)


def _active_model() -> str:
    """Return the currently selected model name."""
    return st.session_state.get("llm_model", DEFAULT_MODEL)


def get_openrouter_key() -> str:
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        return os.environ.get("OPENROUTER_API_KEY", "")


# ── Ollama: list installed models ─────────────────────────────────────────────

def ollama_list_models() -> list:
    """
    Query Ollama for locally installed models.
    Returns list of model name strings, or [] on error.
    """
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def ollama_is_running() -> bool:
    """Check if Ollama server is reachable."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ── Backend call functions ────────────────────────────────────────────────────

def _call_ollama(messages: list, temperature: float, max_tokens: int) -> tuple:
    model = _active_model()
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model":   model,
                "messages": messages,
                "stream":  False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=120,
        )
        if r.status_code != 200:
            return None, f"Ollama HTTP {r.status_code}: {r.text[:200]}"
        content = r.json().get("message", {}).get("content", "").strip()
        if not content:
            return None, "Ollama returned an empty response."
        return content, None
    except requests.exceptions.ConnectionError:
        return None, (
            f"❌ Cannot connect to Ollama at {OLLAMA_HOST}.\n\n"
            "Make sure Ollama is running:\n"
            "  → Open a terminal and run: `ollama serve`\n"
            f"  → Then pull your model: `ollama pull {model}`"
        )
    except requests.exceptions.Timeout:
        return None, (
            f"⏱ Ollama timed out (120s). Model '{model}' may still be loading — try again."
        )
    except Exception as exc:
        return None, f"Ollama error: {exc}"


def _call_openrouter(messages: list, temperature: float, max_tokens: int) -> tuple:
    key = get_openrouter_key()
    if not key:
        return None, "API Key missing – add OPENROUTER_API_KEY to .streamlit/secrets.toml"
    model = _active_model()
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=45,
        )
        d = r.json()
        if "error" in d:
            return None, f"OpenRouter: {d['error'].get('message', str(d['error']))}"
        return d["choices"][0]["message"]["content"].strip(), None
    except requests.exceptions.Timeout:
        return None, "Request timed out (45s)."
    except Exception as exc:
        return None, f"Unexpected error: {exc}"


def call_llm(
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = TOKENS_DEFAULT,
) -> tuple:
    """Route to the active backend. Returns (content | None, error | None)."""
    backend = _active_backend()
    if backend == "ollama":
        return _call_ollama(messages, temperature, max_tokens)
    elif backend == "openrouter":
        return _call_openrouter(messages, temperature, max_tokens)
    return None, f"Unknown backend: '{backend}'"


def llm_status_badge() -> str:
    backend = _active_backend()
    model   = _active_model()
    icon    = "🖥️" if backend == "ollama" else "☁️"
    return (
        f'<span style="display:inline-block;background:#F0FFF4;color:#1A5C35;'
        f'border:1px solid #9AE6B4;border-radius:10px;font-size:.7rem;'
        f'padding:2px 10px;font-weight:600;margin-left:6px;">'
        f'{icon} {backend} · {model}</span>'
    )


def clean_sql(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"```sql", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw).strip()
    if ";" in raw:
        raw = raw[: raw.index(";") + 1]
    return raw.strip()


def make_safe_name(name: str, idx: int) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", str(name)).strip("_")
    if not safe or safe[0].isdigit():
        safe = f"col{idx}"
    return f"c{idx}_{safe[:20]}" if safe else f"col_{idx}"


def sanitize_df(df: pd.DataFrame) -> tuple:
    col_map, reverse_map, new_cols = {}, {}, []
    for i, col in enumerate(df.columns):
        safe = make_safe_name(str(col), i)
        col_map[col]      = safe
        reverse_map[safe] = col
        new_cols.append(safe)
    safe_df         = df.copy()
    safe_df.columns = new_cols
    return safe_df, col_map, reverse_map


def restore_columns(df: pd.DataFrame, reverse_map: dict) -> pd.DataFrame:
    result         = df.copy()
    result.columns = [reverse_map.get(c, c) for c in result.columns]
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  Date detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_date_cols(df: pd.DataFrame) -> list:
    date_cols = []
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(50)
        if sample.empty:
            continue
        try:
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() >= 0.7:
                date_cols.append(col)
                continue
        except Exception:
            pass
        try:
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() >= 0.7:
                date_cols.append(col)
        except Exception:
            pass
    return date_cols


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in detect_date_cols(df):
        try:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
        except Exception:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass
    return df


#  Schema & Semantic Layer

def get_schema(table_name: str) -> dict:
    return st.session_state.get("schemas", {}).get(table_name, {})


def build_schema_context(table_name: str, columns: list) -> str:
    schema      = get_schema(table_name)
    col_descs   = schema.get("column_descriptions", {})
    biz_metrics = schema.get("business_metrics", {})
    lines = []
    if col_descs:
        lines.append("Column descriptions:")
        for col in columns:
            if col_descs.get(col, ""):
                lines.append(f"  {col}: {col_descs[col]}")
    if biz_metrics:
        lines.append("Business metric definitions:")
        for m, d in biz_metrics.items():
            lines.append(f"  {m}: {d}")
    return "\n".join(lines) if lines else ""


#  Conversation context

def build_conversation_context(messages: list, max_turns: int = 6) -> str:
    qa = [m for m in messages if m["role"] in ("user", "assistant")]
    recent = qa[-(max_turns * 2):]
    history, i = [], 0
    while i < len(recent) - 1:
        if recent[i]["role"] == "user" and recent[i+1]["role"] == "assistant":
            q = recent[i]["content"]
            a = recent[i+1].get("content", "")
            history.append(f"  Q: {q}")
            if a:
                history.append(f"  A: {a[:120]}{'…' if len(a)>120 else ''}")
            i += 2
        else:
            i += 1
    return "\n".join(history) if history else ""


#  Best column pair helper

def _best_cat_num(df: pd.DataFrame) -> tuple:
    """Returns (best_cat_col, best_num_col) — both may be None."""
    if df.empty:
        return None, None

    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object","category","string"]).columns.tolist()

    def is_id_col(col: str) -> bool:
        try:
            s = df[col].dropna()
            if len(s) == 0 or not pd.api.types.is_integer_dtype(s):
                return False
            return s.nunique() == len(s) and int(s.min())==1 and int(s.max())==len(s)
        except Exception:
            return False

    good_num = [c for c in num_cols if not is_id_col(c)] or num_cols
    best_num = None
    if good_num:
        try:
            best_num = max(good_num,
                           key=lambda c: df[c].std(skipna=True) if df[c].std(skipna=True)>0 else 0)
        except Exception:
            best_num = good_num[0]

    def cat_score(c):
        try:
            u = df[c].nunique()
            return u if 2 <= u <= 50 else 0
        except Exception:
            return 0

    best_cat = None
    if cat_cols:
        try:
            best_cat = max(cat_cols, key=cat_score)
        except Exception:
            best_cat = cat_cols[0]

    return best_cat, best_num



def _ov_font():
    return dict(family="Arial, sans-serif", size=12, color="#1C2333")


def _build_overview_charts(df: pd.DataFrame, rev_map: dict) -> list:
    """
    Build up to 4 business-meaningful charts for the overview.
    Returns list of (label, fig) tuples — only non-None figs are included.

    Chart logic (in priority order):
      A. Top-10 ranking       — always (if cat + num)
      B. Category distribution — always (pie/donut, different cat col)
      C. Monthly trend         — if date + num
      D. Numeric distribution  — histogram of main numeric col
    """
    CLR  = px.colors.qualitative.Set2
    BASE = dict(template="plotly_white")
    FONT = _ov_font()
    out  = []

    num  = df.select_dtypes(include=["number"]).columns.tolist()
    cat  = df.select_dtypes(include=["object","category","string"]).columns.tolist()
    date = df.select_dtypes(include=["datetime"]).columns.tolist()
    best_cat, best_num = _best_cat_num(df)

    # Guard
    if best_num is not None and best_num not in df.columns:
        best_num = num[0] if num else None
    if best_cat is not None and best_cat not in df.columns:
        best_cat = cat[0] if cat else None

    def orig(col):
        return rev_map.get(col, col) if col else ""

    # ── A. Top-10 horizontal bar (ranking) ───────────────────────────────────
    if best_cat and best_num:
        try:
            grp = (df.groupby(best_cat)[best_num]
                   .sum().nlargest(10).reset_index())
            grp.columns = [best_cat, best_num]
            fig = px.bar(grp, x=best_num, y=best_cat, orientation="h",
                         title=f"🏆 Top 10 — {orig(best_cat)} by {orig(best_num)}",
                         color=best_cat, color_discrete_sequence=CLR, **BASE)
            fig.update_layout(
                font=FONT, showlegend=False,
                yaxis_title="", xaxis_title=orig(best_num),
                yaxis=dict(autorange="reversed"),
                margin=dict(t=45, b=30, l=130, r=20), height=320,
            )
            out.append(("Top 10 Ranking", fig))
        except Exception:
            pass

    # ── B. Composition pie (second cat col if available, else same) ──────────
    pie_cat = None
    # prefer a different cat col with fewer unique values (2-8) for a clean pie
    for c in cat:
        if c != best_cat and 2 <= df[c].nunique() <= 8:
            pie_cat = c
            break
    if pie_cat is None and best_cat and df[best_cat].nunique() <= 8:
        pie_cat = best_cat

    if pie_cat and best_num:
        try:
            grp = (df.groupby(pie_cat)[best_num].sum()
                   .nlargest(8).reset_index())
            grp.columns = [pie_cat, best_num]
            fig = px.pie(grp, names=pie_cat, values=best_num,
                         title=f"📊 Composition — {orig(pie_cat)}",
                         color_discrete_sequence=CLR, hole=0.4)
            fig.update_traces(textposition="outside", textinfo="percent+label",
                              pull=[0.03]*len(grp))
            fig.update_layout(
                font=FONT, showlegend=False,
                margin=dict(t=45, b=30, l=20, r=20), height=320,
            )
            out.append(("Composition", fig))
        except Exception:
            pass

    # ── C. Monthly trend (if date column exists) ─────────────────────────────
    if date and best_num:
        try:
            tmp = df[[date[0], best_num]].dropna().copy()
            tmp[date[0]] = pd.to_datetime(tmp[date[0]], errors="coerce")
            tmp = tmp.dropna(subset=[date[0]])
            tmp["_m"] = tmp[date[0]].dt.to_period("M").astype(str)
            trend = tmp.groupby("_m")[best_num].sum().reset_index()
            trend.columns = ["Month", best_num]
            if len(trend) >= 2:
                fig = px.line(trend, x="Month", y=best_num,
                              title=f"📈 Monthly Trend — {orig(best_num)}",
                              color_discrete_sequence=["#3B7DDD"], **BASE)
                fig.update_traces(mode="lines+markers",
                                  line=dict(width=2.5), marker=dict(size=6))
                fig.update_layout(
                    font=FONT, xaxis_title="", yaxis_title=orig(best_num),
                    margin=dict(t=45, b=30, l=50, r=20), height=320,
                )
                out.append(("Monthly Trend", fig))
        except Exception:
            pass

    # ── D. Numeric distribution (histogram of primary numeric) ──────────────
    if best_num:
        try:
            vals = df[best_num].dropna()
            if len(vals) > 1 and vals.std() > 0:
                fig = px.histogram(df, x=best_num,
                                   nbins=min(25, max(10, df[best_num].nunique())),
                                   title=f"🔢 Distribution — {orig(best_num)}",
                                   color_discrete_sequence=["#3B7DDD"], **BASE)
                fig.update_layout(
                    font=FONT, xaxis_title=orig(best_num), yaxis_title="Count",
                    margin=dict(t=45, b=30, l=50, r=20), height=320,
                    bargap=0.05,
                )
                out.append(("Distribution", fig))
        except Exception:
            pass

    # ── E. Fallback: numeric-only summary bar (no category) ─────────────────
    if not out and not cat and num:
        try:
            good = [c for c in num if df[c].std() > 0][:5]
            if good:
                summary = pd.DataFrame({
                    "Metric": [orig(c) for c in good],
                    "Value":  [df[c].sum() for c in good],
                })
                fig = px.bar(summary, x="Metric", y="Value",
                             title="📊 Key Metrics — Totals",
                             color="Metric", color_discrete_sequence=CLR, **BASE)
                fig.update_layout(
                    font=FONT, showlegend=False,
                    xaxis_title="", yaxis_title="Total",
                    margin=dict(t=45, b=30, l=50, r=20), height=320,
                )
                out.append(("Key Metrics", fig))
        except Exception:
            pass

    return out[:4]   # max 4 charts


def business_eda_stats(df: pd.DataFrame, rev_map: dict) -> list:
    """Return up to 4 (label, value, sub) tuples for KPI tiles."""
    if df.empty:
        return [("Total Records", "0", "no data")]

    best_cat, best_num = _best_cat_num(df)
    num = df.select_dtypes(include=["number"]).columns.tolist()

    def orig(col):
        return rev_map.get(col, col) if col else ""

    def is_id(col):
        if col is None or col not in df.columns:
            return True
        s = df[col].dropna()
        if len(s) == 0:
            return False
        return s.nunique() == len(s) and pd.api.types.is_integer_dtype(s)

    cards = [("Total Records", f"{len(df):,}", "rows in dataset")]

    if best_num is not None and best_num in df.columns and not is_id(best_num):
        try:
            total = df[best_num].sum()
            avg   = df[best_num].mean()
            fmt_t = f"{total:,.0f}" if float(total)==int(float(total)) else f"{total:,.2f}"
            cards.append((f"Total  {orig(best_num)}", fmt_t, f"avg {avg:,.2f}"))
        except Exception:
            pass

    if best_cat is not None and best_cat in df.columns:
        try:
            uniq    = df[best_cat].nunique()
            vc      = df[best_cat].value_counts()
            top_val = vc.idxmax() if not vc.empty else "—"
            top_str = str(top_val)[:18] + ("…" if len(str(top_val))>18 else "")
            cards.append((f"Unique  {orig(best_cat)}", str(uniq), f"top: {top_str}"))
        except Exception:
            pass

    other_num = [c for c in num if c != best_num and c in df.columns and not is_id(c)]
    if other_num:
        try:
            c2  = other_num[0]
            mx  = df[c2].max()
            mn  = df[c2].min()
            fmt = f"{mx:,.0f}" if float(mx)==int(float(mx)) else f"{mx:,.2f}"
            cards.append((f"Max  {orig(c2)}", fmt, f"min {mn:,.2f}"))
        except Exception:
            pass

    return cards[:4]


def business_eda_text(df: pd.DataFrame, table_name: str,
                      schema_context: str = "") -> str:
    """Ask the LLM for a 3-sentence executive summary."""
    best_cat, best_num = _best_cat_num(df)
    num  = df.select_dtypes(include=["number"]).columns.tolist()
    cat  = df.select_dtypes(include=["object","category","string"]).columns.tolist()
    date = df.select_dtypes(include=["datetime"]).columns.tolist()

    stats_lines = []
    cols_for_stats = ([best_num] + [x for x in num if x != best_num])[:4] if best_num else num[:4]
    for c in cols_for_stats:
        if c and c in df.columns:
            try:
                stats_lines.append(
                    f"  {c}: total={df[c].sum():,.0f}  avg={df[c].mean():,.2f}"
                    f"  max={df[c].max():,.2f}  min={df[c].min():,.2f}"
                )
            except Exception:
                pass

    cat_info = []
    for c in cat[:4]:
        if c in df.columns:
            try:
                top = df[c].value_counts().idxmax()
                cat_info.append(f"  {c}: {df[c].nunique()} unique, most common = '{top}'")
            except Exception:
                pass

    schema_block = f"\nBusiness context:\n{schema_context}\n" if schema_context else ""

    prompt = f"""You are a business analyst writing for a senior executive.

Dataset: {table_name}  |  {df.shape[0]:,} rows  |  {df.shape[1]} columns
Date columns: {date if date else "none"}
{schema_block}
Numeric stats:
{chr(10).join(stats_lines) if stats_lines else "  No numeric columns."}

Category info:
{chr(10).join(cat_info) if cat_info else "  No category columns."}

Write exactly 3 short sentences:
1. What this dataset is about (mention the table name and scale).
2. The single most important number from the stats above.
3. One specific business question this data can answer immediately.

Use actual numbers. No jargon. No bullet points."""

    text, _ = call_llm([{"role":"user","content":prompt}],
                       temperature=0.3, max_tokens=TOKENS_EDA_TEXT)
    return text or "Dataset loaded successfully."


# ─────────────────────────────────────────────────────────────────────────────
#  LLM Guardrail
# ─────────────────────────────────────────────────────────────────────────────

def validate_question(user_text: str, table_name: str, columns: list) -> tuple:
    prompt = f"""You are a data query validator. Decide if the user question can be answered from this table.

Table: {table_name}
Columns: {", ".join(columns)}
User question: "{user_text}"

RULES — Be LENIENT:
- Mark VALID for counts, totals, rankings, filters, comparisons, trends — even if phrasing is vague or in Arabic.
- Mark INVALID ONLY if the question is completely unrelated to this data.
- When in doubt → mark VALID.

Reply ONLY with valid JSON, nothing else:
{{"valid": true, "reason": "ok"}}
or
{{"valid": false, "reason": "one sentence"}}"""

    raw, err = call_llm([{"role":"user","content":prompt}],
                        temperature=0.0, max_tokens=TOKENS_GUARDRAIL)
    if err or not raw:
        return True, ""
    raw = raw.strip().replace("```json","").replace("```","").strip()
    try:
        obj = json.loads(raw)
        return bool(obj.get("valid", True)), str(obj.get("reason", ""))
    except Exception:
        return True, ""


# ─────────────────────────────────────────────────────────────────────────────
#  SQL generation & auto-fix
# ─────────────────────────────────────────────────────────────────────────────

def generate_sql(user_text: str, table_name: str, safe_columns: list,
                 col_map: dict, schema_context: str, conv_context: str) -> tuple:
    mapping_lines = "\n".join(f"  '{o}'  →  {s}" for o, s in col_map.items())
    schema_block  = f"\nSchema / semantic definitions:\n{schema_context}\n" if schema_context else ""
    conv_block    = f"\nConversation context:\n{conv_context}\n" if conv_context else ""

    prompt = f"""You are a precise SQL generator for pandasql (SQLite dialect).

TABLE NAME : {table_name}   ← use EXACTLY this name
SAFE COLUMN NAMES (use these in SQL):
{", ".join(safe_columns)}

Original → safe column mapping (for understanding the user's question):
{mapping_lines}
{schema_block}{conv_block}
OUTPUT RULES:
- Return ONLY the raw SQL query ending with a semicolon.
- Use ONLY the safe column names listed above, exactly as spelled.
- No markdown, no backticks, no explanation.
- Aggregations → GROUP BY all non-aggregated columns.
- For text/category columns: use LIKE '%value%' for partial matching.
- ORDER BY + LIMIT for "top N" questions.

USER REQUEST: {user_text}"""

    raw, err = call_llm([{"role":"user","content":prompt}],
                        temperature=0.0, max_tokens=TOKENS_SQL)
    if err:
        return None, err
    return clean_sql(raw), None


def fix_sql(broken_sql: str, error: str, table_name: str,
            safe_columns: list) -> tuple:
    prompt = f"""Fix this pandasql (SQLite) query. Return ONLY the corrected SQL ending with a semicolon.

TABLE  : {table_name}
COLUMNS (safe names): {", ".join(safe_columns)}
BROKEN : {broken_sql}
ERROR  : {error}

Common fixes:
- Use safe column names from the list — never Arabic or special-char names
- COUNT(DISTINCT col) not COUNT DISTINCT col
- GROUP BY must include all non-aggregated SELECT columns"""

    raw, err = call_llm([{"role":"user","content":prompt}],
                        temperature=0.0, max_tokens=TOKENS_SQL)
    if err:
        return None, err
    return clean_sql(raw), None


# ─────────────────────────────────────────────────────────────────────────────
#  Chart type selection & building
# ─────────────────────────────────────────────────────────────────────────────

CHART_MENU = {
    "bar":       "Bar chart – compare categories",
    "bar_h":     "Horizontal bar – ranking / many categories",
    "line":      "Line chart – trend over time",
    "pie":       "Pie chart – share / composition",
    "scatter":   "Scatter – correlation between two numeric values",
    "histogram": "Histogram – distribution of one numeric column",
}


def pick_chart_type(user_question: str, df: pd.DataFrame) -> str:
    num  = df.select_dtypes(include="number").columns.tolist()
    cat  = df.select_dtypes(include=["object","category"]).columns.tolist()
    date = df.select_dtypes(include="datetime").columns.tolist()
    n    = len(df)

    all_keys = list(CHART_MENU.keys()) + ["kpi_cards", "none"]
    options  = "\n".join(f"  {k}: {v}" for k, v in CHART_MENU.items())
    options += "\n  kpi_cards: Large number tiles – 1 row of key figures"
    options += "\n  none: No chart – table is sufficient"

    prompt = f"""You are a BI expert picking the best chart for a business result.

User question: "{user_question}"
Result: {n} rows × {len(df.columns)} cols
Numeric: {num}  Category: {cat}  Date: {date}
Sample: {df.head(3).to_dict(orient="records")}

Rules: 1 row + numbers→kpi_cards | date+num→line | cat+num many→bar_h | cat+num few→pie/bar | 2 nums→scatter | 1 num→histogram

Available: {', '.join(all_keys)}
Return ONLY the key."""

    raw, _ = call_llm([{"role":"user","content":prompt}],
                      temperature=0.0, max_tokens=TOKENS_CHART)
    if raw:
        key = raw.strip().lower().strip("\"'")
        if key in all_keys:
            return key

    # Heuristic
    if n == 1 and num:             return "kpi_cards"
    if date and num:               return "line"
    if cat and num:
        best_cat, _ = _best_cat_num(df)
        uniq = df[best_cat].nunique() if best_cat else n
        return "pie" if uniq <= 6 else ("bar" if n <= 8 else "bar_h")
    if len(num) >= 2:              return "scatter"
    if len(num) == 1:              return "histogram"
    return "none"


def build_chart(chart_type: str, df: pd.DataFrame, title: str = ""):
    if chart_type in ("kpi_cards", "none"):
        return None

    CLR  = px.colors.qualitative.Set2
    BASE = dict(template="plotly_white", title=title)
    FONT = _ov_font()

    num      = df.select_dtypes(include="number").columns.tolist()
    cat      = df.select_dtypes(include=["object","category"]).columns.tolist()
    date     = df.select_dtypes(include="datetime").columns.tolist()
    best_cat, best_num = _best_cat_num(df)

    if best_num is not None and best_num not in df.columns:
        best_num = num[0] if num else None
    if best_cat is not None and best_cat not in df.columns:
        best_cat = cat[0] if cat else None

    if chart_type == "line":
        y_col = best_num or (num[0] if num else None)
        x_col = date[0] if date else (cat[0] if cat else None)
        if y_col:
            plot = df[[x_col, y_col]].dropna().sort_values(x_col) if x_col else df[[y_col]].dropna().reset_index()
            x    = x_col or "index"
            fig  = px.line(plot, x=x, y=y_col, color_discrete_sequence=["#3B7DDD"], **BASE)
            fig.update_traces(mode="lines+markers")
            fig.update_layout(font=FONT, xaxis_title="", yaxis_title=y_col)
            return fig

    if chart_type == "bar":
        x_col = best_cat or (cat[0] if cat else None)
        y_col = best_num or (num[0] if num else None)
        if x_col and y_col:
            plot = df[[x_col, y_col]].dropna().sort_values(y_col, ascending=False).head(15)
            fig  = px.bar(plot, x=x_col, y=y_col, color=x_col, color_discrete_sequence=CLR, **BASE)
            fig.update_layout(font=FONT, showlegend=False, xaxis_title="", yaxis_title=y_col)
            return fig
        if y_col:
            fig = px.bar(df[[y_col]].dropna().reset_index(), x="index", y=y_col, color_discrete_sequence=CLR, **BASE)
            fig.update_layout(font=FONT)
            return fig

    if chart_type == "bar_h":
        x_col = best_num or (num[0] if num else None)
        y_col = best_cat or (cat[0] if cat else None)
        if x_col and y_col:
            plot = df[[y_col, x_col]].dropna().sort_values(x_col, ascending=True).tail(20)
            fig  = px.bar(plot, x=x_col, y=y_col, orientation="h",
                          color_discrete_sequence=["#3B7DDD"], **BASE)
            fig.update_layout(font=FONT, yaxis_title="", xaxis_title=x_col,
                              yaxis=dict(autorange="reversed"))
            return fig
        return build_chart("bar", df, title)

    if chart_type == "pie":
        names  = best_cat or (cat[0] if cat else None)
        values = best_num or (num[0] if num else None)
        if names and values:
            plot = df[[names, values]].dropna().groupby(names)[values].sum().nlargest(8).reset_index()
            fig  = px.pie(plot, names=names, values=values,
                          color_discrete_sequence=CLR, title=title, hole=0.4)
            fig.update_traces(textposition="outside", textinfo="percent+label")
            fig.update_layout(font=FONT, showlegend=False,
                              margin=dict(t=50, b=50, l=20, r=20))
            return fig
        return build_chart("bar_h", df, title)

    if chart_type == "scatter":
        good_num = [c for c in num if c in df.columns and df[c].std() > 0]
        if len(good_num) >= 2:
            try:
                fig = px.scatter(df, x=good_num[0], y=good_num[1], color=best_cat,
                                 color_discrete_sequence=CLR,
                                 trendline="ols" if len(df) >= 10 else None, **BASE)
            except Exception:
                fig = px.scatter(df, x=good_num[0], y=good_num[1], color=best_cat,
                                 color_discrete_sequence=CLR, **BASE)
            fig.update_layout(font=FONT)
            return fig
        return build_chart("bar", df, title)

    if chart_type == "histogram":
        y_col = best_num or (num[0] if num else None)
        if y_col:
            fig = px.histogram(df, x=y_col, nbins=min(30, len(df)),
                               color_discrete_sequence=["#3B7DDD"], **BASE)
            fig.update_layout(font=FONT, xaxis_title=y_col, yaxis_title="Count")
            return fig

    return None


def render_kpi_cards(df: pd.DataFrame):
    num      = df.select_dtypes(include="number").columns.tolist()
    good_num = [c for c in num if df[c].nunique() > 1 or len(df) == 1]
    if df.empty or not good_num:
        return
    row  = df.iloc[0]
    cols = st.columns(min(len(good_num), 4))
    for i, col_name in enumerate(good_num[:4]):
        val = row[col_name]
        fmt = f"{val:,.2f}" if isinstance(val, float) else f"{val:,}"
        with cols[i]:
            st.markdown(
                f'<div class="kpi-tile">'
                f'<div class="kpi-label">{col_name}</div>'
                f'<div class="kpi-value">{fmt}</div>'
                f'</div>', unsafe_allow_html=True,
            )


#  Business insights

def generate_insights(df_result: pd.DataFrame, question: str,
                      conv_context: str = "") -> tuple:
    if df_result.empty:
        return "No rows were returned by this query.", None
    try:
        stats = df_result.describe(include="all").to_string()
    except Exception:
        stats = "Stats unavailable."
    conv_block = f"\nConversation context:\n{conv_context}\n" if conv_context else ""

    prompt = f"""You are a business analyst writing for a senior executive.

User asked: "{question}"{conv_block}

Query result stats:
{stats}

Sample rows (up to 20):
{df_result.head(20).to_dict(orient="records")}

Write exactly 3 short sentences:
1. Direct answer with actual numbers from the data.
2. The most important pattern or anomaly.
3. One concrete business action.

No bullet points. No jargon. Be direct.
Respond in the same language the user used."""

    content, err = call_llm([{"role":"user","content":prompt}],
                            temperature=0.3, max_tokens=TOKENS_INSIGHTS)
    return content or "Query completed.", err


#  DB Connectivity

DB_DRIVERS = {
    "PostgreSQL":  "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
    "MySQL":       "mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
    "SQL Server":  "mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server",
    "SQLite File": "sqlite:///{database}",
    "Teradata":    "teradatasql://{host}/?user={user}&password={password}&database={database}",
}


def build_connection_string(db_type: str, params: dict) -> str:
    return DB_DRIVERS.get(db_type, "").format(**params)


def test_db_connection(conn_str: str) -> tuple:
    if not _HAS_SQLALCHEMY:
        return False, "sqlalchemy not installed. Run: pip install sqlalchemy"
    try:
        engine = sqlalchemy.create_engine(conn_str, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return True, "Connection successful ✓"
    except Exception as exc:
        return False, str(exc)


def load_table_from_db(conn_str: str, table_or_query: str) -> tuple:
    if not _HAS_SQLALCHEMY:
        return None, "sqlalchemy not installed."
    try:
        engine = sqlalchemy.create_engine(conn_str)
        q = table_or_query.strip()
        if " " not in q and not q.upper().startswith("SELECT"):
            q = f"SELECT * FROM {q} LIMIT 100000"
        return pd.read_sql(q, engine), None
    except Exception as exc:
        return None, str(exc)


def list_db_tables(conn_str: str) -> tuple:
    if not _HAS_SQLALCHEMY:
        return [], "sqlalchemy not installed."
    try:
        engine    = sqlalchemy.create_engine(conn_str)
        inspector = sqlalchemy.inspect(engine)
        return inspector.get_table_names(), None
    except Exception as exc:
        return [], str(exc)


#  Utilities

def load_df(selected: str) -> pd.DataFrame:
    if st.session_state.get("uploaded_df") is not None:
        return st.session_state["uploaded_df"]
    path = f"data/{selected}"
    if os.path.exists(path):
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="cp1256")
    st.error(f"File not found: {path}")
    return pd.DataFrame()


def safe_tbl(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(raw).replace(".csv", ""))


#  Sidebar  —  navigation + model switcher + SQL history
with st.sidebar:
    st.markdown("## 🗄️ Chat with DB")
    st.markdown("---")

    # ── Model Switcher ────────────────────────────────────────────────────────
    st.markdown('<span class="sec-label">🤖 Model Settings</span>',
                unsafe_allow_html=True)

    # Session state init
    st.session_state.setdefault("llm_backend", DEFAULT_BACKEND)
    st.session_state.setdefault("llm_model",   DEFAULT_MODEL)

    # Backend selector
    backend_choice = st.radio(
        "Backend",
        ["ollama", "openrouter"],
        index=0 if st.session_state["llm_backend"] == "ollama" else 1,
        horizontal=True,
        key="backend_radio",
    )
    if backend_choice != st.session_state["llm_backend"]:
        st.session_state["llm_backend"] = backend_choice
        # Reset model to first option for the new backend
        if backend_choice == "ollama":
            st.session_state["llm_model"] = list(OLLAMA_MODELS.keys())[0]
        else:
            st.session_state["llm_model"] = list(OPENROUTER_MODELS.keys())[0]
        st.rerun()

    # ── Ollama panel ──────────────────────────────────────────────────────────
    if st.session_state["llm_backend"] == "ollama":

        # Check server status
        running = ollama_is_running()
        if running:
            st.markdown(
                '<span style="color:#38A169;font-size:.78rem;">● Ollama running</span>',
                unsafe_allow_html=True,
            )
            # Detect installed models
            installed = ollama_list_models()
            # Build options: installed models first, then remaining from OLLAMA_MODELS
            installed_keys = [m.split(":")[0] for m in installed]  # strip tags like :latest
            available_opts  = {}
            for m in installed:
                base = m.split(":")[0]
                label = OLLAMA_MODELS.get(base, OLLAMA_MODELS.get(m, m))
                available_opts[m] = f"✅ {label}"
            # Add not-installed models with pull hint
            for key, label in OLLAMA_MODELS.items():
                if key not in available_opts and key.split(":")[0] not in installed_keys:
                    available_opts[key] = f"⬇️ {label} (not installed)"

            model_keys   = list(available_opts.keys())
            model_labels = list(available_opts.values())

            # Find current index
            cur = st.session_state["llm_model"]
            cur_idx = model_keys.index(cur) if cur in model_keys else 0

            sel_idx = st.selectbox(
                "Select model",
                range(len(model_keys)),
                index=cur_idx,
                format_func=lambda i: model_labels[i],
                key="model_sel_ollama",
            )
            selected_key = model_keys[sel_idx]

            if selected_key != st.session_state["llm_model"]:
                st.session_state["llm_model"] = selected_key

            # Show pull command if not installed
            if "⬇️" in model_labels[sel_idx]:
                st.markdown(
                    f'<div style="background:#FFFBEA;border:1px solid #FDE68A;'
                    f'border-radius:6px;padding:6px 10px;font-size:.73rem;'
                    f'color:#78350F;margin-top:4px;">'
                    f'Run in terminal:<br>'
                    f'<code style="background:transparent;">ollama pull {selected_key}</code>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Custom model input
            with st.expander("Enter custom model name", expanded=False):
                custom = st.text_input(
                    "Custom model",
                    value="",
                    placeholder="e.g. qwen2.5:14b",
                    key="custom_model_input",
                    label_visibility="collapsed",
                )
                if custom.strip():
                    if st.button("Use this model", key="use_custom",
                                 use_container_width=True):
                        st.session_state["llm_model"] = custom.strip()
                        st.rerun()

        else:
            st.markdown(
                '<span style="color:#E53935;font-size:.78rem;">● Ollama not running</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="background:#FFF0F0;border:1px solid #FFCDD2;'
                'border-radius:6px;padding:8px 10px;font-size:.73rem;'
                'color:#7B1515;margin-top:4px;">'
                '1. Install Ollama → <b>ollama.com</b><br>'
                '2. Run: <code>ollama serve</code><br>'
                '3. Pull a model: <code>ollama pull mistral</code>'
                '</div>',
                unsafe_allow_html=True,
            )
            # Still allow manual model entry
            custom = st.text_input(
                "Model name (for when server starts)",
                value=st.session_state["llm_model"],
                key="offline_model_input",
            )
            if custom.strip() != st.session_state["llm_model"]:
                st.session_state["llm_model"] = custom.strip()

    # ── OpenRouter panel ──────────────────────────────────────────────────────
    else:
        or_keys   = list(OPENROUTER_MODELS.keys())
        or_labels = list(OPENROUTER_MODELS.values())
        cur       = st.session_state["llm_model"]
        cur_idx   = or_keys.index(cur) if cur in or_keys else 0

        sel_idx = st.selectbox(
            "Select model",
            range(len(or_keys)),
            index=cur_idx,
            format_func=lambda i: or_labels[i],
            key="model_sel_or",
        )
        if or_keys[sel_idx] != st.session_state["llm_model"]:
            st.session_state["llm_model"] = or_keys[sel_idx]

        key_set = bool(get_openrouter_key())
        if key_set:
            st.markdown(
                '<span style="color:#38A169;font-size:.78rem;">● API key configured</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span style="color:#E53935;font-size:.78rem;">● No API key found</span>',
                unsafe_allow_html=True,
            )
            st.caption("Add OPENROUTER_API_KEY to .streamlit/secrets.toml")

    # Current active model summary
    st.markdown(
        f'<div style="background:#253047;border-radius:7px;padding:6px 10px;'
        f'margin-top:8px;font-size:.73rem;color:#CDD5DF;">'
        f'Active: <b style="color:#7DD3FC;">{_active_model()}</b> '
        f'via <b style="color:#7DD3FC;">{_active_backend()}</b>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Navigation ────────────────────────────────────────────────────────────
    st.markdown('<span class="sec-label">Navigation</span>', unsafe_allow_html=True)
    pages = ["Login", "Select Table", "Chat & Visuals",
             "🔌 DB Connect", "📊 My Dashboard"]
    st.session_state.setdefault("current_page", "Login")
    page = st.radio("", pages, index=pages.index(st.session_state["current_page"]))
    st.session_state["current_page"] = page

    st.markdown("---")

    # ── SQL History ───────────────────────────────────────────────────────────
    st.markdown('<span class="sec-label">SQL History</span>', unsafe_allow_html=True)
    st.session_state.setdefault("sql_history", [])

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


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: Login
# ─────────────────────────────────────────────────────────────────────────────
if page == "Login":
    st.markdown('<div class="page-title">Welcome</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Enter your name to start using Chat with Database</div>',
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
        st.markdown("</div>", unsafe_allow_html=True)
    if "username" in st.session_state:
        st.info(f"Logged in as **{st.session_state['username']}**")


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: Select Table
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Select Table":
    if "username" not in st.session_state:
        st.warning("Please log in first.")
        st.stop()

    st.markdown('<div class="page-title">Select Data Source</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Choose a local CSV or upload your own</div>',
                unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="card"><div class="card-title">Local Files</div>',
                    unsafe_allow_html=True)
        files = ([f for f in os.listdir("data") if f.endswith(".csv")]
                 if os.path.exists("data") else [])
        if files:
            chosen = st.selectbox("Choose from data/:", files)
            if st.button("Load File", use_container_width=True, type="primary"):
                st.session_state.update(selected_table=chosen, uploaded_df=None,
                                        messages=[], sql_history=[],
                                        current_page="Chat & Visuals")
                st.rerun()
        else:
            st.info("No CSV files found in the data/ folder.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="card"><div class="card-title">Upload File</div>',
                    unsafe_allow_html=True)
        up = st.file_uploader("Upload a CSV:", type="csv")
        if up:
            try:
                try:
                    preview = pd.read_csv(up, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    up.seek(0)
                    preview = pd.read_csv(up, encoding="cp1256")
                st.success(f"{up.name} — {preview.shape[0]:,} rows × {preview.shape[1]} cols")
                st.dataframe(preview.head(5), use_container_width=True)
                if st.button("Use This File", use_container_width=True, type="primary"):
                    st.session_state.update(
                        selected_table=up.name.replace(".csv", ""),
                        uploaded_df=preview, messages=[], sql_history=[],
                        current_page="Chat & Visuals",
                    )
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not read file: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: DB Connect
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔌 DB Connect":
    if "username" not in st.session_state:
        st.warning("Please log in first.")
        st.stop()

    st.markdown('<div class="page-title">🔌 Direct Database Connection</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Connect to a live database and query it directly</div>',
                unsafe_allow_html=True)

    if not _HAS_SQLALCHEMY:
        st.warning("sqlalchemy is not installed. Run: `pip install sqlalchemy`")

    col_form, col_help = st.columns([2, 1])
    with col_form:
        st.markdown('<div class="card"><div class="card-title">Connection Settings</div>',
                    unsafe_allow_html=True)
        db_type = st.selectbox("Database Type", list(DB_DRIVERS.keys()))
        st.session_state["db_type"] = db_type

        if db_type == "SQLite File":
            db_path = st.text_input("SQLite File Path", placeholder="/path/to/database.db")
            conn_params = {"database": db_path}
        else:
            c1, c2 = st.columns(2)
            with c1:
                host = st.text_input("Host", placeholder="localhost")
                user = st.text_input("Username")
                db   = st.text_input("Database Name")
            with c2:
                port_defaults = {"PostgreSQL":"5432","MySQL":"3306",
                                 "SQL Server":"1433","Teradata":"1025"}
                port = st.text_input("Port", value=port_defaults.get(db_type,"5432"))
                pwd  = st.text_input("Password", type="password")
            conn_params = {"host":host,"port":port,"user":user,"password":pwd,"database":db}

        if st.button("🔗 Test Connection", type="primary", use_container_width=True):
            conn_str = build_connection_string(db_type, conn_params)
            with st.spinner("Testing connection…"):
                ok, msg = test_db_connection(conn_str)
            if ok:
                st.success(msg)
                st.session_state["db_conn_str"] = conn_str
                tables, err = list_db_tables(conn_str)
                if tables:
                    st.session_state["db_tables"] = tables
                    st.success(f"Found {len(tables)} table(s).")
            else:
                st.error(f"Connection failed: {msg}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_help:
        st.markdown('<div class="card"><div class="card-title">How to Use</div>',
                    unsafe_allow_html=True)
        st.markdown("""
1. Choose your database type
2. Enter connection details
3. Click **Test Connection**
4. Select a table → loads into **Chat & Visuals**
5. Ask questions in natural language
""")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("db_conn_str") and st.session_state.get("db_tables"):
        st.markdown("---")
        st.markdown("### Load a Table")
        chosen_tbl = st.selectbox("Select table to load:", st.session_state["db_tables"])
        if st.button("📥 Load Table", type="primary"):
            with st.spinner(f"Loading {chosen_tbl}…"):
                df, err = load_table_from_db(st.session_state["db_conn_str"], chosen_tbl)
            if err:
                st.error(f"Error: {err}")
            else:
                st.success(f"Loaded {df.shape[0]:,} rows × {df.shape[1]} cols")
                st.session_state.update(
                    selected_table=chosen_tbl, uploaded_df=df,
                    messages=[], sql_history=[], current_page="Chat & Visuals",
                    db_active_conn=st.session_state["db_conn_str"],
                    db_active_table=chosen_tbl,
                )
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: Chat & Visuals
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Chat & Visuals":
    if "selected_table" not in st.session_state:
        st.warning("Please select a table first.")
        st.stop()

    raw_df     = load_df(st.session_state["selected_table"])
    table_name = safe_tbl(st.session_state["selected_table"])
    if raw_df.empty:
        st.stop()

    # Sanitize
    san_key = f"san_{table_name}"
    if san_key not in st.session_state:
        st.session_state[san_key] = sanitize_df(raw_df)
    safe_df, col_map, rev_map = st.session_state[san_key]

    # Prepare datetime
    prep_key = f"prep_{table_name}"
    if prep_key not in st.session_state:
        st.session_state[prep_key] = prepare_df(safe_df)
    df = st.session_state[prep_key]

    st.session_state.setdefault("messages",  [])
    st.session_state.setdefault("dashboard", [])
    st.session_state.setdefault("schemas",   {})

    # Header
    st.markdown(
        f'<div class="page-title">Chat with {table_name} '
        f'{llm_status_badge()}</div>',
        unsafe_allow_html=True,
    )
    col_preview = ", ".join(raw_df.columns[:8].tolist())
    if len(raw_df.columns) > 8:
        col_preview += "…"
    st.markdown(
        f'<div class="page-sub">{raw_df.shape[0]:,} rows · {raw_df.shape[1]} columns'
        f' · Columns: {col_preview}</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  BUSINESS OVERVIEW  — Multi-visual section
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("📊 Business Overview", expanded=True):

        # ── KPI stat tiles ────────────────────────────────────────────────────
        stat_cards = business_eda_stats(df, rev_map)
        if stat_cards:
            kpi_cols = st.columns(len(stat_cards))
            for i, (label, value, sub) in enumerate(stat_cards):
                with kpi_cols[i]:
                    st.markdown(
                        f'<div class="kpi-tile">'
                        f'<div class="kpi-label">{label}</div>'
                        f'<div class="kpi-value">{value}</div>'
                        f'<div class="kpi-sub">{sub}</div>'
                        f'</div>', unsafe_allow_html=True,
                    )

        st.markdown("---")

        # ── Multi-visual charts (2×2 grid, up to 4 charts) ───────────────────
        ov_key = f"ov_charts_{table_name}"
        if ov_key not in st.session_state:
            st.session_state[ov_key] = _build_overview_charts(df, rev_map)
        ov_charts = st.session_state[ov_key]

        if ov_charts:
            # Row 1: first 2 charts
            if len(ov_charts) >= 2:
                r1c1, r1c2 = st.columns(2)
                with r1c1:
                    st.plotly_chart(ov_charts[0][1], use_container_width=True)
                with r1c2:
                    st.plotly_chart(ov_charts[1][1], use_container_width=True)

                # Row 2: remaining charts
                remaining = ov_charts[2:]
                if remaining:
                    if len(remaining) == 1:
                        # Single chart spans full width
                        st.plotly_chart(remaining[0][1], use_container_width=True)
                    else:
                        r2c1, r2c2 = st.columns(2)
                        with r2c1:
                            st.plotly_chart(remaining[0][1], use_container_width=True)
                        with r2c2:
                            st.plotly_chart(remaining[1][1], use_container_width=True)
            else:
                # Only 1 chart — show full width
                st.plotly_chart(ov_charts[0][1], use_container_width=True)
        else:
            st.info("Not enough data to generate business charts automatically.")

        st.markdown("---")

        # ── AI executive summary ──────────────────────────────────────────────
        eda_text_key = f"biz_eda_text_{table_name}"
        if eda_text_key not in st.session_state:
            schema_ctx = build_schema_context(table_name, raw_df.columns.tolist())
            with st.spinner("Generating business overview…"):
                st.session_state[eda_text_key] = business_eda_text(
                    df, table_name, schema_ctx
                )
        st.markdown(
            f'<div class="insight-box">📌 {st.session_state[eda_text_key]}</div>',
            unsafe_allow_html=True,
        )

    # ── Schema & Semantic Layer ───────────────────────────────────────────────
    with st.expander("🧩 Schema & Semantic Layer  (optional — improves accuracy)",
                     expanded=False):
        st.markdown("Add descriptions to help the AI understand your columns and business terms.")
        schema = st.session_state["schemas"].setdefault(table_name, {
            "column_descriptions": {}, "business_metrics": {},
        })

        st.markdown("**Column Descriptions**")
        for col in raw_df.columns.tolist():
            existing = schema["column_descriptions"].get(col, "")
            new_val  = st.text_input(
                f"  {col}", value=existing,
                placeholder="e.g. Branch location name",
                key=f"cdesc_{table_name}_{col}",
                label_visibility="visible",
            )
            schema["column_descriptions"][col] = new_val

        st.markdown("---")
        st.markdown("**Business Metric Definitions**")
        st.caption("Define terms like 'revenue', 'churn' so the AI understands them.")

        bm = schema.get("business_metrics", {})
        metric_names  = list(bm.keys()) + [""]
        metric_values = list(bm.values()) + [""]
        new_bm = {}
        for j in range(len(metric_names)):
            c1, c2 = st.columns([1, 2])
            with c1:
                mname = st.text_input(f"Metric name {j+1}", value=metric_names[j],
                                      key=f"bm_name_{table_name}_{j}",
                                      placeholder="e.g. revenue",
                                      label_visibility="collapsed")
            with c2:
                mdef = st.text_input(f"Metric definition {j+1}", value=metric_values[j],
                                     key=f"bm_def_{table_name}_{j}",
                                     placeholder="e.g. SUM of price × quantity",
                                     label_visibility="collapsed")
            if mname.strip():
                new_bm[mname.strip()] = mdef.strip()
        schema["business_metrics"] = new_bm

        if st.button("💾 Save Schema", key=f"save_schema_{table_name}"):
            st.session_state["schemas"][table_name] = schema
            st.session_state.pop(f"biz_eda_text_{table_name}", None)
            st.toast("Schema saved ✓", icon="✅")

    st.markdown("---")

    # ── Empty chat state ──────────────────────────────────────────────────────
    if not st.session_state["messages"]:
        st.markdown(
            f"""<div class="empty-state">
                <div class="es-icon">💬</div>
                <div class="es-title">Ask anything about {table_name}</div>
                <div class="es-hint">
                    "كم عدد الموديلات المتوفرة لكل فرع؟"<br>
                    "Show top 10 products by price"<br>
                    "ما هو أعلى سعر في كل فرع؟"
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Chat history ──────────────────────────────────────────────────────────
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

        ctx_badge = '<span class="ctx-badge">↩ follow-up</span><br>' if msg.get("used_context") else ""
        st.markdown(
            f'<div class="bot-row"><div class="bot-avatar">🤖</div>'
            f'<div><div class="bubble-lbl">Assistant</div>'
            f'{ctx_badge}'
            f'<div class="bot-bubble">{msg["content"]}</div></div></div>',
            unsafe_allow_html=True,
        )

        if msg.get("rejected"):
            st.markdown(
                f'<div class="reject-box">⚠️ <strong>Cannot answer from this dataset.</strong>'
                f'<br>{msg["rejected"]}</div>',
                unsafe_allow_html=True,
            )
        if msg.get("error"):
            st.markdown(f'<div class="err-box">⛔ {msg["error"]}</div>',
                        unsafe_allow_html=True)

        if msg.get("chart_type") == "kpi_cards" and msg.get("dataframe") is not None:
            render_kpi_cards(msg["dataframe"])
        elif msg.get("dataframe") is not None:
            st.dataframe(msg["dataframe"], use_container_width=True)

        msg_id = msg.get("id", id(msg))
        if msg.get("chart") is not None:
            st.plotly_chart(msg["chart"], use_container_width=True, key=f"ch_{msg_id}")

        if msg.get("insight"):
            st.markdown(f'<div class="insight-box">💡 {msg["insight"]}</div>',
                        unsafe_allow_html=True)

        if msg.get("chart") is not None and not msg.get("rejected"):
            st.markdown(
                '<div class="chart-feedback">📊 <strong>Change chart or save to dashboard:</strong></div>',
                unsafe_allow_html=True,
            )
            fc1, fc2, fc3, fc4, fc5 = st.columns([1.6, 0.9, 0.9, 0.9, 1.6])
            with fc1:
                if st.button("✅ Add to Dashboard", key=f"add_{msg_id}", use_container_width=True):
                    st.session_state["dashboard"].append({
                        "title": msg["content"], "chart": msg["chart"],
                        "insight": msg.get("insight", ""),
                    })
                    st.toast("Added to dashboard ✓", icon="✅")
            with fc2:
                if st.button("📊 Bar", key=f"bar_{msg_id}", use_container_width=True):
                    df_r = msg.get("_df_for_regen")
                    if df_r is not None:
                        nf = build_chart("bar", df_r, msg["content"])
                        if nf:
                            msg["chart"] = nf; msg["chart_type"] = "bar"; st.rerun()
            with fc3:
                if st.button("📉 H-Bar", key=f"barh_{msg_id}", use_container_width=True):
                    df_r = msg.get("_df_for_regen")
                    if df_r is not None:
                        nf = build_chart("bar_h", df_r, msg["content"])
                        if nf:
                            msg["chart"] = nf; msg["chart_type"] = "bar_h"; st.rerun()
            with fc4:
                if st.button("📈 Line", key=f"line_{msg_id}", use_container_width=True):
                    df_r = msg.get("_df_for_regen")
                    if df_r is not None:
                        nf = build_chart("line", df_r, msg["content"])
                        if nf:
                            msg["chart"] = nf; msg["chart_type"] = "line"; st.rerun()
            with fc5:
                other_opts = [""] + [k for k in CHART_MENU if k not in ("bar","bar_h","line")]
                choice = st.selectbox("Other type", other_opts,
                                      key=f"other_sel_{msg_id}",
                                      label_visibility="collapsed")
                if choice:
                    if st.button("Apply", key=f"other_apply_{msg_id}", use_container_width=True):
                        df_r = msg.get("_df_for_regen")
                        if df_r is not None:
                            nf = build_chart(choice, df_r, msg["content"])
                            if nf:
                                msg["chart"] = nf; msg["chart_type"] = choice; st.rerun()

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input(f"Ask about {table_name}…")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})

        conv_ctx     = build_conversation_context(st.session_state["messages"][:-1])
        schema_ctx   = build_schema_context(table_name, raw_df.columns.tolist())
        used_context = bool(conv_ctx)

        # Step 1: Guardrail
        with st.spinner("Checking your question…"):
            is_valid, reject_reason = validate_question(
                user_input, table_name, raw_df.columns.tolist()
            )
        if not is_valid:
            st.session_state["messages"].append({
                "role":"assistant", "content":"I can't answer that from this dataset.",
                "rejected": reject_reason,
            })
            st.rerun()

        # Step 2: Generate SQL
        with st.spinner("Generating SQL…"):
            sql, sql_err = generate_sql(
                user_input, table_name,
                safe_df.columns.tolist(), col_map,
                schema_ctx, conv_ctx,
            )
        if sql_err or not sql:
            st.session_state["messages"].append({
                "role":"assistant", "content":"Could not generate SQL.",
                "error": sql_err or "Empty response from model.",
            })
            st.rerun()

        # Step 3: Execute
        t0 = time.time()
        local_env = {table_name: safe_df}
        result_df = None; used_sql = sql; fixed = False; run_error = None
        try:
            result_df = ps.sqldf(sql, local_env)
        except Exception as e1:
            with st.spinner("Auto-fixing SQL…"):
                fixed_sql, fix_err = fix_sql(sql, str(e1), table_name,
                                             safe_df.columns.tolist())
            if fixed_sql and not fix_err:
                try:
                    result_df = ps.sqldf(fixed_sql, local_env)
                    used_sql = fixed_sql; fixed = True
                except Exception as e2:
                    run_error = f"Original: {e1} | After fix: {e2}"
            else:
                run_error = str(e1) + (f" | Fix: {fix_err}" if fix_err else "")

        exec_time = time.time() - t0
        st.session_state["sql_history"].append({
            "question":user_input, "sql":used_sql,
            "exec_time":exec_time,
            "rows":len(result_df) if result_df is not None else 0,
            "fixed":fixed,
        })

        if run_error or result_df is None:
            st.session_state["messages"].append({
                "role":"assistant", "content":"The query could not be executed.",
                "error": run_error or "Unknown execution error.",
            })
            st.rerun()

        result_df_display = restore_columns(result_df, rev_map)
        result_df_prep    = prepare_df(result_df)

        # Step 4: Chart
        with st.spinner("Choosing best visualization…"):
            chart_type = pick_chart_type(user_input, result_df_prep)
        fig = build_chart(chart_type, result_df_prep, title=user_input[:60])

        if fig is not None:
            try:
                fig.for_each_trace(lambda t: t.update(name=rev_map.get(t.name, t.name)))
                fig.update_layout(
                    xaxis_title=rev_map.get(fig.layout.xaxis.title.text or "",
                                            fig.layout.xaxis.title.text or ""),
                    yaxis_title=rev_map.get(fig.layout.yaxis.title.text or "",
                                            fig.layout.yaxis.title.text or ""),
                )
            except Exception:
                pass

        # Step 5: Insights
        with st.spinner("Generating business insight…"):
            insight, ins_err = generate_insights(result_df_display, user_input, conv_ctx)

        note = " *(auto-corrected)*" if fixed else ""
        st.session_state["messages"].append({
            "role":         "assistant",
            "content":      f"**{len(result_df_display):,} rows** in {exec_time:.2f}s{note}",
            "dataframe":    result_df_display.head(500) if not result_df_display.empty else None,
            "chart":        fig,
            "chart_type":   chart_type,
            "_df_for_regen":result_df_prep,
            "insight":      insight,
            "error":        ins_err,
            "id":           len(st.session_state["messages"]),
            "used_context": used_context,
        })
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: My Dashboard
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📊 My Dashboard":
    st.markdown('<div class="page-title">📊 My Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Charts you confirmed as useful — add them from Chat & Visuals</div>',
                unsafe_allow_html=True)
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
                    st.plotly_chart(item["chart"], use_container_width=True,
                                    key=f"dash_{idx}")
                    if item.get("insight"):
                        st.markdown(
                            f'<div class="insight-box" style="font-size:.82rem">'
                            f'💡 {item["insight"]}</div>',
                            unsafe_allow_html=True,
                        )
                    if st.button("🗑️ Remove", key=f"del_{idx}"):
                        st.session_state["dashboard"].pop(idx)
                        st.rerun()
