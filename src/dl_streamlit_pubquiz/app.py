import streamlit as st
import requests

# 1. Page Configuration (Forced centering for mobile optimization)
st.set_page_config(
    page_title="DS Team Quiz",
    page_icon="🧠",
    layout="centered"
)

# 2. Securely Fetch Credentials
# Locally, these pull from .streamlit/secrets.toml
# In production, these pull from your Streamlit Cloud Dashboard settings
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

# 3. Track Session State (Prevents users from re-submitting if they refresh)
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# App UI Header
st.title("🧠 Data Science Pub Quiz")
st.subheader("Round 1: Machine Learning & Stats")

# 4. App Flow Control
if st.session_state.submitted:
    st.success("🎉 Your answers have been locked into Notion! Waiting for the host...")
    st.balloons()
else:
    # Everything inside st.form stays frozen until the user hits the submit button
    with st.form("quiz_form"):
        st.write("### Step 1: Identify Your Team")
        team_name = st.text_input("What is your Team Name?", placeholder="e.g., The Overfitted Outliers")

        st.divider()
        st.write("### Step 2: Answer the Questions")

        # Question 1 (Using mobile-friendly segmented controls)
        q1_ans = st.segmented_control(
            "1. What does 'ReLU' stand for in neural networks?",
            options=["Rectified Linear Unit", "Regularized Linear Unit", "Relative Linear Utility"]
        )

        # Question 2
        q2_ans = st.segmented_control(
            "2. Is a Random Forest model fundamentally a bagging or boosting ensemble?",
            options=["Bagging", "Boosting", "Neither"]
        )

        st.divider()

        # Form Submission Button (stretching to full width makes it easier to tap on phones)
        submit_button = st.form_submit_button("Lock In Answers 🚀", use_container_width=True)

        # 5. Submission Logic
        if submit_button:
            # Frontend validation checks
            if not team_name:
                st.error("⚠️ Please enter a team name before submitting!")
            elif not q1_ans or not q2_ans:
                st.error("⚠️ Please answer all questions before submitting!")
            else:
                with st.spinner("Transmitting answers to the quizmaster..."):
                    # Notion API setup
                    url = "https://api.notion.com/v1/pages"
                    headers = {
                        "Authorization": f"Bearer {NOTION_TOKEN}",
                        "Content-Type": "application/json",
                        "Notion-Version": "2022-06-28"
                    }

                    # Map the form entries cleanly to Notion's exact database schema
                    payload = {
                        "parent": {"database_id": DATABASE_ID},
                        "properties": {
                            "Team Name": {
                                "title": [{"text": {"content": team_name}}]
                            },
                            "Q1 Answer": {
                                "rich_text": [{"text": {"content": q1_ans}}]
                            },
                            "Q2 Answer": {
                                "rich_text": [{"text": {"content": q2_ans}}]
                            }
                        }
                    }

                    try:
                        # Make the API call
                        response = requests.post(url, json=payload, headers=headers)

                        if response.status_code == 200:
                            # Update state so the quiz vanishes and showing the success banner
                            st.session_state.submitted = True
                            st.rerun()
                        else:
                            st.error(f"Notion API error ({response.status_code}): {response.text}")
                    except Exception as e:
                        st.error(f"Failed to connect to Notion: {e}")