import html
import random
import time
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from database import (
    authenticate_user,
    create_user,
    get_attempts,
    get_concept_performance,
    get_section_performance,
    initialize_database,
    save_attempt,
)
from questions import QUESTIONS


st.set_page_config(
    page_title="Apple Developer Academy Prep",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed",
)


TEST_DURATION_SECONDS = 90 * 60
SECTION_CONFIG = {
    "Section 1: Logic": {"label": "Logic", "quota": 10},
    "Section 2: Programming (Swift Focus)": {"label": "Swift", "quota": 15},
    "Section 6: Code Analysis": {"label": "Analisis Kode", "quota": 20},
    "Section 5: Code Completion": {"label": "Lengkapi Kode", "quota": 15},
    "Section 3: OOP": {"label": "OOP", "quota": 20},
    "Section 4: Bonus (Design/UX)": {"label": "Design & UX", "quota": 5},
}


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
        .brand-mark {
            display: grid; place-items: center; width: 36px; height: 36px;
            border-radius: 11px; background: linear-gradient(145deg, #ff737a, #e84255);
            box-shadow: 0 8px 24px rgba(255, 90, 98, .22); font-size: .9rem;
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
        .palette-section { color: var(--muted); font-size: .72rem; font-weight: 750; margin: .8rem 0 .35rem; }
        .st-key-question_palette .stButton > button {
            min-width: 0; width: 100%; min-height: 46px; padding: .35rem .2rem;
            font-size: .84rem; white-space: nowrap;
        }
        .st-key-question_palette .stButton > button p {
            white-space: nowrap; overflow: hidden; text-overflow: clip;
        }

        .progress-copy { display: flex; justify-content: space-between; color: var(--muted); font-size: .78rem; margin: .15rem 0 .35rem; }
        div[data-testid="stProgress"] > div > div { background-color: var(--accent); }
        .stButton > button { min-height: 44px; border-radius: 11px; font-weight: 680; cursor: pointer; }
        .stButton > button:focus-visible { outline: 3px solid rgba(255, 90, 98, .35); outline-offset: 2px; }

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
            prepared_item["options"] = random.sample(item["options"], len(item["options"]))
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
    st.session_state.current_question = 0
    st.session_state.started_at = time.time()
    st.session_state.finished_at = None
    st.session_state.finish_reason = None
    st.session_state.attempt_id = None
    st.session_state.persistence_error = None
    st.session_state.screen = "exam"


def return_to_intro():
    st.session_state.screen = "intro"


def return_to_dashboard():
    st.session_state.screen = "dashboard"


def set_authenticated_user(user):
    st.session_state.user = user
    st.session_state.screen = "dashboard"
    st.session_state.login_failures = 0
    st.session_state.login_locked_until = 0


def logout_user():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.screen = "auth"


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
                "section": question_data["section_label"],
                "concept": question.get("concept"),
                "question": question["q"],
                "user_answer": user_answer,
                "correct_answer": question["answer"],
                "is_correct": user_answer == question["answer"],
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
    except Exception as error:
        st.session_state.persistence_error = str(error)


def finish_test(reason="submitted"):
    if st.session_state.get("screen") != "exam":
        return
    st.session_state.finished_at = time.time()
    st.session_state.finish_reason = reason
    persist_current_attempt()
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
        """
        <div class="brand-row">
            <div class="brand-mark">A</div>
            <div>Academy Prep</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intro():
    render_brand()
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
            <div class="info-item"><div class="info-value">85 soal</div><div class="info-label">50 soal berfokus pada Swift</div></div>
            <div class="info-item"><div class="info-value">90 menit</div><div class="info-label">Timer berjalan setelah tes dimulai</div></div>
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
    if st.button("Mulai Tes", type="primary", use_container_width=True):
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
            <div class="timer-label">Sisa waktu</div>
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
    if unanswered:
        st.warning(f"Masih ada {unanswered} soal yang belum dijawab.")
    else:
        st.success("Semua soal sudah dijawab.")
    st.write("Setelah dikumpulkan, jawaban tidak dapat diubah.")
    left, right = st.columns(2)
    with left:
        if st.button("Lanjut Mengerjakan", use_container_width=True):
            st.rerun()
    with right:
        if st.button("Kumpulkan Jawaban", type="primary", use_container_width=True):
            finish_test()
            st.rerun()


def render_exam():
    remaining = TEST_DURATION_SECONDS - (time.time() - st.session_state.started_at)
    if remaining <= 0:
        finish_test("time_up")
        st.rerun()

    total = len(st.session_state.test_questions)
    current_index = st.session_state.current_question
    question_data = st.session_state.test_questions[current_index]
    question = question_data["item"]
    answered = len(st.session_state.answers)

    top_left, top_right = st.columns([5, 1.25], vertical_alignment="center")
    with top_left:
        st.markdown(
            f"""
            <div class="exam-name">Apple Developer Academy Simulation Test</div>
            <div class="exam-meta">Soal {current_index + 1} dari {total} &nbsp;·&nbsp; {answered} sudah dijawab</div>
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
            st.markdown(
                f'<div class="question-meta">{question_data["section_label"]} · Soal {question_data["section_number"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f'<div class="question-title">{question["q"]}</div>', unsafe_allow_html=True)
            if question.get("difficulty") or question.get("concept"):
                badges = "".join(
                    f'<span class="code-badge">{value}</span>'
                    for value in (question.get("difficulty"), question.get("concept"))
                    if value
                )
                st.markdown(f'<div class="code-context">{badges}</div>', unsafe_allow_html=True)
            if question.get("code"):
                st.code(question["code"], language="swift", line_numbers=True)
            st.markdown('<div class="choice-label">Pilih satu jawaban</div>', unsafe_allow_html=True)

            widget_key = f"answer_{st.session_state.test_id}_{current_index}"
            current_answer = st.session_state.answers.get(current_index)
            default_index = question["options"].index(current_answer) if current_answer in question["options"] else None
            choice = st.radio(
                "Pilih satu jawaban",
                question["options"],
                index=default_index,
                key=widget_key,
                label_visibility="collapsed",
            )
            if choice is not None:
                st.session_state.answers[current_index] = choice

            if current_index in st.session_state.answers:
                st.button(
                    "Kosongkan jawaban",
                    type="tertiary",
                    on_click=clear_answer,
                    args=(current_index, widget_key),
                )

        st.write("")
        previous, spacer, next_column = st.columns([1, 1.4, 1])
        with previous:
            st.button(
                "Sebelumnya",
                disabled=current_index == 0,
                on_click=move_question,
                args=(-1,),
                use_container_width=True,
            )
        with next_column:
            if current_index < total - 1:
                st.button(
                    "Berikutnya",
                    type="primary",
                    on_click=move_question,
                    args=(1,),
                    use_container_width=True,
                )
            else:
                if st.button("Selesaikan Tes", type="primary", use_container_width=True):
                    confirm_finish_dialog()

    with palette:
        with st.container(key="question_palette", border=True):
            st.markdown('<div class="palette-title">Navigasi soal</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="palette-copy">Soal aktif berwarna merah. Soal terjawab diberi tanda.</div>',
                unsafe_allow_html=True,
            )

            grouped_indices = defaultdict(list)
            for index, data in enumerate(st.session_state.test_questions):
                grouped_indices[data["section_label"]].append(index)

            for section_label, indices in grouped_indices.items():
                st.markdown(f'<div class="palette-section">{section_label}</div>', unsafe_allow_html=True)
                for row_start in range(0, len(indices), 4):
                    row_indices = indices[row_start : row_start + 4]
                    columns = st.columns(4)
                    for column, index in zip(columns, row_indices):
                        label = f"{index + 1}"
                        if index in st.session_state.answers and index != current_index:
                            label = f"{index + 1}·"
                        with column:
                            st.button(
                                label,
                                key=f"nav_{st.session_state.test_id}_{index}",
                                type="primary" if index == current_index else "secondary",
                                on_click=go_to_question,
                                args=(index,),
                                use_container_width=True,
                                help=f"Buka soal {index + 1}",
                            )

            st.divider()
            if st.button("Kumpulkan Jawaban", use_container_width=True):
                confirm_finish_dialog()


def render_results():
    render_brand()
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
        if st.button("Tes Lagi", type="primary", use_container_width=True):
            start_test()
            st.rerun()
    with action_right:
        if st.button("Kembali ke Awal", use_container_width=True):
            return_to_intro()
            st.rerun()

    st.divider()
    st.subheader("Review jawaban")
    st.caption("Buka setiap soal untuk melihat jawaban Anda, jawaban benar, dan cara menyelesaikannya.")
    review_filter = st.radio(
        "Filter review",
        ["Semua", "Salah", "Benar", "Kosong"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key=f"review_filter_{st.session_state.test_id}",
    )

    for index, question_data in enumerate(st.session_state.test_questions):
        question = question_data["item"]
        user_answer = st.session_state.answers.get(index)
        if user_answer is None:
            status, status_class = "Kosong", "status-empty"
        elif user_answer == question["answer"]:
            status, status_class = "Benar", "status-good"
        else:
            status, status_class = "Salah", "status-bad"

        if review_filter != "Semua" and review_filter != status:
            continue

        with st.expander(
            f"{index + 1}. [{status}] {question['q']}",
            expanded=False,
        ):
            st.markdown(
                f'<div class="question-meta">{question_data["section_label"]} · <span class="{status_class}">{status}</span></div>',
                unsafe_allow_html=True,
            )
            if question.get("code"):
                st.code(question["code"], language="swift", line_numbers=True)
            if question.get("difficulty") or question.get("concept"):
                badges = "".join(
                    f'<span class="code-badge">{value}</span>'
                    for value in (question.get("difficulty"), question.get("concept"))
                    if value
                )
                st.markdown(f'<div class="code-context">{badges}</div>', unsafe_allow_html=True)
            answer_columns = st.columns(2)
            with answer_columns[0]:
                answer_class = "correct" if status == "Benar" else "wrong"
                st.markdown(
                    f"""
                    <div class="answer-box {answer_class}">
                        <div class="answer-label">Jawaban Anda</div>
                        <div class="answer-value">{user_answer or "Tidak dijawab"}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with answer_columns[1]:
                st.markdown(
                    f"""
                    <div class="answer-box correct">
                        <div class="answer-label">Jawaban benar</div>
                        <div class="answer-value">{question["answer"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"""
                <div class="explanation">
                    <div class="explanation-title">Cara menjawab</div>
                    <div>{get_explanation(question)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


bank_errors = validate_question_bank()
if bank_errors:
    st.error("Bank soal belum valid:\n- " + "\n- ".join(bank_errors))
    st.stop()

if "screen" not in st.session_state:
    st.session_state.screen = "intro"

if st.session_state.screen == "intro":
    render_intro()
elif st.session_state.screen == "exam":
    render_exam()
else:
    render_results()
