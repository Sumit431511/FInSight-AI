import os
import base64
import requests
import streamlit as st

from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
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

st.set_page_config(
    page_title="FinSight AI Assistant",
    page_icon="🤖",
    layout="wide",
)

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
                radial-gradient(1200px 600px at 15% -10%, rgba(198, 160, 79, 0.08), transparent 60%),
                radial-gradient(1000px 500px at 100% 0%, rgba(63, 156, 147, 0.07), transparent 55%),
                linear-gradient(180deg, var(--fs-bg) 0%, var(--fs-bg-soft) 100%);
            color: var(--fs-text);
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
            padding: 28px 32px;
            text-align: center;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
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
            font-size: 2.1rem;
            margin: 0 0 14px 0;
            color: #f5f1e8;
            letter-spacing: 0.3px;
        }

        .fs-hero-divider {
            width: 96px;
            height: 2px;
            margin: 0 auto 14px auto;
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
            padding: 14px 8px;
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
            background: var(--fs-surface-solid);
            border: 1px solid var(--fs-border);
            border-radius: var(--fs-r-md);
            padding: 4px 8px;
            margin-bottom: 10px;
        }

        [data-testid="stChatMessageAvatarUser"] {
            background: var(--fs-teal) !important;
        }

        [data-testid="stChatMessageAvatarAssistant"] {
            background: var(--fs-gold) !important;
        }

        [data-testid="stChatInput"]{
            position:fixed;
            bottom:18px;
            left:50%;
            transform:translateX(-50%);
            width:72%;
            z-index:99999;

            background:#141b29;
            border:1px solid rgba(198,160,79,.35);
            border-radius:18px;

            padding:8px;
            box-shadow:
            0 0 20px rgba(0,0,0,.45);
        }
        .main .block-container{
            padding-bottom:140px;
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

        @media (max-width: 640px) {
            .fs-hero { padding: 20px 18px; }
            .fs-hero-title { font-size: 1.5rem; }
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
            <p class="fs-hero-sub">Your AI-powered document assistant for FinSolve Technologies.</p>
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

        return r.status_code==200

    except requests.RequestException:

        return False

if st.session_state.page == "login":

    st.subheader("🔐 Login")

    if not backend_available():
        st.error("❌ FastAPI backend is not running.")
        st.info("Start it using:\n\nuvicorn app.main:app --reload")
        st.stop()

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):

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

                    st.success("✅ Login Successful")

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
            st.session_state.clear()

            st.session_state.token = None

            st.session_state.username = None

            st.session_state.role = None

            st.session_state.page = "login"

            st.session_state.roles = []

            st.session_state.messages = []

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

        st.markdown("""
                <div style="
                padding:18px;
                border-radius:14px;
                background:#141b29;
                border:1px solid rgba(198,160,79,.18);
                margin-bottom:15px;
                ">
                <h2 style="margin:0">
                🤖 FinSight Assistant
                </h2>

                <span style="color:#9AA2B5">
                Hybrid SQL + RAG • RBAC Enabled
                </span>
                </div>
                """,
                unsafe_allow_html=True)

        chat_container = st.container(height=650)
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
                        context = data.get("context", [])

                        with st.chat_message("assistant"):

                            st.markdown(
                                        f"""
                                        <div style="
                                        padding:18px;
                                        border-radius:14px;
                                        background:#182131;
                                        border-left:4px solid #c6a04f;
                                        ">

                                        {answer}

                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                        )

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

                            if context:

                                with st.expander(
                                    "Retrieved Documents"
                                ):

                                    for doc in context:

                                        metadata = doc.get(
                                            "metadata",
                                            {}
                                        )

                                        source = metadata.get(
                                            "source",
                                            "Unknown"
                                        )

                                        st.markdown(
                                            f"### 📄 {source}"
                                        )

                                        st.write(
                                            doc.get(
                                                "page_content",
                                                ""
                                            )[:500]
                                        )

                        st.session_state.messages.append(
                            {
                                "question": question,
                                "answer": answer,
                                "mode": mode,
                                "fallback": fallback,
                                "sql": sql,
                                "context": context,
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

            st.subheader("📂 Upload Documents")

            roles = st.session_state.roles

            selected_role = st.selectbox(
                "Assign Document Role",
                roles,
            )

            uploaded_files = st.file_uploader(
                "Choose CSV or Markdown files",
                type=["csv", "md"],
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

                                st.success(
                                    response.json()["message"]
                                )

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

            st.subheader("👤 User Management")

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

            for doc in documents:
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

                            status = (
                                "✅ Indexed"
                                if doc["embedded"]
                                else "⏳ Pending"
                            )

                            st.write(
                                f"📄 **{doc['filename']}**  —  {status}"
                            )
        with tab4:

            st.header("📊 AI Evaluation Dashboard")

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
                    "📚 Average Retrieved Documents",
                    f'{overview.get("avg_sources",0):.1f}%'
                )
                col6.metric(
                    "🗄 SQL Queries",
                    f'{overview.get("sql_ratio",0):.1f}%'
                )

                col7.metric(
                    "📄 RAG Queries",
                    f'{overview.get("rag_ratio",0):.1f}%'
                )

                col8.metric(
                    "🔁 Fallback Rate",
                    f'{overview.get("fallback_rate",0):.1f}%'
                )

                st.divider()
                

                st.subheader("Recent Conversations")

                st.dataframe(
                    dashboard["history"],
                    use_container_width=True,
                )

            else:

                try:
                    error = response.json().get(
                        "detail",
                        "Unable to load dashboard."
                    )

                except Exception:
                    error = response.text

                st.error(error)