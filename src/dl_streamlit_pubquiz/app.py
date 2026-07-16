import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Page Configuration (optimized for mobile)
st.set_page_config(
    page_title="DS Team Quiz",
    page_icon="🧠",
    layout="centered"
)

# 2. Establish Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Simple Session State to track if they have already submitted in this session
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# App Header
st.title("🧠 Data Science Pub Quiz")
st.subheader("Round 1: The Basics")

# If they already answered, show a success screen instead of the quiz
if st.session_state.submitted:
    st.success("🎉 Your answers have been locked in! Waiting for the host...")
    st.balloons()
else:
    # We wrap everything in a form so it only writes to the sheet when they hit "Submit"
    with st.form("quiz_form"):
        st.write("### Identify Your Team")
        team_name = st.text_input("What is your Team Name?", placeholder="e.g., Overfitted Outliers")

        st.divider()
        st.write("### Questions")

        # Question 1
        q1_ans = st.segmented_control(
            "1. Which activation function can suffer from the 'dying' problem?",
            options=["ReLU", "Sigmoid", "Tanh", "Leaky ReLU"]
        )

        # Question 2
        q2_ans = st.segmented_control(
            "2. In statistics, what is Type I error?",
            options=["False Negative", "False Positive", "Random Noise", "Overfitting"]
        )

        st.divider()
        # Submit Button
        submit_button = st.form_submit_button("Submit Answers 🚀", use_container_width=True)

        if submit_button:
            # Simple validation to make sure they filled everything out
            if not team_name:
                st.error("⚠️ Please enter a team name before submitting!")
            elif not q1_ans or not q2_ans:
                st.error("⚠️ Please answer all questions before submitting!")
            else:
                with st.spinner("Locking in your answers..."):
                    try:
                        # Fetch the existing data to append to it
                        existing_data = conn.read(ttl="0s")  # ttl=0s ensures we get fresh data

                        # Create a new row of data
                        new_row = pd.DataFrame([{
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "team_name": team_name,
                            "q1_answer": q1_ans,
                            "q2_answer": q2_ans
                        }])

                        # Combine and update
                        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                        conn.update(data=updated_df)

                        # Mark session as submitted so the form disappears
                        st.session_state.submitted = True
                        st.rerun()

                    except Exception as e:
                        st.error(f"Oh no! Something went wrong: {e}")
