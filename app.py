import streamlit as st
import tempfile
import os
import html
from extract_resume import extract_text_from_pdf
from retrieve import retrieve_matching_jobs
from generate import generate_match_explanation
from rank_resumes import rank_resumes_against_jd
from ats_score import get_ats_score

st.set_page_config(page_title="Resume AI Toolkit", page_icon="🎯", layout="wide")

def clean_for_html(text):
    """Sanitize LLM output before injecting into HTML to avoid markdown/HTML rendering issues."""
    if not text:
        return ""
    text = " ".join(text.split())
    text = html.escape(text)
    return text

st.markdown("""
<style>
    .stApp { background-color: #f4faf5; }
    .navbar {
        background-color: #2e7d32;
        padding: 1.1rem 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .navbar-title { color: white; font-size: 1.6rem; font-weight: 800; letter-spacing: 1px; }
    .task-column {
        background-color: #e8f5e9;
        border: 2px solid #a5d6a7;
        border-radius: 14px;
        padding: 2rem 1.5rem;
        min-height: 480px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .task-icon { font-size: 2.4rem; margin-bottom: 0.6rem; }
    .task-title { font-size: 1.3rem; font-weight: 800; color: #1b5e20; margin-bottom: 1rem; }
    .task-desc { color: #33691e; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem; }
    div[data-testid="stButton"] button {
        background-color: #2e7d32 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.6rem 1rem !important;
    }
    div[data-testid="stButton"] button:hover { background-color: #1b5e20 !important; }
    .result-card {
        background-color: #ffffff;
        border: 1px solid #c8e6c9;
        border-radius: 12px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1.1rem;
    }
    .job-rank {
        display: inline-block;
        background-color: #2e7d32;
        color: white;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 3px 12px;
        border-radius: 20px;
        margin-bottom: 0.5rem;
    }
    .job-title { font-size: 1.2rem; font-weight: 700; color: #1b5e20; margin-bottom: 0.2rem; }
    .job-meta { color: #558b2f; font-size: 0.85rem; margin-bottom: 0.8rem; }
    .match-score {
        display: inline-block;
        background-color: #c8e6c9;
        color: #1b5e20;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 3px 12px;
        border-radius: 20px;
        margin-left: 6px;
    }
    .explanation-box {
        border-left: 3px solid #2e7d32;
        padding-left: 1rem;
        color: #37474f;
        font-size: 0.93rem;
        line-height: 1.6;
    }
    .winner-badge {
        display: inline-block;
        background-color: #fff59d;
        color: #7a5c00;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 20px;
        margin-bottom: 0.6rem;
    }
    .checklist-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0;
        border-bottom: 1px solid #e0e0e0;
        color: #263238;
        font-size: 0.92rem;
    }
    .checklist-item:last-child { border-bottom: none; }
    .status-good { color: #2e7d32; font-weight: 800; }
    .status-warning { color: #ef6c00; font-weight: 800; }
    .suggestion-item { padding: 0.5rem 0; color: #37474f; font-size: 0.9rem; line-height: 1.5; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "home"

def go_home():
    st.session_state.page = "home"

def go_to(page_name):
    st.session_state.page = page_name

def render_navbar():
    st.markdown('<div class="navbar"><span class="navbar-title">🎯 RESUME AI TOOLKIT</span></div>', unsafe_allow_html=True)


def render_score_gauge(score, label="RESUME STRENGTH"):
    color = "#2e7d32" if score >= 75 else "#ef6c00" if score >= 50 else "#c62828"
    tier = "GOOD" if score >= 75 else "FAIR" if score >= 50 else "NEEDS WORK"
    circumference = 2 * 3.14159 * 45
    offset = circumference * (1 - score / 100)

    svg = (
        '<div style="text-align:center;">'
        f'<svg width="150" height="150" viewBox="0 0 100 100">'
        f'<circle cx="50" cy="50" r="45" fill="none" stroke="#e0e0e0" stroke-width="8"/>'
        f'<circle cx="50" cy="50" r="45" fill="none" stroke="{color}" stroke-width="8" '
        f'stroke-dasharray="{circumference}" stroke-dashoffset="{offset}" '
        f'stroke-linecap="round" transform="rotate(-90 50 50)"/>'
        f'<text x="50" y="48" text-anchor="middle" font-size="22" font-weight="800" fill="#1b5e20">{score}</text>'
        f'<text x="50" y="63" text-anchor="middle" font-size="9" font-weight="700" fill="{color}">{tier}</text>'
        '</svg>'
        f'<div style="color:#558b2f; font-size:0.78rem; font-weight:700; letter-spacing:0.5px; margin-top:0.3rem;">{label}</div>'
        '</div>'
    )
    st.markdown(svg, unsafe_allow_html=True)


def render_home():
    render_navbar()
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown(
            '<div class="task-column"><div>'
            '<div class="task-icon">🔍</div>'
            '<div class="task-title">Resume Job Matcher</div>'
            '<div class="task-desc">Upload your resume and find the best-matching jobs from our database, ranked with AI-generated explanations.</div>'
            '</div></div>',
            unsafe_allow_html=True
        )
        st.button("Open →", key="btn1", use_container_width=True, on_click=go_to, args=("matcher",))

    with col2:
        st.markdown(
            '<div class="task-column"><div>'
            '<div class="task-icon">🏆</div>'
            '<div class="task-title">Best Resume for a Job</div>'
            '<div class="task-desc">Paste a job description and upload up to 5 resumes — find out which candidate fits best.</div>'
            '</div></div>',
            unsafe_allow_html=True
        )
        st.button("Open →", key="btn2", use_container_width=True, on_click=go_to, args=("ranker",))

    with col3:
        st.markdown(
            '<div class="task-column"><div>'
            '<div class="task-icon">📊</div>'
            '<div class="task-title">Resume ATS Score</div>'
            '<div class="task-desc">Get an ATS-friendliness score for your resume, with a category breakdown and improvement tips.</div>'
            '</div></div>',
            unsafe_allow_html=True
        )
        st.button("Open →", key="btn3", use_container_width=True, on_click=go_to, args=("ats",))


def render_matcher():
    render_navbar()
    st.button("← Back to Home", on_click=go_home)

    left, right = st.columns([1, 1.6], gap="large")

    with left:
        st.markdown("#### Upload Resume")
        uploaded_file = st.file_uploader("Upload your resume", type=["pdf"], label_visibility="collapsed", key="matcher_upload")
        top_k = st.selectbox("Matches to show", [3, 5, 10], index=0)
        find_clicked = False
        if uploaded_file is not None:
            find_clicked = st.button("🔍 Find Matching Jobs", use_container_width=True)

    with right:
        st.markdown("#### Results")
        if uploaded_file is not None and find_clicked:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            progress = st.progress(0, text="Extracting resume text...")
            resume_text = extract_text_from_pdf(tmp_path)
            progress.progress(30, text="Searching job database...")

            results = retrieve_matching_jobs(tmp_path, top_k=top_k)
            progress.progress(60, text="Generating match explanations...")

            for i in range(len(results["ids"][0])):
                title = results["metadatas"][0][i]["title"]
                exp_level = results["metadatas"][0][i]["experience_level"]
                job_text = results["documents"][0][i]
                distance = results["distances"][0][i]
                similarity_pct = max(0, min(100, round((1 - distance) * 100)))

                explanation = clean_for_html(generate_match_explanation(resume_text, job_text, title))
                safe_title = clean_for_html(title)
                safe_exp = clean_for_html(exp_level)

                card_html = (
                    '<div class="result-card">'
                    + f'<span class="job-rank">MATCH #{i+1}</span>'
                    + f'<span class="match-score">{similarity_pct}% relevance</span>'
                    + f'<div class="job-title">{safe_title}</div>'
                    + f'<div class="job-meta">Experience Level: {safe_exp}</div>'
                    + f'<div class="explanation-box">{explanation}</div>'
                    + '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

            progress.progress(100, text="Done!")
            progress.empty()
            os.unlink(tmp_path)
        else:
            st.markdown('<div style="text-align:center; padding: 3rem; color: #9e9e9e;">📄 Upload a resume and click "Find Matching Jobs" to see results here</div>', unsafe_allow_html=True)


def render_ranker():
    render_navbar()
    st.button("← Back to Home", on_click=go_home)

    left, right = st.columns([1, 1.6], gap="large")

    with left:
        st.markdown("#### Job Description + Resumes")
        jd_text = st.text_area("Job Description", height=160, placeholder="Paste the job description here...")
        resume_files = st.file_uploader("Upload resumes (max 5)", type=["pdf"], accept_multiple_files=True, key="ranker_upload")
        if resume_files and len(resume_files) > 5:
            st.warning("Only the first 5 resumes will be used.")
            resume_files = resume_files[:5]
        rank_clicked = False
        if jd_text and resume_files:
            rank_clicked = st.button("🏆 Rank Resumes", use_container_width=True)

    with right:
        st.markdown("#### Results")
        if jd_text and resume_files and rank_clicked:
            tmp_paths = []
            for f in resume_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(f.read())
                    tmp_paths.append((tmp_file.name, f.name))

            progress = st.progress(0, text="Comparing resumes to job description...")
            results = rank_resumes_against_jd(jd_text, [p[0] for p in tmp_paths])
            path_to_name = {p[0]: p[1] for p in tmp_paths}
            progress.progress(60, text="Generating explanations...")

            for i, r in enumerate(results):
                filename = clean_for_html(path_to_name[r["path"]])
                similarity_pct = max(0, min(100, round(r["similarity"] * 100)))
                badge = '<span class="winner-badge">🏆 BEST MATCH</span>' if i == 0 else ""

                explanation = clean_for_html(generate_match_explanation(r["resume_text"], jd_text, "the job description"))

                card_html = (
                    '<div class="result-card">'
                    + badge
                    + f'<span class="job-rank">RANK #{i+1}</span>'
                    + f'<span class="match-score">{similarity_pct}% match</span>'
                    + f'<div class="job-title">{filename}</div>'
                    + f'<div class="explanation-box">{explanation}</div>'
                    + '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

            progress.progress(100, text="Done!")
            progress.empty()
            for p, _ in tmp_paths:
                os.unlink(p)
        else:
            st.markdown('<div style="text-align:center; padding: 3rem; color: #9e9e9e;">📋 Paste a JD and upload resumes to see rankings here</div>', unsafe_allow_html=True)


def render_ats():
    render_navbar()
    st.button("← Back to Home", on_click=go_home)

    left, right = st.columns([1, 1.6], gap="large")

    with left:
        st.markdown("#### Upload Resume")
        uploaded_file = st.file_uploader("Upload your resume", type=["pdf"], label_visibility="collapsed", key="ats_upload")
        check_clicked = False
        if uploaded_file is not None:
            check_clicked = st.button("📊 Check ATS Score", use_container_width=True)

    with right:
        st.markdown("#### Results")
        if uploaded_file is not None and check_clicked:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            with st.spinner("Analyzing your resume..."):
                resume_text = extract_text_from_pdf(tmp_path)
                result = get_ats_score(resume_text)
            os.unlink(tmp_path)

            gcol, ccol = st.columns([1, 1.2])
            with gcol:
                render_score_gauge(result["overall_score"])
            with ccol:
                checklist_parts = ['<div class="result-card">']
                for section, info in result["sections"].items():
                    status = info["status"]
                    icon = "✓" if status == "good" else "!"
                    status_class = "status-good" if status == "good" else "status-warning"
                    safe_section = clean_for_html(section)
                    checklist_parts.append(
                        f'<div class="checklist-item"><span>{safe_section}</span><span class="{status_class}">{icon}</span></div>'
                    )
                checklist_parts.append('</div>')
                st.markdown("".join(checklist_parts), unsafe_allow_html=True)

            st.markdown("##### Suggestions to Improve")
            suggestion_parts = ['<div class="result-card">']
            for s in result["suggestions"]:
                suggestion_parts.append(f'<div class="suggestion-item">💡 {clean_for_html(s)}</div>')
            suggestion_parts.append('</div>')
            st.markdown("".join(suggestion_parts), unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; padding: 3rem; color: #9e9e9e;">📄 Upload a resume and click "Check ATS Score" to see results here</div>', unsafe_allow_html=True)


if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "matcher":
    render_matcher()
elif st.session_state.page == "ranker":
    render_ranker()
elif st.session_state.page == "ats":
    render_ats()