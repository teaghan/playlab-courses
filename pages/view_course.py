import streamlit as st
from utils.session import check_state
from utils.menu import menu
from utils.aws import get_course_details
from utils.display_units import display_units

# Get course code from session state
course_code = st.session_state.get("course_code")

# Get course details
course_details = get_course_details(course_code)
if not course_details:
    st.error("Course not found")
    st.stop()

# Get course metadata
metadata = next((item for item in course_details if item["SK"] == "METADATA"), None)
if not metadata:
    st.error("Course metadata not found")
    st.stop()

# Store course metadata in session state if not already present
if "course_name" not in st.session_state:
    st.session_state.course_name = metadata.get('name', '')
if "course_description" not in st.session_state:
    st.session_state.course_description = metadata.get('description', '')
if "grade_level" not in st.session_state:
    st.session_state.grade_level = metadata.get('grade_level', 6)

st.set_page_config(page_title=st.session_state.course_name, page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", layout="wide")

# Check user state
check_state(check_user=False)

# Display page buttons
menu()

# Display course header
st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state.course_name}</h1>", unsafe_allow_html=True)

# Course description
st.markdown(st.session_state.course_description)

# Display units and sections
st.markdown("## Course Content")
display_units(course_code, allow_editing=False) 