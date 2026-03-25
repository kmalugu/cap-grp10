# Timetable UI Component

import streamlit as st
import requests

API_URL = "http://localhost:8000/timetable/"

def timetable_ui():
    st.subheader("📅 Timetable Viewer")

    year = st.number_input("Enter Year", min_value=1, max_value=4, value=1)
    department = st.text_input("Department (e.g., CSE)")

    if st.button("Get Timetable"):
        try:
            response = requests.get(API_URL, params={
                "year": year,
                "department": department
            })
            data = response.json()

            st.write(data)

        except:
            st.error("Failed to fetch timetable")