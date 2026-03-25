# Course UI Component

import streamlit as st
import requests

API_URL = "http://localhost:8000/course/"

def course_ui():
    st.subheader("📘 Course Lookup")

    course_code = st.text_input("Enter Course Code (e.g., AI101)")

    if st.button("Get Course Details"):
        try:
            response = requests.get(API_URL, params={"code": course_code})
            data = response.json()

            st.write(data)

        except:
            st.error("Failed to fetch course data")
