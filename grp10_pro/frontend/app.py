# Streamlit Main UI
import streamlit as st
from components.chat_ui import chat_ui
from components.course_ui import course_ui
from components.timetable_ui import timetable_ui
from components.fees_ui import fees_ui
from components.calendar_ui import calendar_ui

st.set_page_config(page_title="University AI Assistant", layout="wide")

st.title("🎓 University AI Assistant")

# Sidebar navigation
option = st.sidebar.selectbox(
    "Choose Feature",
    ["Chat Assistant", "Course Lookup", "Timetable", "Fees", "Academic Calendar"]
)

if option == "Chat Assistant":
    chat_ui()

elif option == "Course Lookup":
    course_ui()

elif option == "Timetable":
    timetable_ui()

elif option == "Fees":
    fees_ui()

elif option == "Academic Calendar":
    calendar_ui()