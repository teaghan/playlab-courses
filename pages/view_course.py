import streamlit as st
from utils.session import check_state
from utils.aws import get_course_details, get_unit_sections
from utils.display_units import display_units

# Get course code from session state
course_code = st.session_state.get("course_code")

# Get course details
course_details = get_course_details(course_code)
if not course_details:
    st.switch_page("pages/enter_course.py")

# Get course metadata
metadata = next((item for item in course_details if item["SK"] == "METADATA"), None)
if not metadata:
    st.error("Course metadata not found")
    st.switch_page("pages/enter_course.py")

# Create nested dictionary of units and sections
course_structure = {}
for item in course_details:
    if item["SK"].startswith("UNIT#"):
        unit_id = item["SK"].replace("UNIT#", "")
        unit_title = item.get("title", "")
        course_structure[unit_id] = {
            "title": unit_title,
            "sections": {}
        }
    elif item["SK"].startswith("SECTION#"):
        # Extract unit_id from PK (format: COURSE#{course_code}#UNIT#{unit_id})
        pk_parts = item["PK"].split("#")
        if len(pk_parts) >= 4:
            unit_id = pk_parts[3]
            section_id = item["SK"].replace("SECTION#", "")
            section_title = item.get("title", "")
            if unit_id in course_structure:
                course_structure[unit_id]["sections"][section_id] = {
                    "title": section_title
                }

# Get sections for each unit
for unit_id in course_structure:
    sections = get_unit_sections(course_code, unit_id)
    if sections:
        # Sort sections by order
        sections.sort(key=lambda x: x.get('order', 0))
        for section in sections:
            section_id = section["SK"].replace("SECTION#", "")
            section_title = section.get("title", "")
            course_structure[unit_id]["sections"][section_id] = {
                "title": section_title
            }

# Store course structure in session state
st.session_state.course_structure = course_structure

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

# Display course header
st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state.course_name}</h1>", unsafe_allow_html=True)

# Course description
st.markdown(st.session_state.course_description)
st.markdown("---")
# Display units and sections
display_units(course_code, allow_editing=False) 