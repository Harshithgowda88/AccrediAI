import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import pandas as pd
import matplotlib.pyplot as plt
import json, re
from google import genai

# =========================================================
# Load API Keys
# =========================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# =========================================================
# Helper Functions
# =========================================================
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def analyze_with_ai(pdf_text):
    prompt = f"""
    You are an AI reviewer for UGC/AICTE approval.
    Return ONLY valid JSON with keys:
    - faculty_percentage (0-100)
    - infrastructure_percentage (0-100)
    - document_percentage (0-100)
    - other_percentage (0-100)
    - total_percentage (0-100)
    - summary (short text)
    - faculty_summary (5–10 lines about faculty: number of PhD holders, professors, associate professors, assistant professors, teaching quality, etc.)
    - infrastructure_summary (5–10 lines about infrastructure: labs, classrooms, library, campus facilities, digital resources, etc.)
    - document_summary (5–10 lines about documents: research papers, approvals, accreditation, student records, etc.)
    - other_summary (5–10 lines about other aspects: extracurriculars, community engagement, innovation, etc.)
    - overall_summary (5–10 lines summarizing the institution’s overall strengths and weaknesses) important

    Text:
    {pdf_text}
    """
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def safe_parse_json(ai_result):
    """Extract JSON safely even if AI adds extra text"""
    try:
        match = re.search(r"\{.*\}", ai_result, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return {}
    except Exception as e:
        st.error(f"Could not parse AI output as JSON. Error: {e}")
        return {}
    
    st.set_page_config(
    page_title="AccrediAI - Institutional Intelligence System",
    page_icon="🎓",
    layout="wide"
)

# =========================================================
# Streamlit UI
# =========================================================

st.markdown("""
<style>
.main { background: linear-gradient(to right, #eef2ff, #f8fafc); }
.stApp { background-color: #f4f7fb; }
.main-title { font-size: 48px; font-weight: 800; text-align: center; color: #1e3a8a; margin-bottom: 10px; }
.sub-title { text-align: center; font-size: 20px; color: #475569; margin-bottom: 40px; }
.upload-box { padding: 25px; border-radius: 20px; background: white; box-shadow: 0px 4px 20px rgba(0,0,0,0.08); margin-bottom: 25px; }
.metric-card { background: white; padding: 20px; border-radius: 18px; text-align: center; box-shadow: 0px 4px 18px rgba(0,0,0,0.08); transition: 0.3s; }
.metric-card:hover { transform: translateY(-5px); }
.metric-title { font-size: 18px; color: #475569; font-weight: 600; }
.metric-value { font-size: 38px; font-weight: bold; color: #2563eb; }
.summary-box { background: white; padding: 25px; border-radius: 20px; box-shadow: 0px 4px 18px rgba(0,0,0,0.08); margin-top: 20px; }
.section-heading { font-size: 28px; font-weight: bold; color: #1e293b; margin-bottom: 15px; }
.footer { text-align: center; margin-top: 40px; color: gray; font-size: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">🎓 AccrediAI</div>
<div class="sub-title">AI-Powered Institutional Accreditation & Performance Intelligence System</div>
""", unsafe_allow_html=True)



uploaded_file = st.file_uploader("Upload SSR/SST PDF", type=["pdf"])

if uploaded_file:
    st.info("Extracting text from PDF...")
    pdf_text = extract_text_from_pdf(uploaded_file)
    st.success("Text extracted successfully!")

    st.info("Analyzing with Gemini AI...")
    ai_result = analyze_with_ai(pdf_text)

    st.subheader("🔍 AI Review Result (Raw)")
    st.write(ai_result)   # optional: shows raw AI output

    # ✅ Parse JSON safely
    result_json = safe_parse_json(ai_result)

    faculty_percentage = result_json.get("faculty_percentage", 0)
    infrastructure_percentage = result_json.get("infrastructure_percentage", 0)
    document_percentage = result_json.get("document_percentage", 0)
    other_percentage = result_json.get("other_percentage", 0)
    total_percentage = result_json.get("total_percentage", 0)
    summary = result_json.get("summary", "")
    faculty_summary = result_json.get("faculty_summary","")
    infrastructure_summary = result_json.get("infrastructure_summary","")
    document_summary = result_json.get("document_summary","")
    other_summary = result_json.get("other_summary","")
    overall_summary = result_json.get("overall_summary","")

    # =========================================================
    # Custom CSS for Styling
    # =========================================================
    st.markdown("""
        <style>
        body {
            background-color: #f8f8ff; /* light purple-white tone */
            font-family: 'Open Sans', sans-serif;
        }
        .header-box {
            background: linear-gradient(135deg, #6a0dad, #ffffff);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            text-align: center;
            color: black;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
        }
        .summary-box {
            background: linear-gradient(135deg, #e6e6fa, #ffffff);
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
            color: black;
        }
        .summary-box h3 {
            margin-top: 0;
            color: #4b0082; /* elegant purple heading */
        }
        </style>
    """, unsafe_allow_html=True)

    # =========================
    # Header Section
    # =========================
    st.markdown(f"""
        <div class="header-box">
            <h1>AccrediAI Dashboard</h1>
            <p>AI-Based Institutional Performance Analyzer</p>
        </div>
    """, unsafe_allow_html=True)

    # ✅ Dashboard
    st.subheader("📈 Performance Indicators")
    data = {
        "Metric": ["Faculty %", "Infrastructure %", "Document %", "Other %", "Total Approval %"],
        "Score": [faculty_percentage, infrastructure_percentage, document_percentage, other_percentage, total_percentage]
    }
    df = pd.DataFrame(data)

    fig, ax = plt.subplots(figsize=(8,5))
    ax.bar(df["Metric"], df["Score"], color="#6a0dad")  # purple bars
    ax.set_ylabel("Score (%)")
    ax.set_ylim(0, 100)
    plt.xticks(rotation=30, ha="right")
    st.pyplot(fig)

    st.success(f"✅ Final Approval Percentage: {total_percentage:.2f}%")

    st.markdown("## 📈 AI Analytics Visualization")
    df = pd.DataFrame({
        "Metric": ["Faculty", "Infrastructure", "Documents", "Innovation"],
        "Score": [faculty_percentage, infrastructure_percentage, document_percentage, other_percentage]
    })

    colA, colB = st.columns(2)
    with colA:
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(df["Metric"], df["Score"], color="#6a0dad")
        ax.set_ylim(0,100)
        ax.set_ylabel("Performance %")
        st.pyplot(fig)

    with colB:
        fig2, ax2 = plt.subplots(figsize=(6,4))
        ax2.pie(df["Score"], labels=df["Metric"], autopct='%1.1f%%')
        st.pyplot(fig2)

    # =========================
    # Summary Boxes
    # =========================
    st.markdown(f"""
        <div class="summary-box">
            <h3>📌 Summary</h3>
            <p>{summary}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="summary-box">
            <h3>👩‍🏫 Faculty Summary</h3>
            <p>{faculty_summary}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="summary-box">
            <h3>🏫 Infrastructure Summary</h3>
            <p>{infrastructure_summary}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="summary-box">
            <h3>📄 Document Summary</h3>
            <p>{document_summary}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="summary-box">
            <h3>🎯 Other Summary</h3>
            <p>{other_summary}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="summary-box">
            <h3>🌐 Overall Summary</h3>
            <p>{overall_summary}</p>
        </div>
    """, unsafe_allow_html=True)



st.markdown("""
<div class="footer">🚀 Powered by Gemini AI | Built for AICTE & UGC Institutional Intelligence</div>
""", unsafe_allow_html=True)