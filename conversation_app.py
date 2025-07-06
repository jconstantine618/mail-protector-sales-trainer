import streamlit as st
import os
import sys
import json
import random
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from openai import OpenAI

# --- This line loads your local .env file ---
load_dotenv()

# --- CONFIGURATION ---
AGENT_ID = "agent_01jzdff6g6mehda95hx56cc5pwd" 

# --- Page Configuration ---
st.set_page_config(
    page_title="Sales Trainer AI",
    page_icon="🎙️",
    layout="wide"
)

# --- Helper Functions ---
def load_prospects(file_path='data/prospects.json'):
    """Loads prospect profiles from the specified JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: The file '{file_path}' contains invalid JSON.")
        return None

def get_conversation_analysis(transcript: str, api_key: str):
    """
    Sends the transcript to an LLM to be scored and returns the analysis.
    """
    client = OpenAI(api_key=api_key)
    system_prompt = """
    You are an expert sales coach, deeply familiar with Dale Carnegie's principles, the Sandler model, and the Challenger Sale.
    Your task is to analyze the provided sales call transcript. Evaluate the salesperson's performance based on the following criteria:
    1. Rapport Building (Carnegie Principles): Did they show genuine interest, use the prospect's name, and make them feel important?
    2. Needs Discovery (Sandler/Challenger): Did they ask open-ended questions to uncover deep pain points? Did they reframe the problem or teach the prospect something new?
    3. Handling Objections: Did they validate concerns instead of arguing? Did they reframe price around value?
    4. Closing: Did they propose a clear, collaborative next step?

    Provide your response ONLY in a valid JSON object format with the following keys:
    - "overall_score": A number from 0 to 100.
    - "category_scores": An object with scores for each category (e.g., {"Rapport Building": 8, "Needs Discovery": 7, "Handling Objections": 6, "Closing": 8}).
    - "feedback_summary": A concise paragraph summarizing the salesperson's performance.
    - "strengths": A list of 2-3 bullet points on what the salesperson did well.
    - "areas_for_improvement": A list of 2-3 specific, actionable suggestions for improvement.
    """
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please analyze this transcript: \n\n{transcript}"}
        ]
    )
    analysis = json.loads(response.choices[0].message.content)
    return analysis

# --- Session State Initialization ---
if 'prospect' not in st.session_state:
    st.session_state.prospect = None

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("Configuration")
    
    # --- API Key Handling ---
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if 'ELEVENLABS_API_KEY' in st.secrets and 'OPENAI_API_KEY' in st.secrets:
        elevenlabs_api_key = st.secrets["ELEVENLABS_API_KEY"]
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        st.sidebar.success("API keys loaded from Streamlit Secrets.", icon="✅")
    elif elevenlabs_api_key and openai_api_key:
        st.sidebar.info("API keys loaded from local .env file.", icon="ℹ️")
    else:
        st.sidebar.error("API Keys not found. Please add ELEVENLABS_API_KEY and OPENAI_API_KEY to your secrets or a local .env file.")
        st.stop()
    
    st.info(f"Agent ID: {AGENT_ID}")
    st.divider()
    
    # --- Prospect Loading ---
    prospects = load_prospects()
    if prospects:
        if st.button("Load New Random Prospect"):
            st.session_state.prospect = random.choice(prospects)
            st.rerun()

# --- Main App Body ---
st.title("🎙️ AI Sales Call Trainer")
st.write("Use the sidebar to load a prospect. Review their details, launch the widget to have a practice call, then paste the transcript below for analysis.")
st.divider()

if st.session_state.prospect:
    prospect = st.session_state.prospect
    with st.expander("Show Prospect Details", expanded=True):
        st.subheader(prospect['prospect_name'])
        st.write(f"**Role:** {prospect['prospect_role']}")
        st.write(f"**Company:** {prospect['company_name']} ({prospect['company_industry']})")
        st.write(f"**Disposition:** {prospect['disposition']}")
        st.write(f"**Pain Point 1:** {prospect['pain_point_1']}")
        st.write(f"**Pain Point 2:** {prospect['pain_point_2']}")
    
    st.divider()

    # --- Conversation Launch Button ---
    st.link_button("▶️ Launch Conversation Widget in New Tab", "https://revival-care.squarespace.com/", type="primary")

else:
    st.info("Click 'Load New Random Prospect' in the sidebar to begin your training session.")

# --- Analysis Section ---
st.divider()
st.header("✅ Conversation Analysis & Scoring")

transcript_text = st.text_area("After your call, paste the full conversation transcript here:", height=300)

if st.button("Analyze and Score Conversation", type="secondary"):
    if transcript_text:
        with st.spinner("Your AI Sales Coach is analyzing the call..."):
            try:
                analysis_results = get_conversation_analysis(transcript_text, openai_api_key)

                st.subheader("🏆 Your Score")
                st.metric("Overall Score", f"{analysis_results['overall_score']}/100")

                st.subheader("📝 Feedback Summary")
                st.write(analysis_results['feedback_summary'])

                st.subheader("👍 Strengths")
                for strength in analysis_results['strengths']:
                    st.markdown(f"- {strength}")

                st.subheader("💡 Areas for Improvement")
                for improvement in analysis_results['areas_for_improvement']:
                    st.markdown(f"- {improvement}")

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
    else:
        st.warning("Please paste a transcript to analyze.")