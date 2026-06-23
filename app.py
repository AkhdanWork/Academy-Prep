import pandas as pd
import streamlit as st
import base64
import html
import random
import time
import os
import json
from PIL import Image
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from database import (
    authenticate_user,
    create_remember_token,
    create_user,
    get_attempt_answers,
    get_attempt_sections,
    get_attempts,
    get_concept_performance,
    get_section_performance,
    get_user_by_remember_token,
    initialize_database,
    revoke_remember_token,
    save_attempt,
)
from firebase_service import FirebaseNotConfigured, sync_attempt, sync_user
from questions import QUESTIONS


ROOT_DIR = Path(__file__).resolve().parent
LOGO_PNG_PATH = ROOT_DIR / "assets" / "academy-prep-logo.png"
LOGO_SVG_PATH = ROOT_DIR / "assets" / "academy-prep-logo.svg"
with Image.open(LOGO_PNG_PATH) as logo_image:
    PAGE_ICON = logo_image.copy()
LOGO_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(
    LOGO_SVG_PATH.read_bytes()
).decode("ascii")


st.set_page_config(
    page_title="Swift Programming Prep",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)


TEST_DURATION_SECONDS = 120 * 60
SECTION_CONFIG = {
    "Section 1: Logic": {"label": "Logic", "quota": 40},
    "Section 2: Programming (Swift Focus)": {"label": "Swift", "quota": 10},
    "Section 7: Pseudocode Analysis": {"label": "Analisis Pseudocode", "quota": 15},
    "Section 6: Code Analysis": {"label": "Analisis Kode", "quota": 10},
    "Section 5: Code Completion": {"label": "Lengkapi Kode", "quota": 10},
    "Section 3: OOP": {"label": "OOP", "quota": 10},
    "Section 4: Bonus (Design/UX)": {"label": "Design & UX", "quota": 5},
}

# ── Translations ──────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "id": {
        "lang_label": "Bahasa",
        "nav_title": "Navigasi soal",
        "nav_copy": "Gunakan warna untuk melihat status setiap soal.",
        "legend_active": "Aktif",
        "legend_flagged": "Di-flag",
        "legend_answered": "Terjawab",
        "legend_empty": "Belum dijawab",
        "btn_submit": "Kumpulkan Jawaban",
        "btn_prev": "Sebelumnya",
        "btn_next": "Berikutnya",
        "btn_finish": "Selesaikan Tes",
        "btn_flag": "Flag Soal",
        "btn_unflag": "Hapus Flag",
        "btn_clear": "Kosongkan jawaban",
        "choice_label": "Pilih satu jawaban",
        "timer_label": "Sisa waktu",
        "status_active": "aktif",
        "status_flagged": "di-flag untuk ditinjau",
        "status_answered": "sudah dijawab",
        "status_unanswered": "belum dijawab",
        "status_active_and_flagged": "aktif dan di-flag",
        "soal_prefix": "Soal",
        "dari": "dari",
        "dijawab": "dijawab",
        "di_flag": "di-flag",
        "collapse": "▲",
        "expand": "▼",
    },
    "en": {
        "lang_label": "Language",
        "nav_title": "Question Navigator",
        "nav_copy": "Use colors to see the status of each question.",
        "legend_active": "Active",
        "legend_flagged": "Flagged",
        "legend_answered": "Answered",
        "legend_empty": "Unanswered",
        "btn_submit": "Submit Answers",
        "btn_prev": "Previous",
        "btn_next": "Next",
        "btn_finish": "Finish Test",
        "btn_flag": "Flag Question",
        "btn_unflag": "Remove Flag",
        "btn_clear": "Clear answer",
        "choice_label": "Choose one answer",
        "timer_label": "Time left",
        "status_active": "active",
        "status_flagged": "flagged for review",
        "status_answered": "answered",
        "status_unanswered": "unanswered",
        "status_active_and_flagged": "active and flagged",
        "soal_prefix": "Question",
        "dari": "of",
        "dijawab": "answered",
        "di_flag": "flagged",
        "collapse": "▲",
        "expand": "▼",
    },
}


def get_lang():
    """Return the current UI language ('id' or 'en')."""
    return st.session_state.get("ui_lang", "id")


def t(key):
    """Translate a key using the current language."""
    return TRANSLATIONS[get_lang()].get(key, key)


def q_text(item, field):
    """Return the EN version of a question field when EN is active, otherwise ID."""
    lang = get_lang()
    en_field = field + "_en"
    if lang == "en" and en_field in item:
        return item[en_field]
    return item.get(field, "")

st.markdown(
    """
    <style>
        :root {
            --surface: #121821;
            --surface-raised: #171f2b;
            --border: #2b3544;
            --muted: #9ba8b8;
            --accent: #ff5a62;
            --accent-soft: rgba(255, 90, 98, .12);
            --success: #35d0a0;
            --danger: #ff7185;
            --warning: #f6bf54;
        }

        .stApp { background: #0b1017; }
        header[data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"], #MainMenu, footer { display: none; }
        .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem; }

        h1, h2, h3 { letter-spacing: -.035em; }
        p, label, [data-testid="stMarkdownContainer"] { line-height: 1.6; }

        .brand-row {
            display: flex; align-items: center; gap: .75rem; margin-bottom: 2.2rem;
            color: #f8fafc; font-weight: 750; letter-spacing: -.01em;
        }
        .brand-logo {
            display: block; width: 40px; height: 40px; object-fit: contain;
            filter: drop-shadow(0 8px 18px rgba(255, 82, 104, .24));
        }
        .eyebrow {
            color: #ff7b81; font-size: .76rem; font-weight: 800;
            letter-spacing: .13em; text-transform: uppercase; margin-bottom: .5rem;
        }
        .hero-title { max-width: 760px; font-size: clamp(2.2rem, 5vw, 4rem); line-height: 1.05; margin: 0; }
        .hero-copy { max-width: 650px; color: var(--muted); font-size: 1.05rem; margin: 1.2rem 0 2rem; }
        .info-strip {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px;
            overflow: hidden; border: 1px solid var(--border); border-radius: 16px;
            background: var(--border); margin: 1.5rem 0 2rem;
        }
        .info-item { background: var(--surface); padding: 1.15rem 1.25rem; }
        .info-value { color: #f8fafc; font-size: 1.2rem; font-weight: 750; }
        .info-label { color: var(--muted); font-size: .82rem; margin-top: .2rem; }
        .rule-card {
            min-height: 138px; border: 1px solid var(--border); border-radius: 16px;
            padding: 1.25rem; background: var(--surface);
        }
        .rule-number { color: #ff7b81; font-size: .78rem; font-weight: 800; letter-spacing: .08em; }
        .rule-title { color: #f8fafc; font-weight: 720; margin: .45rem 0 .35rem; }
        .rule-copy { color: var(--muted); font-size: .88rem; line-height: 1.5; }

        .st-key-auth_card [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--border); border-radius: 22px;
            background: var(--surface); padding: clamp(1.2rem, 3vw, 2rem);
        }
        .auth-title { font-size: clamp(2.2rem, 5vw, 4.2rem); line-height: 1.04; margin: .3rem 0 1rem; }
        .auth-copy { color: var(--muted); max-width: 570px; font-size: 1.02rem; }
        .auth-points { display: grid; gap: .75rem; margin-top: 1.6rem; }
        .auth-point {
            display: flex; gap: .75rem; align-items: flex-start; color: #dbe3ed;
            padding: .85rem 1rem; border: 1px solid var(--border); border-radius: 12px;
            background: rgba(18, 24, 33, .7);
        }
        .auth-point-number { color: #ff7b81; font-weight: 800; }
        .account-note { color: var(--muted); font-size: .78rem; margin-top: .7rem; }

        .dashboard-header {
            display: flex; justify-content: space-between; align-items: end;
            gap: 1rem; margin: .5rem 0 1.6rem;
        }
        .dashboard-title { font-size: clamp(2rem, 4vw, 3.2rem); margin: 0; }
        .dashboard-copy { color: var(--muted); margin-top: .45rem; }
        .dashboard-grid {
            display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .8rem;
            margin: 1.1rem 0 1.5rem;
        }
        .dashboard-card {
            border: 1px solid var(--border); border-radius: 15px; background: var(--surface);
            padding: 1rem 1.1rem; min-height: 102px;
        }
        .dashboard-value { font-size: 1.55rem; font-weight: 800; color: #f8fafc; }
        .dashboard-label { color: var(--muted); font-size: .76rem; margin-top: .25rem; }
        .dashboard-detail { color: #c5cfdb; font-size: .75rem; margin-top: .3rem; }
        .evaluation-card {
            border: 1px solid var(--border); border-radius: 16px; background: var(--surface);
            padding: 1.15rem; min-height: 150px;
        }
        .evaluation-kicker { color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; }
        .evaluation-title { color: #f8fafc; font-weight: 760; margin: .35rem 0; }
        .evaluation-copy { color: var(--muted); font-size: .84rem; line-height: 1.55; }
        .trend-up { color: var(--success); }
        .trend-down { color: var(--danger); }
        .trend-flat { color: var(--warning); }

        .exam-topbar {
            display: flex; justify-content: space-between; align-items: center;
            gap: 1rem; padding-bottom: 1.25rem; border-bottom: 1px solid var(--border);
            margin-bottom: 1.4rem;
        }
        .exam-name { color: #f8fafc; font-size: 1.05rem; font-weight: 760; }
        .exam-meta { color: var(--muted); font-size: .82rem; margin-top: .1rem; }
        .timer-card {
            border: 1px solid var(--border); border-radius: 14px; padding: .72rem 1rem;
            background: var(--surface); min-width: 148px;
        }
        .timer-label { color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .09em; }
        .timer-value { color: #f8fafc; font-size: 1.25rem; font-weight: 760; font-variant-numeric: tabular-nums; }
        .timer-danger { border-color: rgba(255, 113, 133, .65); background: rgba(255, 113, 133, .08); }
        .timer-danger .timer-value { color: var(--danger); }

        .st-key-question_card [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--border); border-radius: 20px; padding: clamp(1.25rem, 3vw, 2rem);
            background: var(--surface); min-height: 460px;
        }
        .question-meta { color: var(--muted); font-size: .82rem; font-weight: 650; margin-bottom: .75rem; }
        .st-key-flag_current_question .stButton > button {
            min-height: 38px; padding: .35rem .8rem; font-size: .78rem;
            white-space: nowrap;
        }
        .question-title { font-size: clamp(1.2rem, 2.2vw, 1.65rem); line-height: 1.45; font-weight: 720; margin-bottom: 1.25rem; }
        .code-context {
            display: flex; flex-wrap: wrap; gap: .45rem; margin: -.35rem 0 1rem;
        }
        .code-badge {
            display: inline-flex; align-items: center; min-height: 28px; padding: .25rem .65rem;
            border: 1px solid var(--border); border-radius: 999px; color: #b9c4d2;
            background: #0e141d; font-size: .72rem; font-weight: 700;
        }
        [data-testid="stCodeBlock"] {
            border: 1px solid #303c4d; border-radius: 14px; overflow: hidden;
            margin-bottom: 1.1rem;
        }
        [data-testid="stCodeBlock"] pre { font-size: .9rem; line-height: 1.65; overflow-x: auto; }
        .choice-label { color: var(--muted); font-size: .82rem; margin-bottom: .35rem; }

        div[role="radiogroup"] { gap: .65rem; }
        div[role="radiogroup"] > label {
            min-height: 54px; padding: .85rem 1rem; border: 1px solid var(--border);
            border-radius: 12px; background: #0f151e; cursor: pointer;
            transition: border-color 180ms ease, background 180ms ease;
        }
        div[role="radiogroup"] > label:hover { border-color: #667386; background: #141c27; }
        div[role="radiogroup"] > label:has(input:checked) {
            border-color: var(--accent); background: var(--accent-soft);
        }
        div[role="radiogroup"] > label p { font-size: .96rem; }

        .st-key-question_palette [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--border); border-radius: 20px; padding: 1.25rem;
            background: var(--surface); position: sticky; top: 1.25rem;
        }
        .palette-title { color: #f8fafc; font-weight: 750; }
        .palette-copy { color: var(--muted); font-size: .78rem; margin: .2rem 0 .9rem; }
        .palette-legend {
            display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .45rem .55rem; margin: .75rem 0 1rem;
        }
        .legend-item { display: flex; align-items: center; gap: .4rem; color: var(--muted); font-size: .68rem; }
        .legend-swatch { width: 13px; height: 13px; border-radius: 4px; border: 1px solid #455164; flex: 0 0 auto; }
        .legend-active { background: var(--accent); border-color: var(--accent); }
        .legend-flagged { background: var(--warning); border-color: var(--warning); }
        .legend-answered { background: #3b4655; border-color: #566274; }
        .legend-empty { background: #0f151e; }
        .palette-section { color: var(--muted); font-size: .72rem; font-weight: 750; margin: .8rem 0 .35rem; }
        .st-key-question_palette .stButton > button {
            min-width: 0; width: 100%; min-height: 36px; padding: .1rem 0;
            font-size: .65rem; white-space: nowrap; line-height: 1; margin: 0;
        }
        .st-key-question_palette .stButton > button p {
            white-space: nowrap; overflow: hidden; text-overflow: clip;
            font-size: .65rem; margin: 0; padding: 0;
        }
        .palette-section-header {
            display: flex; justify-content: space-between; align-items: center;
            cursor: pointer; user-select: none; padding: .4rem .2rem;
            border-radius: 8px; transition: background 150ms ease;
        }
        .palette-section-header:hover { background: rgba(255,255,255,.04); }
        .palette-section-label { color: var(--muted); font-size: .72rem; font-weight: 750; }
        .palette-section-toggle { color: var(--muted); font-size: .65rem; transition: transform 200ms; }
        .lang-switcher {
            display: flex; gap: .4rem; align-items: center; margin-bottom: .6rem;
        }
        .lang-btn {
            display: inline-flex; align-items: center; gap: .3rem;
            padding: .3rem .6rem; border-radius: 8px; font-size: .72rem; font-weight: 700;
            cursor: pointer; border: 1px solid var(--border); background: transparent;
            color: var(--muted); transition: all 150ms ease;
        }
        .lang-btn:hover { border-color: #667386; color: #f8fafc; }
        .lang-btn.lang-active { border-color: var(--accent); color: #f8fafc; background: var(--accent-soft); }

        .progress-copy { display: flex; justify-content: space-between; color: var(--muted); font-size: .78rem; margin: .15rem 0 .35rem; }
        div[data-testid="stProgress"] > div > div { background-color: var(--accent); }
        .stButton > button { min-height: 44px; border-radius: 11px; font-weight: 680; cursor: pointer; }
        .stButton > button:focus-visible { outline: 3px solid rgba(255, 90, 98, .35); outline-offset: 2px; }

        .st-key-clear_answer_nav button {
            width: 100%;
            background: transparent !important;
            border: 1px solid rgba(255, 113, 133, .55) !important;
            color: #ff7185 !important;
            font-size: .85rem !important;
            transition: border-color 180ms ease, background 180ms ease;
        }
        .st-key-clear_answer_nav button:hover {
            background: rgba(255, 113, 133, .1) !important;
            border-color: #ff7185 !important;
        }

        .result-hero {
            border: 1px solid var(--border); border-radius: 22px; padding: clamp(1.4rem, 4vw, 2.3rem);
            background: linear-gradient(135deg, #171f2b, #111720); margin-bottom: 1.2rem;
        }
        .result-grid { display: grid; grid-template-columns: minmax(170px, .65fr) 2fr; gap: 2rem; align-items: center; }
        .score-ring {
            width: 150px; height: 150px; border-radius: 50%; display: grid; place-items: center;
            margin: auto; position: relative;
        }
        .score-ring::after { content: ''; position: absolute; inset: 11px; border-radius: 50%; background: #151d28; }
        .score-content { position: relative; z-index: 1; text-align: center; }
        .score-number { color: #f8fafc; font-size: 2rem; font-weight: 800; line-height: 1; }
        .score-caption { color: var(--muted); font-size: .72rem; margin-top: .25rem; }
        .result-title { font-size: clamp(1.6rem, 3vw, 2.4rem); margin: .25rem 0 .6rem; }
        .result-copy { color: var(--muted); max-width: 620px; }
        .metric-card { border: 1px solid var(--border); background: var(--surface); border-radius: 14px; padding: 1rem; }
        .metric-value { color: #f8fafc; font-size: 1.35rem; font-weight: 760; }
        .metric-label { color: var(--muted); font-size: .76rem; margin-top: .15rem; }
        .status-good { color: var(--success); }
        .status-bad { color: var(--danger); }
        .status-empty { color: var(--warning); }
        .answer-box { border-left: 3px solid var(--border); padding: .6rem .85rem; background: #0f151e; border-radius: 0 10px 10px 0; }
        .answer-box.correct { border-left-color: var(--success); }
        .answer-box.wrong { border-left-color: var(--danger); }
        .answer-label { color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; }
        .answer-value { color: #f8fafc; margin-top: .18rem; }
        .answer-options { display: grid; gap: .5rem; margin-top: .75rem; }
        .answer-option {
            border: 1px solid var(--border); border-radius: 11px; padding: .7rem .85rem;
            background: #0f151e; color: #dce4ee; line-height: 1.45;
        }
        .answer-option.correct { border-color: rgba(53, 208, 160, .75); background: rgba(53, 208, 160, .08); }
        .answer-option.selected.wrong { border-color: rgba(255, 113, 133, .75); background: rgba(255, 113, 133, .08); }
        .option-tags { display: flex; flex-wrap: wrap; gap: .35rem; margin-bottom: .35rem; }
        .option-tag {
            display: inline-flex; align-items: center; min-height: 22px; padding: .15rem .45rem;
            border-radius: 999px; background: #253041; color: #cbd5e1; font-size: .66rem;
            font-weight: 750; text-transform: uppercase; letter-spacing: .05em;
        }
        .option-tag.correct { background: rgba(53, 208, 160, .16); color: var(--success); }
        .option-tag.wrong { background: rgba(255, 113, 133, .16); color: var(--danger); }
        .explanation { margin-top: .8rem; padding: .9rem 1rem; border-radius: 11px; background: rgba(83, 120, 255, .08); border: 1px solid rgba(83, 120, 255, .2); }
        .explanation-title { color: #91a8ff; font-size: .76rem; font-weight: 760; margin-bottom: .25rem; }

        @media (max-width: 768px) {
            .block-container { padding: 1.1rem .9rem 3rem; }
            .info-strip { grid-template-columns: 1fr; }
            .dashboard-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .dashboard-header { align-items: flex-start; }
            .exam-topbar { align-items: flex-start; }
            .timer-card { min-width: 126px; }
            .result-grid { grid-template-columns: 1fr; text-align: center; gap: 1rem; }
            .result-copy { margin-inline: auto; }
            .st-key-question_card [data-testid="stVerticalBlockBorderWrapper"] { min-height: auto; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def initialize_storage():
    initialize_database()
    return True


def validate_question_bank():
    errors = []
    for section, items in QUESTIONS.items():
        for position, item in enumerate(items, start=1):
            options = item.get("options", [])
            if len(options) != 4:
                errors.append(f"{section} soal {position}: harus memiliki 4 opsi")
            if len(options) != len(set(options)):
                errors.append(f"{section} soal {position}: opsi jawaban duplikat")
            if item.get("answer") not in options:
                errors.append(f"{section} soal {position}: jawaban tidak ada di opsi")
    return errors


def format_duration(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def build_test_questions():
    test_questions = []
    for section, config in SECTION_CONFIG.items():
        section_questions = QUESTIONS.get(section, [])
        sample_size = min(config["quota"], len(section_questions))
        for section_number, item in enumerate(random.sample(section_questions, sample_size), start=1):
            prepared_item = dict(item)
            # Shuffle the ID options; EN options keep the same order relative to ID
            shuffled_order = random.sample(range(len(item["options"])), len(item["options"]))
            prepared_item["options"] = [item["options"][i] for i in shuffled_order]
            if "options_en" in item:
                prepared_item["options_en"] = [item["options_en"][i] for i in shuffled_order]
                # Also re-map answer_en to match shuffled options_en order
                prepared_item["answer_en"] = item.get("answer_en", item.get("answer", ""))
            test_questions.append(
                {
                    "section": section,
                    "section_label": config["label"],
                    "section_number": section_number,
                    "item": prepared_item,
                }
            )
    return test_questions


def start_test():
    st.session_state.test_id = st.session_state.get("test_id", 0) + 1
    st.session_state.test_questions = build_test_questions()
    st.session_state.answers = {}
    st.session_state.flagged_questions = set()
    st.session_state.current_question = 0
    st.session_state.started_at = time.time()
    st.session_state.finished_at = None
    st.session_state.finish_reason = None
    st.session_state.attempt_id = None
    st.session_state.persistence_error = None
    st.session_state.firebase_error = None
    st.session_state.screen = "exam"


def return_to_intro():
    st.session_state.screen = "intro"


def return_to_dashboard():
    st.session_state.screen = "dashboard"


def save_active_test():
    if not st.session_state.get("user") or st.session_state.get("screen") != "exam":
        return
    user_id = st.session_state.user["id"]
    state = {
        "test_id": st.session_state.get("test_id"),
        "test_questions": st.session_state.get("test_questions"),
        "answers": st.session_state.get("answers", {}),
        "flagged_questions": list(st.session_state.get("flagged_questions", set())),
        "current_question": st.session_state.get("current_question", 0),
        "started_at": st.session_state.get("started_at"),
    }
    os.makedirs("data", exist_ok=True)
    with open(f"data/active_test_{user_id}.json", "w", encoding="utf-8") as f:
        json.dump(state, f)


def load_active_test():
    if not st.session_state.get("user"):
        return False
    user_id = st.session_state.user["id"]
    file_path = f"data/active_test_{user_id}.json"
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            st.session_state.test_id = state.get("test_id", 1)
            st.session_state.test_questions = state.get("test_questions", [])
            st.session_state.answers = {int(k): v for k, v in state.get("answers", {}).items()}
            st.session_state.flagged_questions = set(state.get("flagged_questions", []))
            st.session_state.current_question = state.get("current_question", 0)
            st.session_state.started_at = state.get("started_at", time.time())
            st.session_state.finished_at = None
            st.session_state.finish_reason = None
            st.session_state.attempt_id = None
            st.session_state.persistence_error = None
            st.session_state.firebase_error = None
            return True
        except Exception:
            pass
    return False


def clear_active_test():
    if not st.session_state.get("user"):
        return
    user_id = st.session_state.user["id"]
    file_path = f"data/active_test_{user_id}.json"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass


def set_authenticated_user(user):
    st.session_state.user = user
    if load_active_test():
        st.session_state.screen = "exam"
    else:
        st.session_state.screen = "dashboard"
    st.session_state.login_failures = 0
    st.session_state.login_locked_until = 0


def logout_user():
    remember_token = st.session_state.get("remember_token") or get_remember_token()
    revoke_remember_token(remember_token)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    clear_remember_token()
    st.session_state.screen = "auth"


def get_remember_token():
    token = st.query_params.get("remember")
    if isinstance(token, list):
        return token[0] if token else None
    return token


def set_remember_token(token):
    st.session_state.remember_token = token
    st.query_params["remember"] = token


def clear_remember_token():
    st.session_state.pop("remember_token", None)
    if "remember" in st.query_params:
        del st.query_params["remember"]


def restore_remembered_user():
    if st.session_state.get("user"):
        return False

    remember_token = get_remember_token()
    user = get_user_by_remember_token(remember_token)
    if not user:
        clear_remember_token()
        return False

    st.session_state.remember_token = remember_token
    set_authenticated_user(user)
    return True


def sync_local_user_to_firebase(user):
    sync_user(user)
    attempts = get_attempts(user["id"])
    for attempt in attempts:
        summary = {
            "score": attempt["score"],
            "correct": attempt["correct"],
            "incorrect": attempt["incorrect"],
            "unanswered": attempt["unanswered"],
            "total": attempt["total"],
            "duration_seconds": attempt["duration_seconds"],
            "finish_reason": attempt["finish_reason"],
            "started_at": attempt["started_at"],
            "completed_at": attempt["completed_at"],
        }
        sync_attempt(
            user,
            attempt["id"],
            attempt["session_key"],
            summary,
            get_attempt_sections(user["id"], attempt["id"]),
            get_attempt_answers(user["id"], attempt["id"]),
        )


def try_sync_local_user_to_firebase(user):
    if st.session_state.get("firebase_synced_user_id") == user["id"]:
        return

    try:
        sync_local_user_to_firebase(user)
        st.session_state.firebase_error = None
        st.session_state.firebase_synced_user_id = user["id"]
    except FirebaseNotConfigured:
        st.session_state.firebase_error = None
    except Exception as error:
        st.session_state.firebase_error = f"Firebase sync gagal: {error}"


def persist_current_attempt():
    if st.session_state.get("attempt_id") or not st.session_state.get("user"):
        return

    correct, total, section_results = calculate_results()
    unanswered = total - len(st.session_state.answers)
    incorrect = total - correct - unanswered
    finished_at = st.session_state.finished_at or time.time()
    duration_seconds = max(0, int(finished_at - st.session_state.started_at))
    summary = {
        "score": (correct / total * 100) if total else 0,
        "correct": correct,
        "incorrect": incorrect,
        "unanswered": unanswered,
        "total": total,
        "duration_seconds": duration_seconds,
        "finish_reason": st.session_state.finish_reason or "submitted",
        "started_at": datetime.fromtimestamp(
            st.session_state.started_at, tz=timezone.utc
        ).isoformat(),
        "completed_at": datetime.fromtimestamp(finished_at, tz=timezone.utc).isoformat(),
    }
    answer_results = []
    for index, question_data in enumerate(st.session_state.test_questions):
        question = question_data["item"]
        user_answer = st.session_state.answers.get(index)
        answer_results.append(
            {
                "position": index + 1,
                "section": question_data["section_label"],
                "concept": question.get("concept"),
                "difficulty": question.get("difficulty"),
                "question": question["q"],
                "code": question.get("code"),
                "language": question.get("language", "swift"),
                "options": question.get("options", []),
                "user_answer": user_answer,
                "correct_answer": question["answer"],
                "is_correct": user_answer == question["answer"],
                "explanation": get_explanation(question),
            }
        )

    session_key = (
        f'{st.session_state.user["id"]}:'
        f'{st.session_state.test_id}:{st.session_state.started_at:.6f}'
    )
    try:
        st.session_state.attempt_id = save_attempt(
            st.session_state.user["id"],
            session_key,
            summary,
            dict(section_results),
            answer_results,
        )
        try:
            sync_attempt(
                st.session_state.user,
                st.session_state.attempt_id,
                session_key,
                summary,
                dict(section_results),
                answer_results,
            )
        except FirebaseNotConfigured as error:
            st.session_state.firebase_error = str(error)
        except Exception as error:
            st.session_state.firebase_error = f"Firebase sync gagal: {error}"
    except Exception as error:
        st.session_state.persistence_error = str(error)


def finish_test(reason="submitted"):
    if st.session_state.get("screen") != "exam":
        return
    st.session_state.finished_at = time.time()
    st.session_state.finish_reason = reason
    persist_current_attempt()
    clear_active_test()
    st.session_state.screen = "results"


def go_to_question(index):
    st.session_state.current_question = index


def move_question(offset):
    total = len(st.session_state.test_questions)
    st.session_state.current_question = min(
        max(st.session_state.current_question + offset, 0), total - 1
    )


def clear_answer(index, widget_key):
    st.session_state.answers.pop(index, None)
    st.session_state.pop(widget_key, None)


def toggle_question_flag(index):
    flagged_questions = set(st.session_state.get("flagged_questions", set()))
    if index in flagged_questions:
        flagged_questions.remove(index)
    else:
        flagged_questions.add(index)
    st.session_state.flagged_questions = flagged_questions


def render_navigation_status_styles(total, current_index):
    answered_questions = st.session_state.answers
    flagged_questions = st.session_state.flagged_questions
    rules = []
    for index in range(total):
        selector = f".st-key-nav_{st.session_state.test_id}_{index} button"
        if index == current_index:
            rule = (
                "background:#ff4f57!important;border-color:#ff4f57!important;"
                "color:#ffffff!important;"
            )
            if index in flagged_questions:
                rule += "box-shadow:0 0 0 3px #f6bf54!important;"
        elif index in flagged_questions:
            rule = (
                "background:#f6bf54!important;border-color:#f6bf54!important;"
                "color:#201806!important;font-weight:800!important;"
            )
        elif index in answered_questions:
            rule = (
                "background:#3b4655!important;border-color:#566274!important;"
                "color:#f8fafc!important;"
            )
        else:
            rule = (
                "background:#0f151e!important;border-color:#354052!important;"
                "color:#dce4ee!important;"
            )
        rules.append(f"{selector}{{{rule}}}")
    st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)


def get_explanation(question):
    if question.get("explanation"):
        return question["explanation"]

    text = question["q"].lower()
    answer = question["answer"]
    if "pola" in text or "angka selanjutnya" in text:
        return f"Amati perubahan antarsuku secara berurutan, lalu terapkan pola yang sama pada suku berikutnya. Hasilnya adalah {answer}."
    if "berapa" in text and any(word in text for word in ("harga", "umur", "waktu", "km", "jam")):
        return f"Tuliskan informasi yang diketahui, gunakan operasi hitung yang sesuai, lalu cocokkan hasilnya dengan pilihan. Hasil akhirnya {answer}."
    if text.startswith("jika semua") or "maka" in text:
        return f"Ubah setiap premis menjadi hubungan sederhana dan ambil hanya kesimpulan yang pasti didukung. Jawaban yang valid adalah {answer}."
    if "output" in text:
        return f"Telusuri kode dari kiri ke kanan dan perhatikan tipe datanya. Output yang dihasilkan adalah {answer}."
    return f"Identifikasi kata kunci konsep pada soal, lalu eliminasi opsi yang definisi atau perilakunya tidak sesuai. Pilihan yang tepat adalah {answer}."


def answer_status(user_answer, correct_answer, is_correct=None):
    lang = get_lang()
    if user_answer is None:
        return ("Empty" if lang == "en" else "Kosong"), "status-empty"
    if is_correct is None:
        is_correct = user_answer == correct_answer
    if bool(is_correct):
        return ("Correct" if lang == "en" else "Benar"), "status-good"
    return ("Wrong" if lang == "en" else "Salah"), "status-bad"


def format_answer_value(value):
    lang = get_lang()
    if value is None:
        return "Not answered" if lang == "en" else "Tidak dijawab"
    if value == "":
        return "(empty option)" if lang == "en" else "(opsi kosong)"
    return str(value)


def build_current_review_items():
    review_items = []
    lang = get_lang()
    for index, question_data in enumerate(st.session_state.test_questions):
        question = question_data["item"]
        # Use language-aware fields
        q = q_text(question, "q")
        options = q_text(question, "options") if isinstance(q_text(question, "options"), list) else question.get("options", [])
        correct_answer = q_text(question, "answer")
        user_answer_raw = st.session_state.answers.get(index)
        # Map user_answer from ID answer to EN answer for display
        if lang == "en" and user_answer_raw is not None:
            id_options = question.get("options", [])
            en_options = question.get("options_en", id_options)
            try:
                idx = id_options.index(user_answer_raw)
                user_answer = en_options[idx]
            except (ValueError, IndexError):
                user_answer = user_answer_raw
        else:
            user_answer = user_answer_raw
        review_items.append(
            {
                "position": index + 1,
                "section": question_data["section_label"],
                "concept": question.get("concept"),
                "difficulty": question.get("difficulty"),
                "question": q,
                "code": question.get("code"),
                "language": question.get("language", "swift"),
                "options": options,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": user_answer_raw == question["answer"],
                "explanation": q_text(question, "explanation") if question.get("explanation") else get_explanation(question),
            }
        )
    return review_items


def render_answer_options(options, user_answer, correct_answer):
    if not options:
        return

    option_blocks = []
    for option in options:
        classes = ["answer-option"]
        tags = []
        if option == correct_answer:
            classes.append("correct")
            key_label = "Answer Key" if get_lang() == "en" else "Kunci"
            tags.append(f'<span class="option-tag correct">{key_label}</span>')
        if user_answer is not None and option == user_answer:
            classes.append("selected")
            your_label = "Your Answer" if get_lang() == "en" else "Jawaban Anda"
            if option != correct_answer:
                classes.append("wrong")
                tags.append(f'<span class="option-tag wrong">{your_label}</span>')
            else:
                tags.append(f'<span class="option-tag correct">{your_label}</span>')
        tag_markup = (
            f'<div class="option-tags">{"".join(tags)}</div>' if tags else ""
        )
        option_blocks.append(
            f"""
            <div class="{' '.join(classes)}">
                {tag_markup}
                <div>{html.escape(format_answer_value(option))}</div>
            </div>
            """
        )

    st.html(
        f'<div class="answer-options">{"".join(option_blocks)}</div>'
    )


def render_answer_review(review_items, filter_key):
    lang = get_lang()
    if lang == "en":
        filter_options = ["All", "Wrong", "Correct", "Empty"]
        filter_all = "All"
    else:
        filter_options = ["Semua", "Salah", "Benar", "Kosong"]
        filter_all = "Semua"
    review_filter = st.radio(
        "Filter review",
        filter_options,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key=filter_key,
    )

    visible_count = 0
    for fallback_index, item in enumerate(review_items, start=1):
        user_answer = item.get("user_answer")
        correct_answer = item.get("correct_answer")
        status, status_class = answer_status(
            user_answer, correct_answer, item.get("is_correct")
        )

        if review_filter != filter_all and review_filter != status:
            continue

        visible_count += 1
        position = item.get("position") or fallback_index
        question_text = item.get("question", "")
        with st.expander(f"{position}. [{status}] {question_text}", expanded=False):
            meta_parts = [
                html.escape(str(value))
                for value in (
                    item.get("section"),
                    item.get("difficulty"),
                    item.get("concept"),
                )
                if value
            ]
            meta = " &middot; ".join(meta_parts)
            st.html(
                f'<div class="question-meta">{meta} &middot; <span class="{status_class}">{status}</span></div>'
            )
            if item.get("code"):
                st.code(
                    item["code"],
                    language=item.get("language") or "swift",
                    line_numbers=True,
                )

            render_answer_options(
                item.get("options", []), user_answer, correct_answer
            )

            answer_columns = st.columns(2)
            with answer_columns[0]:
                answer_class = "correct" if status in ("Benar", "Correct") else "wrong"
                user_label = "Your Answer" if get_lang() == "en" else "Jawaban Anda"
                st.html(
                    f"""
                    <div class="answer-box {answer_class}">
                        <div class="answer-label">{user_label}</div>
                        <div class="answer-value">{html.escape(format_answer_value(user_answer))}</div>
                    </div>
                    """
                )
            with answer_columns[1]:
                correct_label = "Correct Answer" if get_lang() == "en" else "Jawaban benar"
                st.html(
                    f"""
                    <div class="answer-box correct">
                        <div class="answer-label">{correct_label}</div>
                        <div class="answer-value">{html.escape(format_answer_value(correct_answer))}</div>
                    </div>
                    """
                )

            explanation = item.get("explanation")
            if explanation:
                explain_title = "How to answer" if get_lang() == "en" else "Cara menjawab"
                st.html(
                    f"""
                    <div class="explanation">
                        <div class="explanation-title">{explain_title}</div>
                        <div>{html.escape(str(explanation))}</div>
                    </div>
                    """
                )

    if visible_count == 0:
        st.caption("Tidak ada soal pada filter ini.")


def calculate_results():
    total = len(st.session_state.test_questions)
    correct = 0
    section_results = defaultdict(lambda: {"correct": 0, "total": 0})

    for index, question_data in enumerate(st.session_state.test_questions):
        user_answer = st.session_state.answers.get(index)
        is_correct = user_answer == question_data["item"]["answer"]
        correct += int(is_correct)
        section = question_data["section_label"]
        section_results[section]["correct"] += int(is_correct)
        section_results[section]["total"] += 1

    return correct, total, section_results


def render_brand():
    st.markdown(
        f"""
        <div class="brand-row">
            <img class="brand-logo" src="{LOGO_DATA_URI}" alt="Academy Prep" />
            <div>Academy Prep</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_user_navigation(show_dashboard=True):
    brand_column, dashboard_column, logout_column = st.columns(
        [5, 1, 1], vertical_alignment="center"
    )
    with brand_column:
        render_brand()
    with dashboard_column:
        if show_dashboard and st.button(
            "Dashboard", width="stretch", key="go_to_dashboard"
        ):
            return_to_dashboard()
            st.rerun()
    with logout_column:
        if st.button("Keluar", width="stretch", key="logout_account"):
            logout_user()
            st.rerun()


def render_auth():
    render_brand()
    marketing, auth_column = st.columns([1.25, 1], gap="large")
    with marketing:
        st.markdown('<div class="eyebrow">Progress Learning</div>', unsafe_allow_html=True)
        st.markdown(
            '<h1 class="auth-title">Belajar lebih terarah dari setiap tes.</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <p class="auth-copy">
                Simpan seluruh hasil latihan, lihat apakah nilai meningkat, dan dapatkan
                evaluasi berdasarkan section serta konsep yang masih perlu diperdalam.
            </p>
            <div class="auth-points">
                <div class="auth-point"><span class="auth-point-number">01</span><span>Riwayat nilai tersimpan otomatis setelah tes selesai.</span></div>
                <div class="auth-point"><span class="auth-point-number">02</span><span>Grafik membandingkan progres dari tes pertama hingga terbaru.</span></div>
                <div class="auth-point"><span class="auth-point-number">03</span><span>Evaluasi menunjukkan kekuatan, kelemahan, dan fokus belajar berikutnya.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with auth_column:
        with st.container(key="auth_card", border=True):
            login_tab, register_tab = st.tabs(["Masuk", "Daftar akun"])
            with login_tab:
                st.subheader("Masuk ke akun")
                st.caption("Lanjutkan progres latihan Anda.")
                locked_until = st.session_state.get("login_locked_until", 0)
                remaining_lock = max(0, int(locked_until - time.time()))
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="nama@email.com")
                    password = st.text_input("Password", type="password")
                    remember_me = st.checkbox(
                        "Ingat saya di perangkat ini",
                        value=True,
                        help="Jangan aktifkan di perangkat publik.",
                    )
                    submitted = st.form_submit_button(
                        "Masuk", type="primary", width="stretch",
                        disabled=remaining_lock > 0,
                    )

                if remaining_lock > 0:
                    st.warning(f"Terlalu banyak percobaan. Coba lagi dalam {remaining_lock} detik.")
                elif submitted:
                    user = authenticate_user(email, password)
                    if user:
                        set_authenticated_user(user)
                        if remember_me:
                            set_remember_token(create_remember_token(user["id"]))
                        else:
                            clear_remember_token()
                        try_sync_local_user_to_firebase(user)
                        st.rerun()
                    else:
                        failures = st.session_state.get("login_failures", 0) + 1
                        st.session_state.login_failures = failures
                        if failures >= 5:
                            st.session_state.login_locked_until = time.time() + 30
                            st.session_state.login_failures = 0
                        st.error("Email atau password tidak sesuai.")

            with register_tab:
                st.subheader("Buat akun baru")
                st.caption("Hasil tes akan tersimpan pada akun ini.")
                with st.form("register_form"):
                    name = st.text_input("Nama lengkap", placeholder="Nama Anda")
                    register_email = st.text_input(
                        "Email", placeholder="nama@email.com", key="register_email"
                    )
                    register_password = st.text_input(
                        "Password",
                        type="password",
                        help="Minimal 8 karakter serta memiliki huruf dan angka.",
                        key="register_password",
                    )
                    confirmation = st.text_input(
                        "Ulangi password", type="password", key="password_confirmation"
                    )
                    registered = st.form_submit_button(
                        "Daftar akun", type="primary", width="stretch"
                    )

                if registered:
                    if register_password != confirmation:
                        st.error("Konfirmasi password tidak sama.")
                    else:
                        user, error = create_user(name, register_email, register_password)
                        if error:
                            st.error(error)
                        else:
                            set_authenticated_user(user)
                            # Auto remember on registration
                            set_remember_token(create_remember_token(user["id"]))
                            try_sync_local_user_to_firebase(user)
                            st.rerun()
                st.markdown(
                    '<div class="account-note">Password disimpan sebagai hash PBKDF2, bukan teks asli.</div>',
                    unsafe_allow_html=True,
                )


def _format_attempt_date(value):
    parsed = datetime.fromisoformat(value)
    return parsed.astimezone(ZoneInfo("Asia/Jakarta")).strftime("%d %b %Y, %H:%M")


def _section_recommendation(section):
    recommendations = {
        "Logic": "Latih pola angka, relasi premis, dan soal hitung dengan menuliskan langkah sebelum memilih jawaban.",
        "Swift": "Ulangi fundamental tipe data, collection, optional, function, dan kontrol alur Swift.",
        "Analisis Kode": "Trace kode baris demi baris. Catat perubahan nilai, urutan eksekusi, serta tipe setiap ekspresi.",
        "Analisis Pseudocode": "Buat tabel trace untuk setiap iterasi atau pemanggilan rekursif sebelum menentukan output algoritma.",
        "Lengkapi Kode": "Biasakan menulis snippet kecil tanpa autocomplete dan pahami kontrak setiap API Swift.",
        "OOP": "Perkuat value/reference semantics, protocol, inheritance, encapsulation, dan composition.",
        "Design & UX": "Pelajari kembali HIG, accessibility, hierarchy, consistency, dan feedback pengguna.",
    }
    return recommendations.get(section, "Tinjau kembali pembahasan jawaban yang salah pada section ini.")


def render_dashboard():
    user = st.session_state.user
    user_name = html.escape(user["name"])
    render_user_navigation(show_dashboard=False)
    try_sync_local_user_to_firebase(user)

    header_content, start_column = st.columns([4, 1], vertical_alignment="bottom")
    with header_content:
        st.markdown('<div class="eyebrow">Learning Dashboard</div>', unsafe_allow_html=True)
        st.markdown(
            f'<h1 class="dashboard-title">Halo, {user_name}</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="dashboard-copy">Pantau perkembangan dan tentukan fokus latihan berikutnya.</div>',
            unsafe_allow_html=True,
        )
    with start_column:
        if st.button("Mulai Tes Baru", type="primary", width="stretch"):
            return_to_intro()
            st.rerun()

    if st.session_state.get("firebase_error"):
        st.warning(st.session_state.firebase_error)

    attempts = get_attempts(user["id"])
    section_performance = get_section_performance(user["id"])
    concept_performance = get_concept_performance(user["id"])

    if not attempts:
        st.markdown(
            """
            <div class="result-hero">
                <div class="eyebrow">Belum Ada Riwayat</div>
                <h2 class="result-title">Tes pertama akan menjadi baseline Anda.</h2>
                <div class="result-copy">Setelah selesai, dashboard akan menampilkan grafik, perbandingan nilai, dan evaluasi personal.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("Klik “Mulai Tes Baru” untuk membuat baseline progres pertama.")
        return

    scores = [attempt["score"] for attempt in attempts]
    latest_score = scores[-1]
    average_score = sum(scores) / len(scores)
    best_score = max(scores)
    if len(scores) >= 2:
        score_delta = scores[-1] - scores[-2]
        if score_delta > 0:
            trend_text = f"Naik {score_delta:+.1f} poin"
            trend_class = "trend-up"
        elif score_delta < 0:
            trend_text = f"Turun {score_delta:.1f} poin"
            trend_class = "trend-down"
        else:
            trend_text = "Tidak berubah"
            trend_class = "trend-flat"
    else:
        score_delta = None
        trend_text = "Tes pertama"
        trend_class = "trend-flat"

    metrics = [
        (f"{latest_score:.0f}", "Nilai terbaru", trend_text, trend_class),
        (f"{average_score:.0f}", "Rata-rata nilai", f"Dari {len(attempts)} tes", ""),
        (f"{best_score:.0f}", "Nilai terbaik", "Personal best", "trend-up"),
        (str(len(attempts)), "Tes diselesaikan", f"Terakhir {_format_attempt_date(attempts[-1]['completed_at'])}", ""),
    ]
    metric_cards = "".join(
        (
            f'<div class="dashboard-card">'
            f'<div class="dashboard-value">{value}</div>'
            f'<div class="dashboard-label">{label}</div>'
            f'<div class="dashboard-detail {detail_class}">{detail}</div>'
            f"</div>"
        )
        for value, label, detail, detail_class in metrics
    )
    st.markdown(
        f'<div class="dashboard-grid">{metric_cards}</div>',
        unsafe_allow_html=True,
    )

    progress_tab, evaluation_tab, history_tab = st.tabs(
        ["Progres", "Evaluasi", "Riwayat Tes"]
    )
    with progress_tab:
        st.subheader("Perkembangan nilai")
        chart_data = pd.DataFrame(
            {
                "Tes": list(range(1, len(attempts) + 1)),
                "Nilai": scores,
                "Target": [75] * len(attempts),
            }
        )
        st.line_chart(
            chart_data,
            x="Tes",
            y=["Nilai", "Target"],
            x_label="Percobaan",
            y_label="Nilai",
            color=["#FF5A62", "#667386"],
        )

        st.subheader("Performa per section")
        section_chart = pd.DataFrame(
            {
                "Section": [row["section"] for row in section_performance],
                "Akurasi": [row["correct"] / row["total"] * 100 for row in section_performance],
            }
        )
        st.bar_chart(
            section_chart,
            x="Section",
            y="Akurasi",
            y_label="Akurasi (%)",
            color="#FF5A62",
        )

    with evaluation_tab:
        st.subheader("Evaluasi belajar")
        strongest = section_performance[0]
        weakest = section_performance[-1]
        strongest_score = strongest["correct"] / strongest["total"] * 100
        weakest_score = weakest["correct"] / weakest["total"] * 100

        evaluation_columns = st.columns(3)
        evaluations = [
            (
                "Kekuatan utama",
                f'{strongest["section"]} · {strongest_score:.0f}%',
                "Pertahankan kemampuan ini sambil meningkatkan konsistensi pada section lain.",
            ),
            (
                "Prioritas belajar",
                f'{weakest["section"]} · {weakest_score:.0f}%',
                _section_recommendation(weakest["section"]),
            ),
            (
                "Arah progres",
                trend_text,
                "Bandingkan minimal tiga tes untuk melihat tren yang lebih representatif."
                if len(attempts) < 3
                else "Gunakan tren ini bersama akurasi per section, bukan nilai total saja.",
            ),
        ]
        for column, (kicker, title, copy) in zip(evaluation_columns, evaluations):
            with column:
                st.markdown(
                    f"""
                    <div class="evaluation-card">
                        <div class="evaluation-kicker">{kicker}</div>
                        <div class="evaluation-title">{title}</div>
                        <div class="evaluation-copy">{copy}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("")
        st.subheader("Konsep yang perlu ditinjau")
        if concept_performance:
            concept_rows = []
            for row in concept_performance[:8]:
                accuracy = row["correct"] / row["total"] * 100
                concept_rows.append(
                    {
                        "Konsep": row["concept"],
                        "Benar": f'{row["correct"]}/{row["total"]}',
                        "Akurasi": f"{accuracy:.0f}%",
                        "Evaluasi": "Prioritas" if accuracy < 60 else "Perlu latihan" if accuracy < 75 else "Baik",
                    }
                )
            st.dataframe(concept_rows, hide_index=True, width="stretch")
        else:
            st.caption("Data konsep akan muncul setelah mengerjakan soal analisis kode.")

    with history_tab:
        st.subheader("Seluruh percobaan")
        history_rows = []
        for number, attempt in enumerate(attempts, start=1):
            history_rows.append(
                {
                    "Tes": number,
                    "Tanggal": _format_attempt_date(attempt["completed_at"]),
                    "Nilai": f'{attempt["score"]:.1f}',
                    "Benar": f'{attempt["correct"]}/{attempt["total"]}',
                    "Kosong": attempt["unanswered"],
                    "Durasi": format_duration(attempt["duration_seconds"]),
                }
            )
        st.dataframe(history_rows, hide_index=True, width="stretch")

        st.write("")
        st.subheader("Detail review percobaan")
        attempt_options = {
            f"Tes {number} - {_format_attempt_date(attempt['completed_at'])} - Nilai {attempt['score']:.1f}": attempt
            for number, attempt in enumerate(attempts, start=1)
        }
        selected_label = st.selectbox(
            "Pilih tes untuk melihat soal dan jawaban",
            list(attempt_options.keys()),
            index=len(attempt_options) - 1,
        )
        selected_attempt = attempt_options[selected_label]

        detail_columns = st.columns(4)
        detail_metrics = [
            (f'{selected_attempt["score"]:.1f}', "Nilai"),
            (
                f'{selected_attempt["correct"]}/{selected_attempt["total"]}',
                "Jawaban benar",
            ),
            (selected_attempt["incorrect"], "Jawaban salah"),
            (selected_attempt["unanswered"], "Tidak dijawab"),
        ]
        for column, (value, label) in zip(detail_columns, detail_metrics):
            with column:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
                    unsafe_allow_html=True,
                )

        selected_answers = get_attempt_answers(user["id"], selected_attempt["id"])
        if selected_answers:
            st.caption(
                "Buka setiap soal untuk melihat pilihan Anda, kunci jawaban, dan pembahasan."
            )
            render_answer_review(
                selected_answers,
                filter_key=f"history_review_filter_{selected_attempt['id']}",
            )
        else:
            st.info("Detail jawaban untuk percobaan ini belum tersedia.")


def render_intro():
    render_user_navigation(show_dashboard=True)
    st.markdown('<div class="eyebrow">Simulation Test</div>', unsafe_allow_html=True)
    st.markdown(
        '<h1 class="hero-title">Latihan dengan suasana tes yang sebenarnya.</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <p class="hero-copy">
            Kerjakan satu soal dalam satu waktu, pantau sisa waktu, dan tinjau seluruh
            jawaban beserta pembahasannya setelah tes selesai.
        </p>
        <div class="info-strip">
            <div class="info-item"><div class="info-value">100 soal</div><div class="info-label">15 soal analisis pseudocode, 20 soal logika</div></div>
            <div class="info-item"><div class="info-value">120 menit</div><div class="info-label">Timer berjalan setelah tes dimulai</div></div>
            <div class="info-item"><div class="info-value">75%</div><div class="info-label">Target nilai latihan</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Sebelum mulai")
    columns = st.columns(3)
    rules = [
        ("01", "Kerjakan mandiri", "Siapkan tempat yang tenang dan hindari membuka referensi selama simulasi."),
        ("02", "Jawaban tersimpan", "Anda bebas berpindah soal. Jawaban yang sudah dipilih tetap tersimpan."),
        ("03", "Review lengkap", "Hasil menampilkan jawaban benar, salah, kosong, dan cara mendapatkan jawabannya."),
    ]
    for column, (number, title, copy) in zip(columns, rules):
        with column:
            st.markdown(
                f"""
                <div class="rule-card">
                    <div class="rule-number">{number}</div>
                    <div class="rule-title">{title}</div>
                    <div class="rule-copy">{copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    if st.button("Mulai Tes", type="primary", width="stretch"):
        start_test()
        st.rerun()


@st.fragment(run_every=1.0)
def render_timer():
    remaining = TEST_DURATION_SECONDS - (time.time() - st.session_state.started_at)
    is_danger = remaining <= 5 * 60
    danger_class = " timer-danger" if is_danger else ""
    st.markdown(
        f"""
        <div class="timer-card{danger_class}" role="timer" aria-live="polite">
            <div class="timer-label">{t('timer_label')}</div>
            <div class="timer-value">{format_duration(remaining)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if remaining <= 0:
        finish_test("time_up")
        st.rerun()


@st.dialog("Selesaikan tes?")
def confirm_finish_dialog():
    total = len(st.session_state.test_questions)
    unanswered = total - len(st.session_state.answers)
    flagged = len(st.session_state.get("flagged_questions", set()))
    if unanswered:
        st.warning(f"Masih ada {unanswered} soal yang belum dijawab.")
    else:
        st.success("Semua soal sudah dijawab.")
    if flagged:
        st.info(f"Ada {flagged} soal yang masih di-flag untuk ditinjau.")
    st.write("Setelah dikumpulkan, jawaban tidak dapat diubah.")
    left, right = st.columns(2)
    with left:
        if st.button("Lanjut Mengerjakan", width="stretch"):
            st.rerun()
    with right:
        if st.button(t("btn_submit"), type="primary", width="stretch"):
            finish_test()
            st.rerun()


def render_exam():
    remaining = TEST_DURATION_SECONDS - (time.time() - st.session_state.started_at)
    if remaining <= 0:
        finish_test("time_up")
        st.rerun()

    if "flagged_questions" not in st.session_state:
        st.session_state.flagged_questions = set()

    total = len(st.session_state.test_questions)
    current_index = st.session_state.current_question
    question_data = st.session_state.test_questions[current_index]
    question = question_data["item"]
    answered = len(st.session_state.answers)
    flagged_count = len(st.session_state.flagged_questions)
    is_flagged = current_index in st.session_state.flagged_questions

    top_left, top_right = st.columns([5, 1.25], vertical_alignment="center")
    with top_left:
        st.markdown(
            f"""
            <div class="exam-name">Swift Programming Simulation Test</div>
            <div class="exam-meta">{t('soal_prefix')} {current_index + 1} {t('dari')} {total} &nbsp;·&nbsp; {answered} {t('dijawab')} &nbsp;·&nbsp; {flagged_count} {t('di_flag')}</div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        render_timer()

    st.markdown('<div style="height:.15rem"></div>', unsafe_allow_html=True)
    st.progress(answered / total)
    st.markdown(
        f'<div class="progress-copy"><span>Progres jawaban</span><span>{answered}/{total}</span></div>',
        unsafe_allow_html=True,
    )

    main, palette = st.columns([3, 1.2], gap="large")
    with main:
        with st.container(key="question_card", border=True):
            meta_column, flag_column = st.columns([4, 1], vertical_alignment="center")
            with meta_column:
                st.markdown(
                    f'<div class="question-meta">{question_data["section_label"]} · {t("soal_prefix")} {question_data["section_number"]}</div>',
                    unsafe_allow_html=True,
                )
            with flag_column:
                if is_flagged:
                    flag_rule = (
                        "background:#f6bf54!important;border-color:#f6bf54!important;"
                        "color:#201806!important;font-weight:800!important;"
                    )
                else:
                    flag_rule = (
                        "background:transparent!important;border-color:#8f7539!important;"
                        "color:#f6bf54!important;"
                    )
                st.markdown(
                    f"<style>.st-key-flag_current_question button{{{flag_rule}}}</style>",
                    unsafe_allow_html=True,
                )
                st.button(
                    t("btn_unflag") if is_flagged else t("btn_flag"),
                    key="flag_current_question",
                    on_click=toggle_question_flag,
                    args=(current_index,),
                    width="stretch",
                    help="Tandai soal ini untuk ditinjau kembali",
                )
            st.markdown(f'<div class="question-title">{html.escape(q_text(question, "q"))}</div>', unsafe_allow_html=True)
            if question.get("difficulty") or question.get("concept"):
                badges = "".join(
                    f'<span class="code-badge">{value}</span>'
                    for value in (question.get("difficulty"), question.get("concept"))
                    if value
                )
                st.markdown(f'<div class="code-context">{badges}</div>', unsafe_allow_html=True)
            if question.get("code"):
                st.code(
                    question["code"],
                    language=question.get("language", "swift"),
                    line_numbers=True,
                )
            st.markdown(f'<div class="choice-label">{t("choice_label")}</div>', unsafe_allow_html=True)

            widget_key = f"answer_{st.session_state.test_id}_{current_index}"
            current_answer = st.session_state.answers.get(current_index)
            # Get active-language options for display
            display_options = q_text(question, "options") if isinstance(q_text(question, "options"), list) else question.get("options", [])
            id_options = question.get("options", [])
            en_options = question.get("options_en", id_options)
            # Map stored ID-language answer to display-language for default_index
            if current_answer is not None and get_lang() == "en" and current_answer in id_options:
                display_current = en_options[id_options.index(current_answer)]
            else:
                display_current = current_answer
            default_index = display_options.index(display_current) if display_current in display_options else None
            choice = st.radio(
                t("choice_label"),
                display_options,
                index=default_index,
                key=widget_key,
                label_visibility="collapsed",
            )
            if choice is not None:
                # Store answer in ID language (for scoring against ID answer)
                if get_lang() == "en" and choice in en_options:
                    stored_answer = id_options[en_options.index(choice)]
                else:
                    stored_answer = choice
                st.session_state.answers[current_index] = stored_answer



        st.write("")
        previous, clear_col, next_column = st.columns([1, 1.4, 1])
        with previous:
            st.button(
                t("btn_prev"),
                disabled=current_index == 0,
                on_click=move_question,
                args=(-1,),
                width="stretch",
            )
        with clear_col:
            if current_index in st.session_state.answers:
                if st.button(
                    t("btn_clear"),
                    key="clear_answer_nav",
                    width="stretch",
                ):
                    clear_answer(current_index, widget_key)
                    st.rerun()
        with next_column:
            if current_index < total - 1:
                st.button(
                    t("btn_next"),
                    type="primary",
                    on_click=move_question,
                    args=(1,),
                    width="stretch",
                )
            else:
                if st.button(t("btn_finish"), type="primary", width="stretch"):
                    confirm_finish_dialog()

    with palette:
        with st.container(key="question_palette", border=True):
            # ── Language switcher ──────────────────────────────────────
            lang = get_lang()
            lang_cols = st.columns(2)
            with lang_cols[0]:
                if st.button("🇮🇩 ID", key="lang_id", use_container_width=True,
                             type="primary" if lang == "id" else "secondary"):
                    st.session_state.ui_lang = "id"
                    st.rerun()
            with lang_cols[1]:
                if st.button("🇬🇧 EN", key="lang_en", use_container_width=True,
                             type="primary" if lang == "en" else "secondary"):
                    st.session_state.ui_lang = "en"
                    st.rerun()

            st.markdown(f'<div class="palette-title">{t("nav_title")}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="palette-copy">{t("nav_copy")}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="palette-legend" aria-label="{t('nav_title')}">
                    <div class="legend-item"><span class="legend-swatch legend-active"></span>{t('legend_active')}</div>
                    <div class="legend-item"><span class="legend-swatch legend-flagged"></span>{t('legend_flagged')}</div>
                    <div class="legend-item"><span class="legend-swatch legend-answered"></span>{t('legend_answered')}</div>
                    <div class="legend-item"><span class="legend-swatch legend-empty"></span>{t('legend_empty')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_navigation_status_styles(total, current_index)

            grouped_indices = defaultdict(list)
            for index, data in enumerate(st.session_state.test_questions):
                grouped_indices[data["section_label"]].append(index)

            if "palette_collapsed" not in st.session_state:
                st.session_state.palette_collapsed = {}

            for section_label, indices in grouped_indices.items():
                is_collapsed = st.session_state.palette_collapsed.get(section_label, False)
                toggle_icon = t("expand") if is_collapsed else t("collapse")
                if st.button(
                    f"{section_label}  {toggle_icon}",
                    key=f"sec_toggle_{section_label}",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state.palette_collapsed[section_label] = not is_collapsed
                    st.rerun()
                st.markdown(
                    f"<style>.st-key-sec_toggle_{section_label.replace(' ', '_').replace('&', 'amp')} button"
                    "{ text-align:left!important; font-size:.7rem!important; min-height:32px!important;"
                    " padding:.3rem .6rem!important; font-weight:750!important;"
                    " color:var(--muted)!important; justify-content:space-between!important; }</style>",
                    unsafe_allow_html=True,
                )

                if not is_collapsed:
                    for row_start in range(0, len(indices), 4):
                        row_indices = indices[row_start : row_start + 4]
                        columns = st.columns(4)
                        for column, index in zip(columns, row_indices):
                            label = f"{index + 1}"
                            if index == current_index:
                                status_text = t("status_active")
                                if index in st.session_state.flagged_questions:
                                    status_text = t("status_active_and_flagged")
                            elif index in st.session_state.flagged_questions:
                                status_text = t("status_flagged")
                            elif index in st.session_state.answers:
                                status_text = t("status_answered")
                            else:
                                status_text = t("status_unanswered")
                            with column:
                                st.button(
                                    label,
                                    key=f"nav_{st.session_state.test_id}_{index}",
                                    type="primary" if index == current_index else "secondary",
                                    on_click=go_to_question,
                                    args=(index,),
                                    width="stretch",
                                    help=f"{t('soal_prefix')} {index + 1}: {status_text}",
                                )

            st.divider()
            if st.button(t("btn_submit"), width="stretch"):
                confirm_finish_dialog()

    save_active_test()


def render_results():
    persist_current_attempt()
    render_user_navigation(show_dashboard=True)
    correct, total, section_results = calculate_results()
    unanswered = total - len(st.session_state.answers)
    incorrect = total - correct - unanswered
    score = (correct / total * 100) if total else 0
    used_seconds = (st.session_state.finished_at or time.time()) - st.session_state.started_at

    if score >= 75:
        result_title = "Target latihan tercapai"
        result_copy = "Pertahankan konsistensi dan pelajari kembali jawaban yang masih salah."
    else:
        result_title = "Masih ada ruang untuk berkembang"
        result_copy = "Gunakan review di bawah untuk memahami konsep yang perlu dilatih kembali."

    ring_color = "#35d0a0" if score >= 75 else "#ff7185"
    st.markdown(
        f"""
        <div class="result-hero">
            <div class="result-grid">
                <div class="score-ring" style="background:conic-gradient({ring_color} {score:.2f}%, #2b3544 0)">
                    <div class="score-content"><div class="score-number">{score:.0f}</div><div class="score-caption">dari 100</div></div>
                </div>
                <div>
                    <div class="eyebrow">Hasil Tes</div>
                    <h1 class="result-title">{result_title}</h1>
                    <div class="result-copy">{result_copy}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_columns = st.columns(4)
    metrics = [
        (f'<span class="status-good">{correct}</span>', "Jawaban benar"),
        (f'<span class="status-bad">{incorrect}</span>', "Jawaban salah"),
        (f'<span class="status-empty">{unanswered}</span>', "Tidak dijawab"),
        (format_duration(used_seconds), "Waktu pengerjaan"),
    ]
    for column, (value, label) in zip(metric_columns, metrics):
        with column:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

    if st.session_state.finish_reason == "time_up":
        st.warning("Waktu habis. Jawaban yang sudah dipilih tetap dinilai.")
    if st.session_state.get("persistence_error"):
        st.error(
            "Hasil tampil, tetapi riwayat belum berhasil disimpan. "
            f'Detail: {st.session_state.persistence_error}'
        )
    elif st.session_state.get("attempt_id"):
        st.success("Hasil tes sudah disimpan ke progres akun Anda.")
    if st.session_state.get("firebase_error"):
        st.warning(st.session_state.firebase_error)

    st.write("")
    st.subheader("Nilai per section")
    section_columns = st.columns(len(section_results))
    for column, (section, data) in zip(section_columns, section_results.items()):
        percentage = data["correct"] / data["total"] * 100
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{percentage:.0f}%</div>
                    <div class="metric-label">{section} · {data["correct"]}/{data["total"]} benar</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    action_left, action_right, action_space = st.columns([1, 1, 2])
    with action_left:
        if st.button("Tes Lagi", type="primary", width="stretch"):
            start_test()
            st.rerun()
    with action_right:
        if st.button("Kembali ke Dashboard", width="stretch"):
            return_to_dashboard()
            st.rerun()

    st.divider()
    st.subheader("Review jawaban")
    st.caption("Buka setiap soal untuk melihat jawaban Anda, jawaban benar, dan cara menyelesaikannya.")
    render_answer_review(
        build_current_review_items(),
        filter_key=f"review_filter_{st.session_state.test_id}",
    )

bank_errors = validate_question_bank()
if bank_errors:
    st.error("Bank soal belum valid:\n- " + "\n- ".join(bank_errors))
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    restore_remembered_user()

if "screen" not in st.session_state:
    if st.session_state.user:
        if load_active_test():
            st.session_state.screen = "exam"
        else:
            st.session_state.screen = "dashboard"
    else:
        st.session_state.screen = "auth"

if not st.session_state.user:
    st.session_state.screen = "auth"

if st.session_state.screen == "auth":
    render_auth()
elif st.session_state.screen == "dashboard":
    render_dashboard()
elif st.session_state.screen == "intro":
    render_intro()
elif st.session_state.screen == "exam":
    render_exam()
else:
    render_results()
