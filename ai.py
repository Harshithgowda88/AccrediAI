
import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import json, re
import matplotlib.pyplot as plt
from google import genai

# ---------------------------
# Load API Keys
# ---------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ---------------------------
# Helper functions
# ---------------------------
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def analyze_with_ai(pdf_text):
    if not client:
        return "ERROR: GEMINI_API_KEY not set."
    prompt = f"""
You are an AI reviewer for UGC/AICTE approval.
Return ONLY valid JSON with keys:
- faculty_percentage (0-100)
- infrastructure_percentage (0-100)
- document_percentage (0-100)
- other_percentage (0-100)
- total_percentage (0-100)
- summary (short text)
- faculty_summary (5–10 lines)
- infrastructure_summary (5–10 lines)
- document_summary (5–10 lines)
- other_summary (5–10 lines)
- overall_summary (5–10 lines)

Text:
{pdf_text}
"""
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def safe_parse_json(ai_result):
    try:
        match = re.search(r"\{.*\}", ai_result, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return {}
    except Exception as e:
        st.error(f"Could not parse AI output as JSON. Error: {e}")
        return {}

def generate_suggestions(parsed_json, summaries_text):
    if not client:
        return "Gemini API key not found. Set GEMINI_API_KEY to generate suggestions."
    prompt = f"""
You are an expert educational consultant. Based on these numeric scores and summaries, give 5 practical, prioritized suggestions (short bullet points) the college can implement to improve approval chances and overall quality.

Scores:
faculty_percentage: {parsed_json.get('faculty_percentage', 0)}
infrastructure_percentage: {parsed_json.get('infrastructure_percentage', 0)}
document_percentage: {parsed_json.get('document_percentage', 0)}
other_percentage: {parsed_json.get('other_percentage', 0)}
total_percentage: {parsed_json.get('total_percentage', 0)}

Summaries:
{summaries_text}

Return plain text bullets only.
"""
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )
    return response.text

# ---------------------------
# Session state defaults
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Upload"
if "ai_raw" not in st.session_state:
    st.session_state.ai_raw = ""
if "parsed" not in st.session_state:
    st.session_state.parsed = {}
if "chart_index" not in st.session_state:
    st.session_state.chart_index = 0
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ""

# ---------------------------
# Page layout and CSS
# ---------------------------
st.set_page_config(page_title="AccrediAI", page_icon="🎓", layout="wide")

st.markdown("""
<style>
body { background-color: #f8fbff; font-family: 'Open Sans', sans-serif; }
.header { text-align:center; padding:18px; background: linear-gradient(90deg,#e8f0ff,#ffffff); border-radius:10px; margin-bottom:18px; }
.card { background:white; padding:18px; border-radius:12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.small-muted { color:#6b7280; font-size:13px; }
.header-box { background: linear-gradient(135deg, #6a0dad, #ffffff); border-radius: 12px; padding: 18px; margin-bottom: 18px; text-align: center; color: black; box-shadow: 2px 2px 10px rgba(0,0,0,0.12); }
.summary-box { background: linear-gradient(135deg, #e6eefc, #ffffff); border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin: 12px 0; box-shadow: 0 6px 18px rgba(0,0,0,0.04); color: #0b3b8c; }
.summary-title { font-size:18px; font-weight:700; color:#1e293b; margin-bottom:8px; }
.summary-text { color:#0b3b8c; line-height:1.45; }
.footer { text-align:center; margin-top:30px; color:gray; font-size:13px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><h1>🎓 AccrediAI</h1><div class="small-muted">Upload PDF → AI Review → Dashboard & Suggestions</div></div>', unsafe_allow_html=True)

# ---------------------------
# Navigation (two pages)
# ---------------------------
nav = st.sidebar.radio("Pages", ["Upload", "Dashboard"], index=0 if st.session_state.page=="Upload" else 1)
st.session_state.page = nav

# ---------------------------
# Page: Upload
# ---------------------------
if st.session_state.page == "Upload":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Step 1 — Upload PDF and Get Raw AI Output")
    uploaded_file = st.file_uploader("Upload SSR/SST PDF", type=["pdf"])
    if uploaded_file:
        st.info("Extracting text from PDF...")
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.success("Text extracted successfully")
        st.info("Sending text to Gemini AI for review...")
        ai_result = analyze_with_ai(pdf_text)
        st.session_state.ai_raw = ai_result
        st.success("AI analysis complete")
        st.subheader("🔍 Raw AI Output")
        st.code(ai_result, language="json")

        parsed = safe_parse_json(ai_result)
        st.session_state.parsed = parsed

        if parsed:
            st.success("Parsed JSON stored for Dashboard")
            st.markdown("**Parsed Scores**")
            st.write({
                "faculty_percentage": parsed.get("faculty_percentage", 0),
                "infrastructure_percentage": parsed.get("infrastructure_percentage", 0),
                "document_percentage": parsed.get("document_percentage", 0),
                "other_percentage": parsed.get("other_percentage", 0),
                "total_percentage": parsed.get("total_percentage", 0)
            })
        else:
            st.warning("AI output could not be parsed into JSON. Please check raw output.")

        st.write("")
        if st.button("Go to Dashboard"):
            st.session_state.page = "Dashboard"
            st.experimental_rerun()
    else:
        st.info("Please upload a PDF to start analysis.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Page: Dashboard
# ---------------------------
else:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header-box"><h2>📊 AI Dashboard</h2><div class="small-muted">Visuals, summaries and improvement suggestions</div></div>', unsafe_allow_html=True)

    parsed = st.session_state.parsed or {}
    if not parsed:
        st.warning("No parsed AI data found. Please go to Upload page and run analysis first.")
        if st.button("Go to Upload"):
            st.session_state.page = "Upload"
            st.experimental_rerun()
        st.stop()

    # Extract values with defaults
    faculty = parsed.get("faculty_percentage", 0)
    infra = parsed.get("infrastructure_percentage", 0)
    docs = parsed.get("document_percentage", 0)
    other = parsed.get("other_percentage", 0)
    total = parsed.get("total_percentage", 0)

    # Summaries
    summary = parsed.get("summary", "")
    faculty_summary = parsed.get("faculty_summary", "")
    infra_summary = parsed.get("infrastructure_summary", "")
    doc_summary = parsed.get("document_summary", "")
    other_summary = parsed.get("other_summary", "")
    overall_summary = parsed.get("overall_summary", "")

    st.markdown(f"**Final Approval Percentage:**  **{total:.2f}%**")
    st.write("")

    # Chart data
    metrics = ["Faculty", "Infrastructure", "Documents", "Other"]
    scores = [faculty, infra, docs, other]
    blue = "#1f6feb"
    light_blue = "#dbeafe"

    # Chart viewer controls (one by one)
    charts = ["Bar Chart", "Pie Chart", "Line Chart", "Radar Chart"]
    idx = st.session_state.chart_index

    st.markdown("### Charts Viewer")
    st.markdown("Use Next / Previous to view charts one at a time.")
    col1, col2, col3 = st.columns([1,1,6])
    with col1:
        if st.button("Previous"):
            st.session_state.chart_index = (st.session_state.chart_index - 1) % len(charts)
            st.experimental_rerun()
    with col2:
        if st.button("Next"):
            st.session_state.chart_index = (st.session_state.chart_index + 1) % len(charts)
            st.experimental_rerun()
    with col3:
        st.markdown(f"**Showing**: {charts[idx]}")

    st.write("")  # spacing

    # Render selected chart
    if charts[idx] == "Bar Chart":
        fig, ax = plt.subplots(figsize=(8,4), facecolor="white")
        bars = ax.bar(metrics, scores, color=blue, edgecolor="#0b4fd6")
        ax.set_ylim(0,100)
        ax.set_ylabel("Score (%)")
        ax.set_title("Performance by Metric", color="#0b3b8c")
        ax.grid(axis="y", linestyle="--", alpha=0.2)
        for bar, val in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width()/2, val + 1, f"{val:.1f}%", ha="center", color="#0b3b8c")
        st.pyplot(fig)

    elif charts[idx] == "Pie Chart":
        fig2, ax2 = plt.subplots(figsize=(6,6), facecolor="white")
        colors = [blue, "#60a5fa", "#93c5fd", light_blue]
        ax2.pie(scores, labels=metrics, autopct="%1.1f%%", colors=colors, textprops={'color':"#0b3b8c"})
        ax2.set_title("Score Distribution", color="#0b3b8c")
        st.pyplot(fig2)

    elif charts[idx] == "Line Chart":
        fig3, ax3 = plt.subplots(figsize=(8,4), facecolor="white")
        ax3.plot(metrics, scores, marker='o', color=blue, linewidth=2)
        ax3.fill_between(metrics, scores, color=light_blue, alpha=0.4)
        ax3.set_ylim(0,100)
        ax3.set_ylabel("Score (%)")
        ax3.set_title("Trend Across Metrics", color="#0b3b8c")
        for x,y in zip(metrics, scores):
            ax3.text(x, y+1, f"{y:.1f}%", ha="center", color="#0b3b8c")
        ax3.grid(alpha=0.15)
        st.pyplot(fig3)

    else:  # Radar Chart
        labels = metrics
        values = scores[:]
        angles = [n / float(len(labels)) * 2 * 3.14159265 for n in range(len(labels))]
        values += values[:1]
        angles += angles[:1]

        fig4 = plt.figure(figsize=(6,6), facecolor="white")
        ax4 = fig4.add_subplot(111, polar=True)
        ax4.plot(angles, values, color=blue, linewidth=2)
        ax4.fill(angles, values, color=light_blue, alpha=0.4)
        ax4.set_xticks(angles[:-1])
        ax4.set_xticklabels(labels, color="#0b3b8c")
        ax4.set_yticklabels([])
        ax4.set_title("Radar View of Metrics", color="#0b3b8c", y=1.08)
        st.pyplot(fig4)

    st.write("")  # spacing

    # =========================
    # Summaries section — separate boxes
    # =========================
    st.markdown("### Summaries")
    # Main summary box
    st.markdown(f"""
        <div class="summary-box">
            <div class="summary-title">📌 Summary</div>
            <div class="summary-text">{summary or 'No summary available.'}</div>
        </div>
    """, unsafe_allow_html=True)

    # Faculty summary box
    st.markdown(f"""
        <div class="summary-box">
            <div class="summary-title">👩‍🏫 Faculty Summary</div>
            <div class="summary-text">{faculty_summary or 'No faculty summary available.'}</div>
        </div>
    """, unsafe_allow_html=True)

    # Infrastructure summary box
    st.markdown(f"""
        <div class="summary-box">
            <div class="summary-title">🏫 Infrastructure Summary</div>
            <div class="summary-text">{infra_summary or 'No infrastructure summary available.'}</div>
        </div>
    """, unsafe_allow_html=True)

    # Document summary box
    st.markdown(f"""
        <div class="summary-box">
            <div class="summary-title">📄 Document Summary</div>
            <div class="summary-text">{doc_summary or 'No document summary available.'}</div>
        </div>
    """, unsafe_allow_html=True)

    # Other summary box
    st.markdown(f"""
        <div class="summary-box">
            <div class="summary-title">🎯 Other Summary</div>
            <div class="summary-text">{other_summary or 'No other summary available.'}</div>
        </div>
    """, unsafe_allow_html=True)

    # Overall summary box
    st.markdown(f"""
        <div class="summary-box">
            <div class="summary-title">🌐 Overall Summary</div>
            <div class="summary-text">{overall_summary or 'No overall summary available.'}</div>
        </div>
    """, unsafe_allow_html=True)

    st.write("")  # spacing

    # AI Suggestions (generate on demand)
    st.markdown("### AI Suggestions to Improve")
    if st.session_state.suggestions:
        st.info(st.session_state.suggestions)
    else:
        if st.button("Generate Suggestions from AI"):
            with st.spinner("Generating suggestions..."):
                summaries_text = "\n".join([faculty_summary, infra_summary, doc_summary, other_summary, overall_summary])
                suggestions_text = generate_suggestions(parsed, summaries_text)
                st.session_state.suggestions = suggestions_text
                st.experimental_rerun()

    st.write("")  # spacing
    if st.button("Back to Upload"):
        st.session_state.page = "Upload"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer">🚀 Powered by Gemini AI | Built for AICTE & UGC Institutional Intelligence</div>', unsafe_allow_html=True)
