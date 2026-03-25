# Calendar UI Component

import streamlit as st
import requests

API_URL = "http://localhost:8000/calendar/"

def calendar_ui():
    st.subheader("📆 Academic Calendar")

    program = st.text_input("Program (e.g., BTech)")

    if st.button("Get Calendar"):
        try:
            response = requests.get(API_URL, params={
                "program": program
            })
            data = response.json()

            st.write(data)

        except:
            st.error("Failed to fetch calendar")