import os
import base64
import hashlib
import requests
import streamlit as st
import pandas as pd
import extra_streamlit_components as stx
from cryptography.fernet import Fernet, InvalidToken

from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
COOKIE_SECRET = os.getenv("COOKIE_SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "finsight-default-cookie-secret-key-change-me"

_cookie_key = base64.urlsafe_b64encode(hashlib.sha256(COOKIE_SECRET.encode("utf-8")).digest())
token_cipher = Fernet(_cookie_key)


def auth_headers():
    """
    Returns Authorization header containing JWT.
    """

    token = st.session_state.get("token")

    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}"
    }


def section_header(title: str, subtitle: str, label: str | None = None):
    badge = f'<span class="fs-badge">{label}</span>' if label else ""
    st.markdown(
        f"""
        <div class="fs-section-title">
            <div><h2>{title}</h2><p>{subtitle}</p></div>
            <div>{badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.set_page_config(
    page_title="FinSight AI Assistant",
    page_icon="🤖",
    layout="wide",
)

cookie_manager = stx.CookieManager(key="finsight_cookie_manager")

def inject_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

        :root {
            --fs-bg: #0a0e16;
            --fs-bg-soft: #0d1220;
            --fs-surface: rgba(255, 255, 255, 0.035);
            --fs-surface-solid: #131a29;
            --fs-surface-solid-2: #161e30;
            --fs-border: rgba(255, 255, 255, 0.09);
            --fs-border-strong: rgba(198, 160, 79, 0.4);
            --fs-gold: #c6a04f;
            --fs-gold-soft: rgba(198, 160, 79, 0.14);
            --fs-gold-dim: #8f7638;
            --fs-teal: #3f9c93;
            --fs-text: #e9e9ec;
            --fs-text-dim: #9aa2b5;
            --fs-text-mute: #616a80;
            --fs-r-sm: 8px;
            --fs-r-md: 14px;
            --fs-r-lg: 22px;
            --fs-font-display: 'Fraunces', Georgia, serif;
            --fs-font-body: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --fs-font-mono: 'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace;
        }

        html, body, [class*="css"] {
            font-family: var(--fs-font-body);
        }

        .stApp {
            background:
                radial-gradient(900px 420px at 12% -10%, rgba(198, 160, 79, 0.08), transparent 62%),
                radial-gradient(800px 400px at 100% 0%, rgba(63, 156, 147, 0.055), transparent 58%),
                linear-gradient(180deg, var(--fs-bg) 0%, var(--fs-bg-soft) 100%);
            color: var(--fs-text);
        }

        .block-container {
            max-width: 1360px;
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(198, 160, 79, 0.35);
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover { background: rgba(198, 160, 79, 0.55); }

        h1, h2, h3, h4 {
            font-family: var(--fs-font-display);
            color: var(--fs-text);
            letter-spacing: 0.2px;
        }

        p, label, span {
            color: var(--fs-text);
        }

        [data-testid="stCaptionContainer"], .stCaption, small {
            color: var(--fs-text-dim) !important;
        }

        /* ---------- Hero card ---------- */
        .fs-hero {
            background: linear-gradient(160deg, var(--fs-surface-solid) 0%, var(--fs-surface-solid-2) 100%);
            border: 1px solid var(--fs-border);
            border-radius: var(--fs-r-lg);
            padding: 24px 30px;
            text-align: left;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.26);
            position: relative;
            overflow: hidden;
        }

        .fs-hero::before {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(500px 200px at 50% -40%, rgba(198, 160, 79, 0.18), transparent 70%);
            pointer-events: none;
        }

        .fs-hero-title {
            font-family: var(--fs-font-display);
            font-weight: 600;
            font-size: clamp(1.7rem, 3vw, 2.35rem);
            margin: 0 0 10px 0;
            color: #f5f1e8;
            letter-spacing: 0.3px;
        }

        .fs-hero-divider {
            width: 72px;
            height: 2px;
            margin: 0 0 12px 0;
            border-radius: 2px;
            background: linear-gradient(90deg, transparent, var(--fs-gold), transparent);
            background-size: 200% 100%;
            animation: fs-shimmer 3.2s ease-in-out infinite;
        }

        @keyframes fs-shimmer {
            0% { background-position: 0% 0%; }
            50% { background-position: 100% 0%; }
            100% { background-position: 0% 0%; }
        }

        @media (prefers-reduced-motion: reduce) {
            .fs-hero-divider { animation: none; }
        }

        .fs-hero-sub {
            font-family: var(--fs-font-body);
            color: var(--fs-text-dim);
            font-size: 0.98rem;
            margin: 0;
        }

        /* ---------- Profile card ---------- */
        .fs-profile-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            background: var(--fs-surface-solid);
            border: 1px solid var(--fs-border);
            border-radius: var(--fs-r-md);
            padding: 15px 10px;
            text-align: center;
        }

        .fs-profile-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--fs-gold), var(--fs-gold-dim));
            color: #14100a;
            font-family: var(--fs-font-display);
            font-weight: 700;
            font-size: 1.1rem;
        }

        .fs-profile-name {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--fs-text);
            word-break: break-word;
        }

        .fs-profile-role {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--fs-gold);
        }

        /* ---------- Badge ---------- */
        .fs-badge {
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 500;
            padding: 3px 10px;
            border-radius: 999px;
            background: var(--fs-gold-soft);
            border: 1px solid var(--fs-border-strong);
            color: #e8d4a0;
            margin-top: 4px;
        }

        .fs-section-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin: 26px 0 6px;
        }

        .fs-section-title h2 {
            font-size: 1.35rem;
            margin: 0;
        }

        .fs-section-title p {
            color: var(--fs-text-dim);
            font-size: 0.9rem;
            margin: 5px 0 0;
        }

        .fs-stat-card {
            background: rgba(19, 26, 41, 0.82);
            border: 1px solid var(--fs-border);
            border-radius: var(--fs-r-md);
            padding: 14px 16px;
        }

        /* ---------- Buttons ---------- */
        .stButton > button, button[data-testid^="stBaseButton"] {
            background: transparent;
            color: var(--fs-gold);
            border: 1px solid var(--fs-border-strong);
            border-radius: var(--fs-r-sm);
            font-family: var(--fs-font-body);
            font-weight: 500;
            letter-spacing: 0.3px;
            padding: 0.5rem 1.1rem;
            transition: all 0.2s ease;
        }

        .stButton > button:hover, button[data-testid^="stBaseButton"]:hover {
            background: var(--fs-gold-soft);
            border-color: var(--fs-gold);
            color: #f5e6bc;
        }

        .stButton > button:active, button[data-testid^="stBaseButton"]:active {
            transform: translateY(1px);
        }

        .stButton > button:focus-visible {
            outline: 2px solid var(--fs-gold);
            outline-offset: 2px;
        }

        /* ---------- Inputs ---------- */
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: var(--fs-surface-solid) !important;
            color: var(--fs-text) !important;
            border: 1px solid var(--fs-border) !important;
            border-radius: var(--fs-r-sm) !important;
        }

        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--fs-gold) !important;
            box-shadow: 0 0 0 1px var(--fs-gold) !important;
        }

        .stTextInput label, .stSelectbox label, .stFileUploader label {
            color: var(--fs-text-dim) !important;
            font-size: 0.85rem;
        }

        /* ---------- File uploader ---------- */
        [data-testid="stFileUploaderDropzone"] {
            background-color: var(--fs-surface-solid);
            border: 1px dashed var(--fs-border-strong);
            border-radius: var(--fs-r-md);
        }

        /* ---------- Tabs ---------- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            border-bottom: 1px solid var(--fs-border);
        }

        .stTabs [data-baseweb="tab"] {
            font-family: var(--fs-font-body);
            color: var(--fs-text-dim);
            letter-spacing: 0.4px;
            text-transform: uppercase;
            font-size: 0.8rem;
            padding: 10px 16px;
        }

        .stTabs [aria-selected="true"] {
            color: var(--fs-gold) !important;
            border-bottom: 2px solid var(--fs-gold) !important;
        }

        /* ---------- Expander ---------- */
        .stExpander, [data-testid="stExpander"] {
            background: var(--fs-surface-solid);
            border: 1px solid var(--fs-border) !important;
            border-radius: var(--fs-r-md) !important;
            overflow: hidden;
        }

        .stExpander summary, [data-testid="stExpander"] summary {
            color: var(--fs-text);
            font-weight: 500;
        }

        /* ---------- Alerts ---------- */
        .stAlert, [data-testid="stAlertContainer"] {
            background: var(--fs-surface-solid) !important;
            border: 1px solid var(--fs-border) !important;
            border-left: 3px solid var(--fs-gold) !important;
            border-radius: var(--fs-r-sm) !important;
        }

        /* ---------- Code blocks ---------- */
        .stCodeBlock, pre, code {
            font-family: var(--fs-font-mono) !important;
        }

        .stCodeBlock {
            border: 1px solid var(--fs-border-strong);
            border-radius: var(--fs-r-md);
        }

        /* ---------- Chat ---------- */
        [data-testid="stChatMessage"] {
            background: rgba(19, 26, 41, 0.76);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: var(--fs-r-md);
            padding: 8px 10px;
            margin-bottom: 12px;
        }

        [data-testid="stChatMessageAvatarUser"] {
            background: var(--fs-teal) !important;
        }

        [data-testid="stChatMessageAvatarAssistant"] {
            background: var(--fs-gold) !important;
        }

        [data-testid="stChatInput"]{
            position: relative;
            width: 100%;
            margin-top: 14px;
            background: rgba(20, 27, 41, 0.94);
            border: 1px solid rgba(198,160,79,.30);
            border-radius: 14px;
            padding: 5px 8px;
            box-shadow: 0 8px 24px rgba(0,0,0,.22);
        }
        .main .block-container{
            padding-bottom: 48px;
        }

        [data-testid="stChatInput"] textarea {
            color: var(--fs-text) !important;
        }

        /* ---------- Divider ---------- */
        hr {
            border-color: var(--fs-border) !important;
        }

        /* ---------- Misc ---------- */
        [data-testid="stSpinner"] p {
            color: var(--fs-text-dim);
        }

        @media (max-width: 768px) {
            .fs-hero { padding: 20px 18px; }
            .fs-hero-title { font-size: 1.5rem; }
            .block-container { padding: 1rem 0.8rem 2rem; }
            [data-testid="stChatInput"] {
                width: 95% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_theme()

BASE_DIR = os.path.dirname(__file__)

IMAGE_PATH = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "static",
        "images",
        "background.jpg",
    )
)


def set_bg_from_local(image_path: str):
    if not os.path.exists(image_path):
        return

    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(180deg, rgba(8, 11, 18, 0.88) 0%, rgba(8, 11, 18, 0.94) 100%),
                url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


set_bg_from_local(IMAGE_PATH)

left_col, right_col = st.columns([7, 1])

with left_col:
    st.markdown(
        """
        <div class="fs-hero">
            <h1 class="fs-hero-title">Welcome to FinSight</h1>
            <div class="fs-hero-divider"></div>
            <p class="fs-hero-sub">A secure workspace for trusted document intelligence and structured-data analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.session_state.setdefault("token", None)
st.session_state.setdefault("username", None)
st.session_state.setdefault("role", None)
st.session_state.setdefault("page", "login")
st.session_state.setdefault("roles", [])
st.session_state.setdefault("messages", [])
st.session_state.setdefault("auth_restore_attempted", False)
st.session_state.setdefault("logged_out", False)


def clear_persisted_session():
    """Remove the encrypted browser token during logout or failed restoration."""
    try:
        cookie_manager.delete("finsight_session", key="finsight_delete_session")
    except Exception:
        pass


def persist_session_token(token: str):
    """Store an opaque token cookie for the same lifetime as the access token."""
    try:
        encrypted_token = token_cipher.encrypt(token.encode("utf-8")).decode("utf-8")
        cookie_manager.set(
            "finsight_session",
            encrypted_token,
            key="finsight_set_session",
            max_age=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")) * 60,
            secure=os.getenv("ENVIRONMENT", "development").lower() in {"production", "prod"},
            same_site="lax",
        )
    except Exception:
        pass


def restore_persisted_session():
    """Restore a refreshed browser session only after FastAPI validates the JWT."""
    if st.session_state.auth_restore_attempted or st.session_state.token or st.session_state.get("logged_out"):
        return
    st.session_state.auth_restore_attempted = True
    try:
        encrypted_token = cookie_manager.get("finsight_session")
    except Exception:
        encrypted_token = None

    if not encrypted_token:
        return
    try:
        token = token_cipher.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError, Exception):
        clear_persisted_session()
        return
    try:
        response = requests.get(
            f"{API_URL}/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.ok:
            profile = response.json()
            st.session_state.token = token
            st.session_state.username = profile["username"]
            st.session_state.role = profile["role"]
            st.session_state.roles = fetch_roles()
            st.session_state.page = "main"
        else:
            clear_persisted_session()
    except requests.RequestException:
        # Do not erase a valid login merely because the API is temporarily unavailable.
        pass


def fetch_roles():
    """
    Fetch all available roles from FastAPI.
    """
    try:
        response = requests.get(
            f"{API_URL}/roles",
            headers=auth_headers(),
            timeout=20,
        )

        if response.ok:
            return response.json().get("roles", [])

    except requests.RequestException:
        st.error("❌ Unable to connect to FastAPI backend.")

    return []


def backend_available():
    try:
        r = requests.get(
            f"{API_URL}/docs",
            timeout=3
        )
        return r.status_code == 200
    except requests.RequestException:
        return False


restore_persisted_session()

if st.session_state.page == "login":

    if not backend_available():
        st.error("❌ FastAPI backend is not running.")
        st.info("Start it using:\n\nuvicorn app.main:app --reload")
        st.stop()

    with st.form("login_form", clear_on_submit=False):
        st.subheader("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)

    if submit:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            with st.spinner("Authenticating..."):
                try:
                    response = requests.post(
                        f"{API_URL}/login",
                        json={
                            "username": username,
                            "password": password,
                        },
                        timeout=20,
                    )

                    if response.ok:
                        data = response.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.username = data["username"]
                        st.session_state.role = data["role"]
                        st.session_state.roles = fetch_roles()
                        st.session_state.page = "main"
                        st.session_state.logged_out = False
                        st.session_state.auth_restore_attempted = True
                        persist_session_token(data["access_token"])
                        st.rerun()

                    else:
                        try:
                            st.error(response.json()["detail"])
                        except Exception:
                            st.error("Login failed.")

                except requests.ConnectionError:
                    st.error("Cannot connect to FastAPI backend.")

                except Exception as e:
                    st.exception(e)

if st.session_state.page == "main":

    username = st.session_state.username
    role = st.session_state.role

    with right_col:

        st.markdown(
            f"""
            <div class="fs-profile-card">
                <div class="fs-profile-avatar">{username[:1].upper() if username else "?"}</div>
                <div class="fs-profile-name">{username}</div>
                <div class="fs-profile-role">{role}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚪 Logout", use_container_width=True):
            try:
                requests.post(
                    f"{API_URL}/logout",
                    headers=auth_headers(),
                    timeout=10,
                )
            except requests.RequestException:
                pass
            clear_persisted_session()
            st.session_state.clear()
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.page = "login"
            st.session_state.roles = []
            st.session_state.messages = []
            st.session_state.logged_out = True
            st.session_state.auth_restore_attempted = True
            st.rerun()

    with left_col:

        if role == "C-Level":

            st.success("🌍 Global Access")

            tab1, tab2, tab3, tab4 = st.tabs(
                [
                    "💬 Chat",
                    "📂 Upload",
                    "👤 Admin",
                    "📊 AI Evaluation",
                ]
            )

        elif role == "General":

            st.info("Access to General documents.")

            (tab1,) = st.tabs(["💬 Chat"])

        else:

            st.info(
                f"You have access to **{role}** and **General** documents."
            )

            (tab1,) = st.tabs(["💬 Chat"])

    with tab1:
        section_header(
            "FinSight Assistant",
            "Ask a policy question, explore uploaded documents, or query authorized CSV data.",
            "RBAC protected",
        )

        if st.session_state.messages:
            import json
            chat_json = json.dumps(st.session_state.messages, indent=2)
            st.download_button(
                label="📥 Export Chat History (JSON)",
                data=chat_json,
                file_name="finsight_chat_history.json",
                mime="application/json",
            )

        chat_container = st.container(height=540)
        with chat_container:
            for msg in st.session_state.messages:

                with st.chat_message("user"):
                    st.markdown(msg["question"])

                with st.chat_message("assistant"):

                    st.markdown(msg["answer"])

                    if msg.get("mode"):
                        st.markdown(
                            f'<span class="fs-badge">{msg["mode"]}</span>',
                            unsafe_allow_html=True,
                        )

                    if msg.get("fallback"):
                        st.warning("SQL failed → Used RAG fallback.")

                    if msg.get("sql"):

                        with st.expander("Generated SQL"):

                            st.code(
                                msg["sql"],
                                language="sql",
                            )

                    if msg.get("sources"):
                        with st.expander("Sources"):
                            for citation in msg["sources"]:
                                st.markdown(f"- 📄 {citation.get('source', 'Unknown')}")
    
        question = st.chat_input("Ask FinSight anything...")

        if question:

            with st.chat_message("user"):
                st.markdown(question)

            with st.spinner("Thinking..."):

                try:

                    response = requests.post(
                        f"{API_URL}/chat",
                        json={"question": question},
                        headers=auth_headers(),
                        timeout=120,
                    )

                    if response.ok:

                        data = response.json()

                        answer = data.get("answer", "No answer returned.")
                        mode = data.get("mode", "")
                        fallback = data.get("fallback", False)
                        sql = data.get("sql")
                        sources = data.get("sources", [])

                        with st.chat_message("assistant"):
                            st.markdown(answer)

                            if mode:
                                st.markdown(
                                    f'<span class="fs-badge">🧠 {mode}</span>',
                                    unsafe_allow_html=True,
                                )

                            if fallback:
                                st.warning(
                                    "SQL query failed. Used RAG fallback."
                                )

                            if sql:

                                with st.expander("Generated SQL"):

                                    st.code(
                                        sql,
                                        language="sql",
                                    )

                            if sources:

                                with st.expander(
                                    "Sources"
                                ):

                                    for citation in sources:
                                        source = citation.get("source", "Unknown")
                                        page = citation.get("page")
                                        page_suffix = f" · page {page + 1}" if isinstance(page, int) else ""
                                        st.markdown(f"- 📄 {source}{page_suffix}")

                        st.session_state.messages.append(
                            {
                                "question": question,
                                "answer": answer,
                                "mode": mode,
                                "fallback": fallback,
                                "sql": sql,
                                "sources": sources,
                            }
                        )

                    else:

                        try:
                            error = response.json().get(
                                "detail",
                                "Backend Error"
                            )

                        except Exception:
                            error = response.text

                        st.error(error)

                except requests.ConnectionError:

                    st.error(
                        "Cannot connect to FastAPI backend."
                    )

                except Exception as e:

                    st.exception(e)

    if role == "C-Level":

        with tab2:
            section_header(
                "Document intake",
                "Upload files to a role-specific workspace. Indexing continues after the upload completes.",
                "C-Level only",
            )

            roles = st.session_state.roles

            selected_role = st.selectbox(
                "Assign Document Role",
                roles,
            )

            uploaded_files = st.file_uploader(
                "Choose CSV, Markdown, PDF, DOCX, or TXT files",
                type=["csv", "md", "txt", "pdf", "docx"],
                accept_multiple_files=True,
            )
            if uploaded_files:
                st.markdown("### 📂 Selected Files")
                for file in uploaded_files:
                    st.write(f"📄 {file.name}")
            if st.button("Upload Documents", use_container_width=True):

                if uploaded_files is None or len(uploaded_files) == 0:
                    st.warning("Please select one or more files.")
                else:

                    with st.spinner("Uploading document..."):

                        try:
                            files = []

                            for uploaded_file in uploaded_files:

                                files.append(
                                    (
                                        "files",
                                        (
                                            uploaded_file.name,
                                            uploaded_file.getvalue(),
                                            uploaded_file.type,
                                        ),
                                    )
                                )
                            response = requests.post(
                                f"{API_URL}/upload-docs",
                                files=files,
                                data={
                                    "role": selected_role,
                                },
                                headers=auth_headers(),
                                timeout=300,
                            )

                            if response.ok:
                                upload_result = response.json()
                                st.success(upload_result["message"])
                                if upload_result.get("indexing_started"):
                                    st.info("Indexing has started in the background. Check document status in the Admin tab.")

                            else:

                                st.error(
                                    response.json().get(
                                        "detail",
                                        "Upload failed."
                                    )
                                )

                        except Exception as e:

                            st.exception(e)

        with tab3:
            section_header(
                "Administration",
                "Manage access, roles, and the document knowledge base from one place.",
                "C-Level only",
            )

            st.markdown("### Create User")

            new_user = st.text_input(
                "Username"
            )

            new_password = st.text_input(
                "Password",
                type="password",
            )

            new_role = st.selectbox(
                "Assign Role",
                st.session_state.roles,
                key="role_select",
            )

            if st.button(
                "Create User",
                use_container_width=True,
            ):

                with st.spinner("Creating user..."):

                    try:

                        response = requests.post(
                            f"{API_URL}/create-user",
                            data={
                                "username": new_user,
                                "password": new_password,
                                "role": new_role,
                            },
                            headers=auth_headers(),
                            timeout=60,
                        )

                        if response.ok:

                            st.success(
                                response.json()["message"]
                            )

                        else:

                            st.error(
                                response.json().get(
                                    "detail",
                                    "Failed to create user."
                                )
                            )

                    except Exception as e:

                        st.exception(e)

            st.divider()

            st.markdown("### Create Role")

            role_name = st.text_input(
                "Role Name"
            )

            if st.button(
                "Create Role",
                use_container_width=True,
            ):

                with st.spinner("Creating role..."):

                    try:

                        response = requests.post(
                            f"{API_URL}/create-role",
                            data={
                                "role_name": role_name,
                            },
                            headers=auth_headers(),
                            timeout=60,
                        )

                        if response.ok:

                            st.success(
                                response.json()["message"]
                            )

                            st.session_state.roles = fetch_roles()

                            st.rerun()

                        else:

                            st.error(
                                response.json().get(
                                    "detail",
                                    "Failed to create role."
                                )
                            )

                    except Exception as e:

                        st.exception(e)
            st.divider()

            st.subheader("Manage Existing Users")
            st.caption("Role changes take effect immediately. Password resets require at least 8 characters.")

            try:
                users_response = requests.get(
                    f"{API_URL}/users",
                    headers=auth_headers(),
                    timeout=60,
                )
                users = users_response.json().get("users", []) if users_response.ok else []
            except requests.RequestException:
                users = []
                st.error("Unable to load users.")

            for managed_user in users:
                user_id = managed_user["id"]
                with st.expander(
                    f"👤 {managed_user['username']} · {managed_user['role']}",
                    expanded=False,
                ):
                    current_role = managed_user["role"]
                    role_index = (
                        st.session_state.roles.index(current_role)
                        if current_role in st.session_state.roles
                        else 0
                    )
                    selected_user_role = st.selectbox(
                        "Role",
                        st.session_state.roles,
                        index=role_index,
                        key=f"managed_user_role_{user_id}",
                    )
                    role_col, password_col = st.columns(2)
                    with role_col:
                        if st.button("Save Role", key=f"save_user_role_{user_id}"):
                            role_response = requests.put(
                                f"{API_URL}/users/{user_id}/role",
                                data={"role": selected_user_role},
                                headers=auth_headers(),
                                timeout=60,
                            )
                            if role_response.ok:
                                st.success(role_response.json()["message"])
                                st.rerun()
                            else:
                                st.error(role_response.json().get("detail", "Unable to update role."))

                    with password_col:
                        reset_password = st.text_input(
                            "New password",
                            type="password",
                            key=f"reset_password_{user_id}",
                        )
                        if st.button("Reset Password", key=f"reset_user_password_{user_id}"):
                            password_response = requests.put(
                                f"{API_URL}/users/{user_id}/password",
                                data={"password": reset_password},
                                headers=auth_headers(),
                                timeout=60,
                            )
                            if password_response.ok:
                                st.success(password_response.json()["message"])
                            else:
                                st.error(password_response.json().get("detail", "Unable to reset password."))

                    if st.session_state.get("confirm_delete_user") == user_id:
                        if st.button("Confirm Delete User", key=f"confirm_delete_user_{user_id}", type="primary"):
                            delete_user_response = requests.delete(
                                f"{API_URL}/users/{user_id}",
                                headers=auth_headers(),
                                timeout=60,
                            )
                            if delete_user_response.ok:
                                st.session_state.pop("confirm_delete_user", None)
                                st.success(delete_user_response.json()["message"])
                                st.rerun()
                            else:
                                st.error(delete_user_response.json().get("detail", "Unable to delete user."))
                    elif st.button("Delete User", key=f"delete_user_{user_id}"):
                        st.session_state["confirm_delete_user"] = user_id
                        st.rerun()

            st.divider()

            st.subheader("📂 Uploaded Documents")

            try:

                response = requests.get(
                    f"{API_URL}/documents",
                    headers=auth_headers(),
                    timeout=60,
                )

                if response.ok:
                    documents = response.json()["documents"]
                else:
                    documents = []

            except Exception as e:

                st.error("Unable to fetch uploaded documents.")
                documents = []
            grouped_docs = defaultdict(list)

            document_filter = st.text_input(
                "Search documents",
                placeholder="Filter by document name or role…",
                key="document_filter",
            ).strip().lower()

            for doc in documents:
                if document_filter and document_filter not in doc["filename"].lower() and document_filter not in doc["role"].lower():
                    continue
                grouped_docs[doc["role"]].append(doc)
            if not grouped_docs:

                st.info("No uploaded documents found.")

            else:

                for role_name, docs in grouped_docs.items():

                    with st.expander(
                        f"📁 {role_name} ({len(docs)})",
                        expanded=False,
                    ):

                        for doc in docs:
                            status_name = doc.get("status") or (
                                "indexed" if doc.get("embedded") else "pending"
                            )
                            status_label = {
                                "indexed": "✅ Indexed",
                                "pending": "⏳ Queued",
                                "indexing": "🔄 Indexing",
                                "failed": "⚠️ Failed",
                            }.get(status_name, status_name.title())

                            doc_col, retry_col, delete_col = st.columns([6, 1.4, 1.4])
                            with doc_col:
                                st.markdown(f"📄 **{doc['filename']}**  —  {status_label}")
                                if status_name == "failed" and doc.get("error_message"):
                                    st.caption(f"Indexing error: {doc['error_message']}")

                            with retry_col:
                                if status_name == "failed" and st.button(
                                    "Retry", key=f"retry_document_{doc['id']}"
                                ):
                                    retry_response = requests.post(
                                        f"{API_URL}/documents/{doc['id']}/retry",
                                        headers=auth_headers(),
                                        timeout=60,
                                    )
                                    if retry_response.ok:
                                        st.success("Retry started.")
                                        st.rerun()
                                    else:
                                        st.error(retry_response.json().get("detail", "Retry failed."))

                            with delete_col:
                                confirmation_key = f"confirm_delete_document_{doc['id']}"
                                if st.session_state.get("confirm_delete_document") == doc["id"]:
                                    if st.button("Confirm", key=confirmation_key, type="primary"):
                                        delete_response = requests.delete(
                                            f"{API_URL}/documents/{doc['id']}",
                                            headers=auth_headers(),
                                            timeout=60,
                                        )
                                        if delete_response.ok:
                                            st.session_state.pop("confirm_delete_document", None)
                                            st.success("Document deleted.")
                                            st.rerun()
                                        else:
                                            st.error(delete_response.json().get("detail", "Delete failed."))
                                elif st.button("Delete", key=f"delete_document_{doc['id']}"):
                                    st.session_state["confirm_delete_document"] = doc["id"]
                                    st.rerun()
        with tab4:
            section_header(
                "AI performance",
                "Track answer quality, response speed, routing behavior, and recent activity.",
                "C-Level only",
            )

            response = requests.get(
                f"{API_URL}/dashboard",
                headers=auth_headers(),
                timeout=60,
            )

            if response.ok:
                dashboard = response.json()
                overview = dashboard["overview"]

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "📊 Total Queries",
                    overview.get("total_queries", 0)
                )

                col2.metric(
                    "🎯 Avg Confidence",
                    f'{overview.get("avg_confidence",0):.1f}%'
                )

                col3.metric(
                    "✅ Faithfulness",
                    f'{overview.get("avg_faithfulness",0):.2f}'
                )

                col4.metric(
                    "⚡ Avg Latency",
                    f'{overview.get("avg_latency",0):.0f} ms'
                )

                # =====================================
                # KPI Row 2
                # =====================================

                col5, col6, col7, col8 = st.columns(4)

                col5.metric(
                    "📚 Avg Retrieved Docs",
                    f'{overview.get("avg_sources",0):.1f}'
                )
                col6.metric(
                    "👻 Hallucination Rate",
                    f'{overview.get("hallucination_rate",0):.1f}%'
                )

                col7.metric(
                    "🗄 SQL vs RAG Ratio",
                    f'{overview.get("sql_ratio",0):.0f}% / {overview.get("rag_ratio",0):.0f}%'
                )

                col8.metric(
                    "🔁 Fallback Rate",
                    f'{overview.get("fallback_rate",0):.1f}%'
                )

                st.divider()

                history_df = pd.DataFrame(dashboard["history"])
                if not history_df.empty:
                    chart_left, chart_right = st.columns(2)
                    history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], errors="coerce")
                    timeline = history_df.dropna(subset=["timestamp"]).sort_values("timestamp")

                    with chart_left:
                        st.caption("Quality Trend (Confidence, Faithfulness & Relevancy)")
                        if not timeline.empty:
                            metrics_cols = [c for c in ["confidence", "faithfulness", "relevancy", "context_recall"] if c in timeline.columns]
                            st.line_chart(
                                timeline.set_index("timestamp")[metrics_cols],
                                height=220,
                            )

                    with chart_right:
                        st.caption("Query Routing Distribution")
                        route_counts = history_df["mode"].fillna("Unknown").value_counts()
                        st.bar_chart(route_counts, height=220)

                    st.subheader("Recent Conversations")
                    st.dataframe(
                        history_df,
                        use_container_width=True,
                    )
                else:
                    st.info("ℹ️ No conversation evaluation logs recorded yet. Ask a question in the Chat tab to generate live AI evaluation metrics.")

            else:
                try:
                    error = response.json().get(
                        "detail",
                        "Unable to load dashboard."
                    )
                except Exception:
                    error = response.text

                st.error(error)
