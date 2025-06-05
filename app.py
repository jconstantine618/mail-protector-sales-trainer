import streamlit as st
import openai
import os
import json
import pathlib
import time
import sqlite3
import datetime
import base64
from gtts import gTTS

# ── DATABASE SETUP ─────────────────────────────────────
DB_PATH = pathlib.Path(__file__).parent / "leaderboard.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    score INTEGER,
    timestamp TEXT
)
""")
conn.commit()

# ── SALES PILLARS & SCORING ─────────────────────────────
PILLARS = {
    "rapport": ["i understand", "great question", "thank you for sharing", "appreciate"],
    "pain":    ["challenge", "issue", "pain point", "concern", "problem"],
    "needs":   ["what system", "how much time", "are you confident", "success look", "goals"],
    "teach":   ["did you know", "we've seen", "benchmark", "tailor", "in our experience"],
    "close":   ["demo", "free trial", "does this sound", "next step", "move forward"]
}

FEEDBACK_HINTS = {
    "rapport": "Work on building rapport: show empathy, thank them, mirror language.",
    "pain":    "Ask more about challenges or frustrations to uncover deeper pain points.",
    "needs":   "Missed discovery—ask what success looks like and usage details.",
    "teach":   "Provide a quick insight or customer story that reframes their thinking.",
    "close":   "Include a clear next step like a demo, trial, or proposal to close."
}

COMPLIMENTS = {
    "rapport": "Great rapport building—your tone is warm and engaging.",
    "pain":    "Excellent uncovering of core challenges.",
    "needs":   "Strong discovery questions—nicely done.",
    "teach":   "You provided valuable insights that reframed the problem.",
    "close":   "Strong close! You confidently moved to next steps."
}

DEAL_OBJECTIONS = ["budget", "timing", "vendor", "implementation", "support", "approval"]

def calc_score(msgs):
    counts = {p: 0 for p in PILLARS}
    convo_texts = []
    for m in msgs:
        if m["role"] != "user":
            continue
        txt = m["content"].lower()
        convo_texts.append(txt)
        for p, kws in PILLARS.items():
            if any(k in txt for k in kws):
                counts[p] += 1

    sub_scores = {p: min(v, 3) * (20 / 3) for p, v in counts.items()}
    total = int(sum(sub_scores.values()))

    brief_fb = [
        f"{'✅' if sub_scores[p] >= 10 else '⚠️'} {p.title()} {int(sub_scores[p])}/20"
        for p in PILLARS
    ]

    details = []
    for p in PILLARS:
        pts = sub_scores[p]
        details.append(
            f"**{p.title()}**: " + (COMPLIMENTS[p] if pts >= 15 else FEEDBACK_HINTS[p])
        )

    convo = " ".join(convo_texts)
    found = [o for o in DEAL_OBJECTIONS if o in convo]
    missed = [o for o in DEAL_OBJECTIONS if o not in convo]
    obj_summary = (
        f"**Objections uncovered:** {', '.join(found) or 'None'}\n"
        f"**Objections missed:** {', '.join(missed) or 'None'}"
    )

    detailed_fb = "\n\n".join(details + [obj_summary])
    return total, "\n".join(brief_fb), sub_scores, detailed_fb

def generate_follow_up(sub_scores, scenario, persona):
    name = persona["persona_name"]
    comp = scenario["prospect"]
    total = int(sum(sub_scores.values()))
    close_pts = sub_scores.get("close", 0)
    rapport_pts = sub_scores.get("rapport", 0)
    pain_pts = sub_scores.get("pain", 0)

    if total >= 75 and close_pts >= 10:
        return f"You and {name} agreed to review a proposal together. {comp} is now a client."
    elif total >= 50 and close_pts >= 5:
        return f"{name} requested detailed pricing and scheduled a follow-up. Next steps are set."
    elif total >= 35 and rapport_pts >= 10 and pain_pts >= 5:
        return f"You followed up by email; {name} is reviewing internally and may reconnect later."
    else:
        return f"You left a voicemail and emailed, but heard nothing. After two weeks, {name} likely moved on."

# ── TIMER HELPERS ─────────────────────────────────────

def init_timer():
    if "start" not in st.session_state:
        st.session_state.start = time.time()
        st.session_state.cut = False


def show_timer(window):
    elapsed = (time.time() - st.session_state.start) / 60
    remaining = max(0, window - elapsed)
    st.sidebar.markdown("### ⏱️ Time Remaining")
    if remaining <= 1:
        st.sidebar.warning("⚠️ <1 minute left")
    elif remaining <= 3:
        st.sidebar.info(f"⏳ {int(remaining)} min left")
    else:
        st.sidebar.write(f"{int(remaining)} minutes left")
    return elapsed >= window

# ── OPENAI CLIENT ─────────────────────────────────────
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Missing API key")
    st.stop()
client = openai.OpenAI(api_key=api_key)

# ── LOAD Mail Protector SCENARIOS ───────────────────────────
DATA_PATH = pathlib.Path(__file__).parent / "data" / "mailprotector_scenarios.json"
SCENARIOS = json.loads(DATA_PATH.read_text())

# ── PAGE SETUP ────────────────────────────────────────
st.set_page_config(page_title="Mail Protector Sales Trainer", page_icon="💬")
st.title("💬 Mail Protector Sales Training Chatbot")

# ── DOWNLOAD PLAYBOOK BUTTON (TEXT NOW WHITE) ────────
pdf_path = pathlib.Path(__file__).parent / "TPA Solutions Play Book.pdf"
if pdf_path.exists():
    b64 = base64.b64encode(pdf_path.read_bytes()).decode()
    st.sidebar.markdown(
        f'<a href="data:application/pdf;base64,{b64}" download="MailProtector_Playbook.pdf" '
        f'style="text-decoration:none;color:white;">'
        f'<div style="background:#d32f2f;padding:8px;border-radius:4px;'
        f'text-align:center;color:white;">'
        f'Download Sales Playbook</div></a>',
        unsafe_allow_html=True
    )

# ── SCENARIO & PERSONA SELECTION ─────────────────────
scenario_names = [f"{s['id']}. {s['prospect']} ({s['category']})" for s in SCENARIOS]
choice = st.sidebar.selectbox("Choose a scenario", scenario_names)
scenario = SCENARIOS[scenario_names.index(choice)]
if st.session_state.get("scenario") != choice:
    st.session_state.clear()
    st.session_state.scenario = choice

plist = scenario["decision_makers"]
pidx = st.sidebar.selectbox(
    "Which decision-maker?",
    options=list(range(len(plist))),
    format_func=lambda i: f"{plist[i]['persona_name']} ({plist[i]['persona_role']})",
    index=st.session_state.get("persona_idx", 0)
)
st.session_state.persona_idx = pidx
persona = plist[pidx]

# ── BUILD SYSTEM PROMPT ──────────────────────────────

def build_prompt(scenario, persona):
    tl = {"Easy": 10, "Medium": 15, "Hard": 20}[scenario["difficulty"]["level"]]
    others = [p["persona_name"] for p in plist if p != persona]
    note = f"You know {', '.join(others)} is another stakeholder." if others else ""
    pains = ", ".join(persona["pain_points"])
    return f"""
You are **{persona['persona_name']}**, the **{persona['persona_role']}** at **{scenario['prospect']}**.
• Background: {persona['persona_background']}; Pain points: {pains}.
• Difficulty: {scenario['difficulty']['level']} → {tl} minutes.
• {note}

**IMPORTANT:**  
• You are NOT the product expert—do NOT explain technical implementation details.  
• Defer specifics back to the rep: “I’m not sure—could you clarify that?”  
• Speak only as this persona: voice objections, ask clarifying questions, respect time.

Stay in character.
""".strip()


prompt = build_prompt(scenario, persona)
init_timer()
if "msgs" not in st.session_state:
    st.session_state.msgs = [{"role": "system", "content": prompt}]

# ── DISPLAY INFO ─────────────────────────────────────
tl = {"Easy": 10, "Medium": 15, "Hard": 20}[scenario["difficulty"]["level"]]
st.markdown(f"""
**Persona:** {persona['persona_name']} ({persona['persona_role']})  
**Company:** {scenario['prospect']}  
**Time Available:** {tl} min  
""")

# ── CHAT LOOP ─────────────────────────────────────────
user_input = st.chat_input("Your message to the prospect")
if user_input and not st.session_state.get("closed", False):
    st.session_state.msgs.append({"role": "user", "content": user_input})
    if show_timer(tl):
        st.session_state.msgs.append({"role": "assistant", "content": f"**{persona['persona_name']}**: Sorry, I need another meeting now."})
        st.session_state.closed = True
    else:
        lower = user_input.lower()
        switched = False
        for idx, p in enumerate(plist):
            if idx != pidx and p["persona_name"].lower() in lower:
                st.session_state.persona_idx = idx
                persona = plist[idx]
                prompt = build_prompt(scenario, persona)
                st.session_state.msgs[0] = {"role": "system", "content": prompt}
                st.session_state.msgs.append({"role": "assistant", "content": f"**{persona['persona_name']} ({persona['persona_role']}) has joined the meeting.**"})
                switched = True
                break
        if not switched:
            resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.msgs)
            st.session_state.msgs.append({"role": "assistant", "content": resp.choices[0].message.content.strip()})

# ── RENDER CHAT ───────────────────────────────────────
for m in st.session_state.msgs[1:]:
    st.chat_message("user" if m["role"] == "user" else "assistant").write(m["content"])
    if m["role"] == "assistant" and st.session_state.get("voice", False):
        gTTS(m["content"]).save("tmp.mp3")
        st.audio(open("tmp.mp3", "rb").read(), format="audio/mp3")

# ── SIDEBAR CONTROLS & SCORING ────────────────────────
voice = st.sidebar.checkbox("🎙️ Voice Mode", key="voice")
if st.sidebar.button("🔄 Reset Chat"):
    st.session_state.clear()
    st.rerun()

if st.sidebar.button("🔚 End & Score") and not st.session_state.get("closed", False):
    total, brief_fb, subs, detail_fb = calc_score(st.session_state.msgs)
    st.session_state.closed = True
    st.sidebar.success("Scored!")
    st.session_state.total = total
    st.session_state.sub_scores = subs
    st.session_state.detail_fb = detail_fb

# After scoring: outcome, breakdown, suggestions & leaderboard
if st.session_state.get("closed", False):
    # What Happened Next
    st.sidebar.markdown("### 📘 What Happened Next")
    st.sidebar.write(generate_follow_up(st.session_state.sub_scores, scenario, persona))

    # Score & breakdown
    st.sidebar.markdown("### 🏆 Your Score")
    st.sidebar.write(f"**{st.session_state.total}/100**")
    st.sidebar.markdown("### 📊 Breakdown")
    for p, pts in st.session_state.sub_scores.items():
        st.sidebar.write(f"{p.title()}: {int(pts)}/20")

    # Suggestions for Improvement
    st.sidebar.markdown("### 📣 Suggestions for Improvement")
    st.sidebar.write(st.session_state.detail_fb)

    # Leaderboard entry
    name = st.sidebar.text_input("Name:", key="name_input")
    if st.sidebar.button("🏅 Save to Leaderboard") and name:
        cur.execute(
            "INSERT INTO leaderboard(name, score, timestamp) VALUES (?, ?, ?)",
            (name, st.session_state.total, datetime.datetime.now().isoformat())
        )
        conn.commit()

    # Top 10 Leaderboard
    st.sidebar.markdown("### 🥇 Leaderboard")
    rows = cur.execute(
        "SELECT name, score FROM leaderboard ORDER BY score DESC, timestamp ASC LIMIT 10"
    ).fetchall()
    for i, (n, s) in enumerate(rows, start=1):
        st.sidebar.write(f"{i}. {n} — {s}")
