import json
import os

import streamlit as st

from agent import summarize_email, save_outputs

st.set_page_config(page_title="Email Summarization Agent", page_icon="📧", layout="centered")

st.title("📧 Email Summarization Agent")
st.markdown("Paste your email below and click **Summarize** to extract key information.")

email_text = st.text_area("Email Content", height=250, placeholder="Paste your email here...")

if st.button("Summarize Email", type="primary", disabled=not email_text.strip()):
    with st.spinner("Analyzing email..."):
        try:
            result = summarize_email(email_text)
            save_outputs(result)

            st.success("Email summarized successfully!")

            st.subheader("Summary")
            st.write(result["summary"])

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Key Points")
                for point in result["key_points"]:
                    st.markdown(f"- {point}")

                st.subheader("Deadlines")
                if result["deadlines"]:
                    for deadline in result["deadlines"]:
                        st.markdown(f"- {deadline}")
                else:
                    st.write("None identified")

            with col2:
                st.subheader("Action Items")
                for action in result["action_items"]:
                    if isinstance(action, dict):
                        who = action.get("who") or action.get("assignee", "")
                        what = action.get("what") or action.get("task", "")
                        st.markdown(f"- **{who}**: {what}")
                    else:
                        st.markdown(f"- {action}")

                st.subheader("Urgency")
                urgency = result["urgency"]
                color = {"Low": "green", "Medium": "orange", "High": "red"}.get(urgency, "gray")
                st.markdown(f":{color}[**{urgency}**]")

            with st.expander("View raw JSON"):
                st.json(result)

        except Exception as e:
            st.error(f"Error: {e}")
