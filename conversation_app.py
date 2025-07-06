import streamlit as st
import os
import sys
import json
import random
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational import Conversation

# --- Page Configuration ---
st.set_page_config(
    page_title="Sales Trainer AI",
    page_icon="🎙️",
    layout="wide"
)

# --- Helper Function to Load Prospects ---
def load_prospects(file_path='data/prospects.json'):
    """Loads prospect profiles from the specified JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found.")
        st.error("Please make sure your Python script is in the 'mail-protector-sales-trainer' root directory.")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: The file '{file_path}' contains invalid JSON. Please check its formatting.")
        return None

# --- Session State Initialization ---
if 'prospect' not in st.session_state:
    st.session_state.prospect = None
    st.session_state.conversation_obj = None
    st.session_state.running = False
    st.session_state.transcript = []

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("Configuration")
    
    # --- API Key Handling ---
    try:
        # For Streamlit Community Cloud deployment
        st.session_state.api_key = st.secrets["ELEVENLABS_API_KEY"]
        st.success("ElevenLabs API Key loaded from secrets.", icon="✅")
    except (KeyError, AttributeError):
        # For local development
        st.session_state.api_key = os.getenv("ELEVENLABS_API_KEY")
        if st.session_state.api_key:
            st.info("ElevenLabs API Key loaded from local .env file.", icon="ℹ️")
        else:
            st.error("ELEVENLABS_API_KEY not found. Please add it to your Streamlit secrets or a local .env file.")
            st.stop()

    # --- Agent ID Input ---
    st.session_state.agent_id = st.text_input("ElevenLabs Agent ID:", value="YOUR_AGENT_ID")

    st.divider()
    
    # --- Prospect Loading ---
    prospects = load_prospects()
    if prospects:
        if st.button("Load New Random Prospect"):
            st.session_state.prospect = random.choice(prospects)
            # Reset conversation if we load a new prospect
            st.session_state.running = False
            st.session_state.transcript = []
            st.session_state.conversation_obj = None

# --- Main App Body ---
st.title("🎙️ AI Sales Call Trainer")

if st.session_state.prospect:
    prospect = st.session_state.prospect
    with st.expander("Show Prospect Details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(prospect['prospect_name'])
            st.write(f"**Role:** {prospect['prospect_role']}")
            st.write(f"**Company:** {prospect['company_name']} ({prospect['company_industry']})")
        with col2:
            st.write(f"**Disposition:** {prospect['disposition']}")
            st.write(f"**Pain Point 1:** {prospect['pain_point_1']}")
            st.write(f"**Pain Point 2:** {prospect['pain_point_2']}")
    
    st.divider()

    # --- Conversation Controls ---
    if not st.session_state.running:
        if st.button("▶️ Start Conversation", type="primary"):
            if st.session_state.agent_id == "YOUR_AGENT_ID":
                st.warning("Please enter your ElevenLabs Agent ID in the sidebar.")
            else:
                st.session_state.running = True
                # Here we would normally start the conversation.
                # In a real-world, complex Streamlit app, this would involve
                # background processes or websockets to handle the audio stream.
                # For this framework, we'll just update the state.
                st.rerun()
    else:
        if st.button("⏹️ Stop Conversation"):
            st.session_state.running = False
            # Logic to gracefully stop the conversation
            st.session_state.conversation_obj = None # Reset
            st.success("Conversation stopped. A full transcript would be saved here.")
            st.rerun()

    # --- Transcript Display ---
    st.subheader("Live Transcript")
    if st.session_state.running:
        st.info("Conversation in progress... Start speaking into your microphone.")
        st.warning("NOTE: This is a UI framework. The real-time audio streaming from the original script is not fully implemented here due to web architecture complexities.")
    
    # This area would be dynamically updated with the transcript
    transcript_area = st.container(height=300)
    with transcript_area:
        for message in st.session_state.transcript:
            st.write(message)

else:
    st.info("Click 'Load New Random Prospect' in the sidebar to begin a training session.")
