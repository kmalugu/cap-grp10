# Fees UI Component

import streamlit as st
import requests

API_URL = "http://localhost:8000/fees/"

def fees_ui():
    st.subheader("💰 Fee Structure")

    program = st.text_input("Program (e.g., BTech)")
    nationality = st.selectbox("Nationality", ["domestic", "international"])

    if st.button("Get Fees"):
        try:
            response = requests.get(API_URL, params={
                "program": program,
                "nationality": nationality
            })
            data = response.json()

            st.write(data)

        except:
            st.error("Failed to fetch fee data")
