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
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


st.set_page_config(
    page_title="FinSight AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─────────────────────────────────────────────────────────────
# LINEAR / MODERN DESIGN SYSTEM — Full CSS Injection
# ─────────────────────────────────────────────────────────────
def inject_theme():
    st.markdown(
        """
        <style>
        /* ── Google Fonts ── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ─────────────── Design Tokens ─────────────── */
        :root {
            --bg-deep:          #020203;
            --bg-base:          #050506;
            --bg-elevated:      #0a0a0c;
            --surface:          rgba(255,255,255,0.05);
            --surface-hover:    rgba(255,255,255,0.08);
            --fg:               #EDEDEF;
            --fg-muted:         #8A8F98;
            --fg-subtle:        rgba(255,255,255,0.45);
            --accent:           #5E6AD2;
            --accent-bright:    #6872D9;
            --accent-glow:      rgba(94,106,210,0.30);
            --accent-glow-sm:   rgba(94,106,210,0.15);
            --border:           rgba(255,255,255,0.06);
            --border-hover:     rgba(255,255,255,0.10);
            --border-accent:    rgba(94,106,210,0.30);
            --radius-sm:        6px;
            --radius-md:        10px;
            --radius-lg:        16px;
            --radius-xl:        22px;
            --font-body:        'Inter', system-ui, sans-serif;
            --font-mono:        'JetBrains Mono', 'SFMono-Regular', monospace;
            --ease-out-expo:    cubic-bezier(0.16,1,0.3,1);
        }

        /* ─────────────── Global Reset ─────────────── */
        html, body, [class*="css"] {
            font-family: var(--font-body) !important;
            color: var(--fg);
        }

        /* ─────────────── Background System ─────────────── */
        .stApp {
            background: var(--bg-base) !important;
            min-height: 100vh;
        }

        /* Noise texture overlay */
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
            opacity: 0.018;
            pointer-events: none;
            z-index: 0;
        }

        /* Ambient blob 1 — top center indigo */
        .stApp::after {
            content: "";
            position: fixed;
            top: -200px;
            left: 50%;
            transform: translateX(-50%);
            width: 1000px;
            height: 700px;
            background: radial-gradient(ellipse, rgba(94,106,210,0.22) 0%, transparent 70%);
            filter: blur(80px);
            pointer-events: none;
            z-index: 0;
            animation: blob-float 10s ease-in-out infinite;
        }

        @keyframes blob-float {
            0%,100% { transform: translateX(-50%) translateY(0px) rotate(0deg); }
            50%      { transform: translateX(-50%) translateY(-24px) rotate(1.5deg); }
        }

        /* ─────────────── Layout ─────────────── */
        .block-container {
            max-width: 1320px !important;
            padding-top: 2rem !important;
            padding-bottom: 4rem !important;
            position: relative;
            z-index: 1;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        /* ─────────────── Scrollbar ─────────────── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(94,106,210,0.35);
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover { background: rgba(94,106,210,0.55); }

        /* ─────────────── Typography ─────────────── */
        h1, h2, h3, h4, h5 {
            font-family: var(--font-body) !important;
            color: var(--fg) !important;
            letter-spacing: -0.02em;
            font-weight: 600;
        }

        p, label, span, div { color: var(--fg); }

        [data-testid="stCaptionContainer"], .stCaption, small {
            color: var(--fg-muted) !important;
            font-size: 0.82rem !important;
        }

        /* ─────────────── Hero Card ─────────────── */
        .fs-hero {
            position: relative;
            padding: 36px 40px;
            border-radius: var(--radius-xl);
            border: 1px solid var(--border);
            background: linear-gradient(135deg,
                rgba(94,106,210,0.08) 0%,
                rgba(255,255,255,0.03) 50%,
                rgba(0,0,0,0) 100%);
            box-shadow:
                0 0 0 1px var(--border),
                0 2px 20px rgba(0,0,0,0.45),
                0 0 60px rgba(94,106,210,0.06);
            overflow: hidden;
        }

        .fs-hero::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg,
                transparent, rgba(94,106,210,0.5), transparent);
        }

        .fs-hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: var(--font-mono);
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--accent);
            background: rgba(94,106,210,0.1);
            border: 1px solid var(--border-accent);
            border-radius: 999px;
            padding: 3px 10px;
            margin-bottom: 14px;
        }

        .fs-hero-title {
            font-family: var(--font-body);
            font-size: clamp(1.8rem, 3.5vw, 2.6rem);
            font-weight: 700;
            letter-spacing: -0.03em;
            line-height: 1.15;
            margin: 0 0 10px 0;
            background: linear-gradient(180deg, #ffffff 0%, rgba(255,255,255,0.72) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .fs-hero-sub {
            font-size: 0.95rem;
            color: var(--fg-muted);
            line-height: 1.65;
            max-width: 520px;
            margin: 0;
        }

        /* Shimmer animated gradient text */
        @keyframes shimmer {
            0%   { background-position: 0% center; }
            100% { background-position: 200% center; }
        }

        .fs-shimmer-text {
            background: linear-gradient(90deg,
                var(--accent) 0%, #a5b4fc 45%, var(--accent) 90%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmer 4s linear infinite;
        }

        /* ─────────────── Profile Card ─────────────── */
        .fs-profile {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 7px;
            background: linear-gradient(160deg,
                rgba(255,255,255,0.06) 0%,
                rgba(255,255,255,0.02) 100%);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 18px 14px;
            text-align: center;
            box-shadow: 0 0 0 1px var(--border),
                        0 4px 24px rgba(0,0,0,0.3);
        }

        .fs-profile-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--accent) 0%, #818cf8 100%);
            color: #fff;
            font-family: var(--font-body);
            font-weight: 700;
            font-size: 1.1rem;
            box-shadow: 0 0 18px rgba(94,106,210,0.45);
        }

        .fs-profile-name {
            font-size: 0.88rem;
            font-weight: 600;
            color: var(--fg);
            word-break: break-word;
        }

        .fs-profile-role {
            font-family: var(--font-mono);
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--accent);
        }

        /* ─────────────── Badges ─────────────── */
        .fs-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-family: var(--font-mono);
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 3px 10px;
            border-radius: 999px;
            background: rgba(94,106,210,0.12);
            border: 1px solid var(--border-accent);
            color: #a5b4fc;
        }

        /* ─────────────── Section Header ─────────────── */
        .fs-section-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin: 28px 0 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }

        .fs-section-title {
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: var(--fg);
            margin: 0;
        }

        .fs-section-sub {
            color: var(--fg-muted);
            font-size: 0.88rem;
            margin: 4px 0 0;
            line-height: 1.5;
        }

        /* ─────────────── Buttons ─────────────── */
        .stButton > button,
        button[data-testid^="stBaseButton"] {
            font-family: var(--font-body) !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.01em;
            border-radius: var(--radius-md) !important;
            padding: 0.55rem 1.2rem !important;
            transition: all 200ms var(--ease-out-expo) !important;
            border: none !important;
            background: var(--surface) !important;
            color: var(--fg) !important;
            box-shadow:
                0 0 0 1px var(--border),
                inset 0 1px 0 rgba(255,255,255,0.08) !important;
        }

        .stButton > button:hover,
        button[data-testid^="stBaseButton"]:hover {
            background: var(--surface-hover) !important;
            color: #fff !important;
            box-shadow:
                0 0 0 1px var(--border-hover),
                inset 0 1px 0 rgba(255,255,255,0.12),
                0 4px 16px rgba(0,0,0,0.3) !important;
            transform: translateY(-1px);
        }

        .stButton > button:active,
        button[data-testid^="stBaseButton"]:active {
            transform: scale(0.98) translateY(0) !important;
        }

        /* Primary button override (type="primary") */
        .stButton > button[kind="primary"] {
            background: var(--accent) !important;
            color: #fff !important;
            box-shadow:
                0 0 0 1px rgba(94,106,210,0.5),
                0 4px 12px rgba(94,106,210,0.35),
                inset 0 1px 0 rgba(255,255,255,0.2) !important;
        }

        .stButton > button[kind="primary"]:hover {
            background: var(--accent-bright) !important;
            box-shadow:
                0 0 0 1px rgba(94,106,210,0.7),
                0 8px 24px rgba(94,106,210,0.45),
                inset 0 1px 0 rgba(255,255,255,0.25) !important;
            transform: translateY(-2px) !important;
        }

        /* ─────────────── Inputs ─────────────── */
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stNumberInput input {
            background: rgba(10,10,14,0.8) !important;
            color: var(--fg) !important;
            border: 1px solid var(--border-hover) !important;
            border-radius: var(--radius-md) !important;
            font-family: var(--font-body) !important;
            font-size: 0.9rem !important;
            transition: border-color 200ms, box-shadow 200ms !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(94,106,210,0.2) !important;
            outline: none !important;
        }

        .stTextInput label,
        .stTextArea label,
        .stSelectbox label,
        .stFileUploader label,
        .stNumberInput label {
            color: var(--fg-muted) !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.01em;
        }

        /* ─────────────── File Uploader ─────────────── */
        [data-testid="stFileUploaderDropzone"] {
            background: rgba(10,10,14,0.6) !important;
            border: 1px dashed var(--border-accent) !important;
            border-radius: var(--radius-lg) !important;
            transition: border-color 200ms, background 200ms !important;
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            background: rgba(94,106,210,0.05) !important;
            border-color: var(--accent) !important;
        }

        /* ─────────────── Tabs ─────────────── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            border-bottom: 1px solid var(--border) !important;
            background: transparent !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-family: var(--font-mono) !important;
            font-size: 0.72rem !important;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--fg-muted) !important;
            padding: 10px 18px !important;
            border-radius: 0 !important;
            background: transparent !important;
            border: none !important;
            transition: color 200ms !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: var(--fg) !important;
            background: rgba(255,255,255,0.03) !important;
        }

        .stTabs [aria-selected="true"] {
            color: var(--accent) !important;
            border-bottom: 2px solid var(--accent) !important;
            margin-bottom: -1px;
        }

        /* ─────────────── Expanders ─────────────── */
        .stExpander,
        [data-testid="stExpander"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-md) !important;
            overflow: hidden;
            box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
        }

        [data-testid="stExpander"] summary {
            color: var(--fg) !important;
            font-weight: 500;
            font-size: 0.9rem !important;
            padding: 12px 16px !important;
        }

        [data-testid="stExpander"] summary:hover {
            background: var(--surface-hover) !important;
        }

        /* ─────────────── Alerts ─────────────── */
        .stAlert,
        [data-testid="stAlertContainer"] {
            background: rgba(10,10,14,0.7) !important;
            border: 1px solid var(--border) !important;
            border-left: 2px solid var(--accent) !important;
            border-radius: var(--radius-md) !important;
            font-size: 0.88rem !important;
        }

        .stSuccess {
            border-left-color: #34d399 !important;
        }

        .stWarning {
            border-left-color: #fbbf24 !important;
        }

        .stError {
            border-left-color: #f87171 !important;
        }

        /* ─────────────── Metrics ─────────────── */
        [data-testid="stMetric"] {
            background: linear-gradient(160deg,
                rgba(255,255,255,0.06) 0%,
                rgba(255,255,255,0.02) 100%);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 16px 18px;
            box-shadow: 0 0 0 1px var(--border),
                        0 4px 20px rgba(0,0,0,0.3);
            transition: border-color 200ms, box-shadow 200ms;
        }

        [data-testid="stMetric"]:hover {
            border-color: var(--border-accent);
            box-shadow: 0 0 0 1px var(--border-accent),
                        0 8px 32px rgba(94,106,210,0.12);
        }

        [data-testid="stMetricLabel"] {
            font-family: var(--font-mono) !important;
            font-size: 0.7rem !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--fg-muted) !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: var(--fg) !important;
            letter-spacing: -0.02em;
        }

        /* ─────────────── Chat Messages ─────────────── */
        [data-testid="stChatMessage"] {
            background: linear-gradient(160deg,
                rgba(255,255,255,0.06) 0%,
                rgba(255,255,255,0.02) 100%);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 14px 16px;
            margin-bottom: 10px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.2);
        }

        [data-testid="stChatMessageAvatarUser"] {
            background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
        }

        [data-testid="stChatMessageAvatarAssistant"] {
            background: linear-gradient(135deg, var(--accent), #818cf8) !important;
            box-shadow: 0 0 14px rgba(94,106,210,0.4) !important;
        }

        [data-testid="stChatInput"] {
            position: relative;
            background: rgba(10,10,14,0.85) !important;
            border: 1px solid var(--border-hover) !important;
            border-radius: var(--radius-lg) !important;
            box-shadow: 0 0 0 1px var(--border),
                        0 8px 28px rgba(0,0,0,0.25) !important;
            transition: border-color 200ms, box-shadow 200ms !important;
        }

        [data-testid="stChatInput"]:focus-within {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px rgba(94,106,210,0.4),
                        0 8px 32px rgba(94,106,210,0.1) !important;
        }

        [data-testid="stChatInput"] textarea {
            color: var(--fg) !important;
            font-family: var(--font-body) !important;
        }

        /* ─────────────── Code Blocks ─────────────── */
        .stCodeBlock, pre {
            background: rgba(10,10,14,0.9) !important;
            border: 1px solid var(--border-accent) !important;
            border-radius: var(--radius-md) !important;
            font-family: var(--font-mono) !important;
        }

        code {
            font-family: var(--font-mono) !important;
            color: #a5b4fc !important;
        }

        /* ─────────────── Divider ─────────────── */
        hr {
            border-color: var(--border) !important;
        }

        /* ─────────────── Dataframe ─────────────── */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-lg) !important;
            overflow: hidden;
        }

        /* ─────────────── Selectbox Dropdown ─────────────── */
        [data-baseweb="popover"] {
            background: rgba(12,12,16,0.97) !important;
            border: 1px solid var(--border-hover) !important;
            border-radius: var(--radius-md) !important;
            backdrop-filter: blur(20px) !important;
        }

        [data-baseweb="menu"] li {
            color: var(--fg) !important;
            font-size: 0.88rem !important;
        }

        [data-baseweb="menu"] li:hover {
            background: var(--surface-hover) !important;
        }

        /* ─────────────── Spinner ─────────────── */
        [data-testid="stSpinner"] p {
            color: var(--fg-muted) !important;
            font-size: 0.88rem !important;
        }

        /* ─────────────── Login card ─────────────── */
        .fs-login-wrap {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 70vh;
        }

        .fs-login-card {
            width: 100%;
            max-width: 420px;
            margin: 0 auto;
            padding: 36px 32px;
            background: linear-gradient(160deg,
                rgba(255,255,255,0.07) 0%,
                rgba(255,255,255,0.02) 100%);
            border: 1px solid var(--border-hover);
            border-radius: var(--radius-xl);
            box-shadow:
                0 0 0 1px var(--border),
                0 8px 40px rgba(0,0,0,0.5),
                0 0 80px rgba(94,106,210,0.08);
            position: relative;
            overflow: hidden;
        }

        .fs-login-card::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg,
                transparent, rgba(94,106,210,0.6), transparent);
        }

        .fs-login-title {
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: linear-gradient(180deg, #fff 0%, rgba(255,255,255,0.7) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 4px 0;
        }

        .fs-login-sub {
            color: var(--fg-muted);
            font-size: 0.88rem;
            margin: 0 0 24px 0;
        }

        /* ─────────────── Responsive ─────────────── */
        @media (max-width: 768px) {
            .fs-hero { padding: 24px 20px; }
            .fs-hero-title { font-size: 1.55rem; }
            .block-container { padding: 1rem 0.8rem 3rem !important; }
            .main .block-container { padding-bottom: 60px !important; }
        }

        /* ─────────────── Reduced motion ─────────────── */
        @media (prefers-reduced-motion: reduce) {
            .stApp::after, .fs-shimmer-text { animation: none !important; }
            * { transition-duration: 0ms !important; }
        }

        /* ─────────────── Extra ambient blob (bottom right) ─────────────── */
        .fs-blob-br {
            position: fixed;
            bottom: -150px;
            right: -100px;
            width: 600px;
            height: 500px;
            background: radial-gradient(ellipse,
                rgba(99,102,241,0.12) 0%, transparent 70%);
            filter: blur(90px);
            pointer-events: none;
            z-index: 0;
            animation: blob-br 12s ease-in-out infinite;
        }

        @keyframes blob-br {
            0%,100% { transform: translateY(0) rotate(0deg); }
            50%      { transform: translateY(-20px) rotate(-1deg); }
        }

        /* Bottom left purple blob */
        .fs-blob-bl {
            position: fixed;
            bottom: 100px;
            left: -120px;
            width: 500px;
            height: 400px;
            background: radial-gradient(ellipse,
                rgba(139,92,246,0.1) 0%, transparent 70%);
            filter: blur(80px);
            pointer-events: none;
            z-index: 0;
            animation: blob-bl 9s ease-in-out infinite;
        }

        @keyframes blob-bl {
            0%,100% { transform: translateY(0) rotate(0deg); }
            50%      { transform: translateY(20px) rotate(1.5deg); }
        }
        </style>

        <!-- ambient blobs injected as DOM elements for z-index stacking -->
        <div class="fs-blob-br"></div>
        <div class="fs-blob-bl"></div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str, label: str | None = None):
    badge_html = (
        f'<span class="fs-badge">✦ {label}</span>' if label else ""
    )
    st.markdown(
        f"""
        <div class="fs-section-header">
            <div>
                <div class="fs-section-title">{title}</div>
                <div class="fs-section-sub">{subtitle}</div>
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Boot theme ───
inject_theme()

# ─────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────
st.session_state.setdefault("token", None)
st.session_state.setdefault("username", None)
st.session_state.setdefault("role", None)
st.session_state.setdefault("page", "login")
st.session_state.setdefault("roles", [])
st.session_state.setdefault("messages", [])
st.session_state.setdefault("auth_restore_attempted", False)
st.session_state.setdefault("logged_out", False)

cookie_manager = stx.CookieManager(key="finsight_cookie_manager")


def clear_persisted_session():
    try:
        cookie_manager.delete("finsight_session", key="finsight_delete_session")
    except Exception:
        pass


def persist_session_token(token: str):
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
        pass


def fetch_roles():
    try:
        response = requests.get(
            f"{API_URL}/roles",
            headers=auth_headers(),
            timeout=20,
        )
        if response.ok:
            return response.json().get("roles", [])
    except requests.RequestException:
        st.error("❌ Unable to connect to backend.")
    return []


def backend_available():
    try:
        r = requests.get(f"{API_URL}/health", timeout=4)
        return r.status_code == 200
    except requests.RequestException:
        return False


# ─────────────────────────────────────────────────────────────
# Session restore
# ─────────────────────────────────────────────────────────────
restore_persisted_session()


# ─────────────────────────────────────────────────────────────
# ── Header row (hero + profile)
# ─────────────────────────────────────────────────────────────
left_col, right_col = st.columns([7, 1])

with left_col:
    st.markdown(
        """
        <div class="fs-hero">
            <div class="fs-hero-eyebrow">✦ Enterprise AI Assistant</div>
            <h1 class="fs-hero-title">
                FinSight<span class="fs-shimmer-text"> AI</span>
            </h1>
            <p class="fs-hero-sub">
                Secure document intelligence and structured-data analysis
                with role-based access control.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# ── LOGIN PAGE
# ─────────────────────────────────────────────────────────────
if st.session_state.page == "login":

    if not backend_available():
        st.error("❌ FastAPI backend is not reachable.")
        st.info("Start it with:\n\n`uvicorn app.main:app --reload`")
        st.stop()

    # centred login card
    st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown(
            """
            <div class="fs-login-card">
                <div class="fs-login-title">Sign in</div>
                <div class="fs-login-sub">Enter your credentials to access FinSight</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="e.g. admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign in →", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                with st.spinner("Authenticating…"):
                    try:
                        response = requests.post(
                            f"{API_URL}/login",
                            json={"username": username, "password": password},
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
                                st.error("Invalid credentials.")
                    except requests.ConnectionError:
                        st.error("Cannot reach the backend.")
                    except Exception as e:
                        st.exception(e)


# ─────────────────────────────────────────────────────────────
# ── MAIN APPLICATION (logged in)
# ─────────────────────────────────────────────────────────────
if st.session_state.page == "main":

    username = st.session_state.username
    role = st.session_state.role

    # ── Profile card + logout (right column)
    with right_col:
        st.markdown(
            f"""
            <div class="fs-profile">
                <div class="fs-profile-avatar">{username[:1].upper() if username else "?"}</div>
                <div class="fs-profile-name">{username}</div>
                <div class="fs-profile-role">{role}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sign out", use_container_width=True):
            try:
                requests.post(f"{API_URL}/logout", headers=auth_headers(), timeout=10)
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

    # ── Access level indicator + tabs
    with left_col:
        if role == "C-Level":
            st.success("🌍 You have global access to all documents and features.")
            tab1, tab2, tab3, tab4 = st.tabs([
                "💬  Chat",
                "📂  Upload",
                "👤  Admin (C-Level)",
                "📊  AI Evaluation",
            ])
        elif role == "General":
            st.info("📄 You have access to General documents.")
            (tab1,) = st.tabs(["💬  Chat"])
        else:
            st.info(
                f"You have access to documents and features related to the **{role}** role. "
                f"You also have access to General documents (e.g., company policies, holidays, announcements)"
            )
            (tab1,) = st.tabs(["💬  Chat"])

    # ─────────────────────────────────────────────────────────
    # ── Tab 1: Chat
    # ─────────────────────────────────────────────────────────
    with tab1:
        section_header(
            "FinSight Assistant",
            "Ask a policy question, explore documents, or query authorized CSV data.",
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
                            f'<span class="fs-badge">🧠 {msg["mode"]}</span>',
                            unsafe_allow_html=True,
                        )
                    if msg.get("fallback"):
                        st.warning("SQL failed → Used RAG fallback.")
                    if msg.get("sql"):
                        with st.expander("Generated SQL"):
                            st.code(msg["sql"], language="sql")
                    if msg.get("sources"):
                        with st.expander("Sources"):
                            for citation in msg["sources"]:
                                st.markdown(f"- 📄 {citation.get('source', 'Unknown')}")

        question = st.chat_input("Ask FinSight anything…")

        if question:
            with st.chat_message("user"):
                st.markdown(question)

            with st.spinner("Thinking…"):
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
                                st.warning("SQL query failed. Used RAG fallback.")
                            if sql:
                                with st.expander("Generated SQL"):
                                    st.code(sql, language="sql")
                            if sources:
                                with st.expander("Sources"):
                                    for citation in sources:
                                        source = citation.get("source", "Unknown")
                                        page = citation.get("page")
                                        page_suffix = f" · page {page + 1}" if isinstance(page, int) else ""
                                        st.markdown(f"- 📄 {source}{page_suffix}")

                        st.session_state.messages.append({
                            "question": question,
                            "answer": answer,
                            "mode": mode,
                            "fallback": fallback,
                            "sql": sql,
                            "sources": sources,
                        })
                    else:
                        try:
                            error = response.json().get("detail", "Backend Error")
                        except Exception:
                            error = response.text
                        st.error(error)

                except requests.ConnectionError:
                    st.error("Cannot connect to FastAPI backend.")
                except Exception as e:
                    st.exception(e)

    # ─────────────────────────────────────────────────────────
    # ── Tab 2: Upload (C-Level only)
    # ─────────────────────────────────────────────────────────
    if role == "C-Level":
        with tab2:
            section_header(
                "Document Intake",
                "Upload files to a role-specific workspace. Indexing runs automatically in the background.",
                "C-Level only",
            )

            roles = st.session_state.roles
            selected_role = st.selectbox("Assign Document Role", roles)
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
                if not uploaded_files:
                    st.warning("Please select one or more files.")
                else:
                    with st.spinner("Uploading…"):
                        try:
                            files = [
                                ("files", (f.name, f.getvalue(), f.type))
                                for f in uploaded_files
                            ]
                            response = requests.post(
                                f"{API_URL}/upload-docs",
                                files=files,
                                data={"role": selected_role},
                                headers=auth_headers(),
                                timeout=300,
                            )
                            if response.ok:
                                upload_result = response.json()
                                st.success(upload_result["message"])
                                if upload_result.get("indexing_started"):
                                    st.info("Indexing started in the background. Check status in the Admin tab.")
                            else:
                                st.error(response.json().get("detail", "Upload failed."))
                        except Exception as e:
                            st.exception(e)

        # ─────────────────────────────────────────────────────
        # ── Tab 3: Admin (C-Level only)
        # ─────────────────────────────────────────────────────
        with tab3:
            section_header(
                "Administration",
                "Manage access, roles, and the document knowledge base from one place.",
                "C-Level only",
            )

            st.markdown("### Create User")
            new_user = st.text_input("Username", key="new_user_input")
            new_password = st.text_input("Password", type="password", key="new_password_input")
            new_role = st.selectbox("Assign Role", st.session_state.roles, key="role_select")

            if st.button("Create User", use_container_width=True):
                with st.spinner("Creating user…"):
                    try:
                        response = requests.post(
                            f"{API_URL}/create-user",
                            data={"username": new_user, "password": new_password, "role": new_role},
                            headers=auth_headers(),
                            timeout=60,
                        )
                        if response.ok:
                            st.success(response.json()["message"])
                        else:
                            st.error(response.json().get("detail", "Failed to create user."))
                    except Exception as e:
                        st.exception(e)

            st.divider()
            st.markdown("### Create Role")
            role_name = st.text_input("Role Name", key="new_role_name_input")

            if st.button("Create Role", use_container_width=True):
                with st.spinner("Creating role…"):
                    try:
                        response = requests.post(
                            f"{API_URL}/create-role",
                            data={"role_name": role_name},
                            headers=auth_headers(),
                            timeout=60,
                        )
                        if response.ok:
                            st.success(response.json()["message"])
                            st.session_state.roles = fetch_roles()
                            st.rerun()
                        else:
                            st.error(response.json().get("detail", "Failed to create role."))
                    except Exception as e:
                        st.exception(e)

            st.divider()
            st.subheader("Manage Existing Users")
            st.caption("Role changes take effect immediately. Password resets require at least 8 characters.")

            try:
                users_response = requests.get(
                    f"{API_URL}/users", headers=auth_headers(), timeout=60
                )
                users = users_response.json().get("users", []) if users_response.ok else []
            except requests.RequestException:
                users = []
                st.error("Unable to load users.")

            for managed_user in users:
                user_id = managed_user["id"]
                with st.expander(f"👤 {managed_user['username']} · {managed_user['role']}", expanded=False):
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
                            "New password", type="password", key=f"reset_password_{user_id}"
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
                response = requests.get(f"{API_URL}/documents", headers=auth_headers(), timeout=60)
                documents = response.json()["documents"] if response.ok else []
            except Exception:
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
                    with st.expander(f"📁 {role_name} ({len(docs)})", expanded=False):
                        for doc in docs:
                            status_name = doc.get("status") or ("indexed" if doc.get("embedded") else "pending")
                            status_label = {
                                "indexed":  "✅ Indexed",
                                "pending":  "⏳ Queued",
                                "indexing": "🔄 Indexing",
                                "failed":   "⚠️ Failed",
                            }.get(status_name, status_name.title())

                            doc_col, retry_col, delete_col = st.columns([6, 1.4, 1.4])
                            with doc_col:
                                st.markdown(f"📄 **{doc['filename']}**  —  {status_label}")
                                if status_name == "failed" and doc.get("error_message"):
                                    st.caption(f"Error: {doc['error_message']}")
                            with retry_col:
                                if status_name == "failed" and st.button("Retry", key=f"retry_document_{doc['id']}"):
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

        # ─────────────────────────────────────────────────────
        # ── Tab 4: AI Evaluation (C-Level only)
        # ─────────────────────────────────────────────────────
        with tab4:
            section_header(
                "AI Performance",
                "Track answer quality, response speed, routing behaviour, and recent activity.",
                "C-Level only",
            )

            response = requests.get(f"{API_URL}/dashboard", headers=auth_headers(), timeout=60)

            if response.ok:
                dashboard = response.json()
                overview = dashboard["overview"]

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📊 Total Queries",   overview.get("total_queries", 0))
                col2.metric("🎯 Avg Confidence",  f'{overview.get("avg_confidence", 0):.1f}%')
                col3.metric("✅ Faithfulness",     f'{overview.get("avg_faithfulness", 0):.2f}')
                col4.metric("⚡ Avg Latency",      f'{overview.get("avg_latency", 0):.0f} ms')

                col5, col6, col7, col8 = st.columns(4)
                col5.metric("📚 Avg Sources",      f'{overview.get("avg_sources", 0):.1f}')
                col6.metric("👻 Hallucination",    f'{overview.get("hallucination_rate", 0):.1f}%')
                col7.metric("🗄 SQL / RAG",        f'{overview.get("sql_ratio", 0):.0f}% / {overview.get("rag_ratio", 0):.0f}%')
                col8.metric("🔁 Fallback Rate",    f'{overview.get("fallback_rate", 0):.1f}%')

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
                            st.line_chart(timeline.set_index("timestamp")[metrics_cols], height=220)

                    with chart_right:
                        st.caption("Query Routing Distribution")
                        route_counts = history_df["mode"].fillna("Unknown").value_counts()
                        st.bar_chart(route_counts, height=220)

                    st.subheader("Recent Conversations")
                    st.dataframe(history_df, use_container_width=True)
                else:
                    st.info("ℹ️ No evaluation logs yet. Ask a question in the Chat tab to generate live AI evaluation metrics.")
            else:
                try:
                    error = response.json().get("detail", "Unable to load dashboard.")
                except Exception:
                    error = response.text
                st.error(error)
