import streamlit as st
import pandas as pd
import json
import plotly.express as px
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="SprintGuard AI", layout="wide", page_icon="🛡️")

# --- CUSTOM CSS FOR "AI" FEEL ---
st.markdown("""
    <style>
   /* Style for the Red Risk Card */
   .risk-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #4a1c1c; /* Dark Red Background */
        border-left: 5px solid #ff4b4b; /* Bright Red Accent */
        margin-bottom: 20px;
    }
    /* Force all text inside the risk card to be white/light */
    .risk-card h3 {
        color: white !important;
        margin-top: 0;
    }
    .risk-card p {
        color: #e0e0e0 !important;
    }
    
    /* Style for the Refresh Button to make it look cleaner */
    div.stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. DATA LOADING (SIMULATING DATABASE) ---
@st.cache_data
def load_data():
    with open('mock_data.json', 'r') as f:
        return json.load(f)

# Load data safely
try:
    data = load_data()
    sprint = data['sprint_info']
    tickets = data['tickets']
except FileNotFoundError:
    st.error("Error: mock_data.json not found. Please make sure the file exists in the same folder.")
    st.stop()

# --- 2. SIDEBAR (CONTEXT) ---
with st.sidebar:
    st.title("🛡️ SprintGuard AI")
    st.caption("Active Monitoring Mode")
    
    st.markdown("---")
    st.subheader("Sprint Context")
    st.write(f"**Sprint:** {sprint['name']}")
    st.write(f"**Day:** {sprint['day']} of {sprint['total_days']}")
    st.progress(sprint['day']/sprint['total_days'])
    
    st.markdown("---")
    st.info("**AI Insight:** We are on Day 7. Historically, risky tickets flagged today have a 90% spillover rate if not addressed within 24h.")

# --- 3. MAIN HEADER & REFRESH BUTTON ---
# We use columns to separate the Text (Left) from the Button (Right)
# [3, 1] means the left side takes up 75% of space, right side takes 25%
col1, col2 = st.columns([3, 1])

with col1:
    st.title("Good Morning, Ketan.")
    st.write("Here is your daily intervention briefing.")

with col2:
    # Adding a little spacing so the button aligns with the text better
    st.write("") 
    st.write("") 
    if st.button("🔄 Refresh Data Sources"):
        with st.spinner('Syncing Jira... Syncing GitHub... Syncing GCal...'):
            time.sleep(1.5)
        st.toast("Sync Complete!", icon="✅")

st.markdown("---")

# --- 4. METRICS ROW ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Sprint Velocity", "32 pts", "On Track")
m2.metric("Completion", "65%", "-5% vs Plan")
m3.metric("Blockers Detected", "1", "Requires Action", delta_color="inverse")
m4.metric("Team Sentiment", "Neutral", "- Trending Down") 

st.markdown("---")

# --- 5. THE AI INTERVENTION LAYER ---
st.subheader("🚨 AI Detected Risks (1)")

# Find the risky ticket
risky_ticket = next((t for t in tickets if t['risk_score'] > 90), None)

if risky_ticket:
    # Create a specialized container for the alert
    with st.container():
        # Render the Risk Card with HTML/CSS
        st.markdown(f"""
        <div class="risk-card">
            <h3>⚠️ Intervention Needed: {risky_ticket['id']} - {risky_ticket['title']}</h3>
            <p><b>Assignee:</b> {risky_ticket['assignee']} | <b>Status:</b> {risky_ticket['status']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.write("#### 🕵️‍♂️ Why AI flagged this?")
            st.error(f"**Anomaly Detected:** {risky_ticket['risk_reason']}")
            
            # Visualizing the discrepancy
            st.caption("Activity vs Status Discrepancy (Projected vs Actual):")
            
            # 1. CREATE FAKE TIME-SERIES DATA (Days 1-7)
            # We construct a DataFrame that shows the 'story' of the sprint so far
            line_data = pd.DataFrame({
                "Day": [1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5, 6, 7],
                "Completion %": [10, 25, 40, 55, 65, 75, 85,  # Jira (Steadily climbing)
                                 10, 25, 25, 25, 25, 25, 25], # Git (Stalled at Day 2)
                "Source": ["Jira Status"] * 7 + ["Git Activity"] * 7
            })
            
            # 2. BUILD THE LINE CHART
            fig = px.line(line_data, x="Day", y="Completion %", color="Source", markers=True,
                          color_discrete_map={"Jira Status": "#00cc96", "Git Activity": "#ff4b4b"})
            
            # 3. FIX THE AXES (Show full 10-day sprint)
            fig.update_xaxes(range=[0.5, 10.5], dtick=1, title="Sprint Day (Current: Day 7)")
            fig.update_yaxes(range=[0, 105]) # Go slightly above 100 for visual breathing room

            # 4. FIX THE LEGEND (Move to bottom center)
            fig.update_layout(
                legend=dict(
                    orientation="h",      # Horizontal
                    yanchor="top",        
                    y=-0.2,               # Push it below the x-axis
                    xanchor="center",     
                    x=0.5                 # Center it
                ),
                margin=dict(l=20, r=20, t=20, b=20), # Tighten margins
                hovermode="x unified"     # Show both values when hovering over a day
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.write("#### 🤖 Suggested AI Intervention")
            st.info("The engineer has 6h of meetings today. They are likely context-switching too much to code.")
            
            tab1, tab2 = st.tabs(["Draft Message", "Re-assign"])
            
            with tab1:
                st.text_area("Draft Slack Message:", 
                    value=f"Hey {risky_ticket['assignee']}, SprintGuard noticed ticket {risky_ticket['id']} has been 'In Progress' for 4 days without git activity. I see your calendar is slammed with meetings. Do you need me to clear your schedule or should we reduce scope here?",
                    height=150
                )
                if st.button("🚀 Send Message via Slack"):
                    st.toast(f"Message sent to {risky_ticket['assignee']}!", icon="✅")
                    time.sleep(1)
                    st.balloons()

            with tab2:
                st.warning("Re-assigning late in sprint is not recommended.")
else:
    st.success("No critical risks detected at this moment.")

st.markdown("---")

# --- 6. THE REST OF THE BOARD (Standard View) ---
st.subheader("✅ Healthy Work Stream")
for ticket in tickets:
    if ticket['risk_score'] < 50:
        with st.expander(f"{ticket['id']}: {ticket['title']} ({ticket['assignee']})"):
            st.write(f"Status: {ticket['status']}")
            st.write(f"Git Activity: {ticket['git_commits']} commits")
            st.success("AI Analysis: Progress matches Git activity. No risk detected.")

