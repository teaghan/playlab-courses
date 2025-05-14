import streamlit as st
from utils.aws import get_unit_sections, get_course_units, get_file_content
from streamlit_pdf_viewer import pdf_viewer
import tempfile
import os
from utils.logger import logger
from utils.session import check_state
from utils.menu import menu

# Initialize session state variables if they don't exist
if "unit_id" not in st.session_state:
    st.error("No unit selected. Please return to the course page.")
    st.stop()

if "section_id" not in st.session_state:
    st.error("No section selected. Please return to the course page.")
    st.stop()

# Get section details
unit_id = st.session_state["unit_id"]
section_id = st.session_state["section_id"]
course_code = st.session_state.get("course_code")

# Get section data
sections = get_unit_sections(course_code, unit_id)
section = next((s for s in sections if s.get('SK') == f'SECTION#{section_id}'), None)

if not section:
    st.error("Section not found. Please return to the course page.")
    st.stop()

# Get unit data
units = get_course_units(course_code)
unit = next((u for u in units if u.get('SK') == f'UNIT#{unit_id}'), None)

st.set_page_config(page_title=f"{section.get('title')}", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", layout="wide")

# Check user state
check_state(check_user=False)

# Display page buttons
menu()

if not unit:
    st.error("Unit not found. Please return to the course page.")
    st.stop()

# Navigation
if st.columns((1, 3))[0].button('Return to Course Page', use_container_width=True, type='primary'):
    st.switch_page('pages/view_course.py')

# Display section content based on type
section_type = section.get('section_type', 'content')

if section_type == 'content':
    # Display markdown content
    st.markdown(section.get('content', ''), unsafe_allow_html=True)
elif section_type == 'file':
    # Display PDF file
    file_path = section.get('file_path')
    if file_path:
        try:
            # Get PDF content from S3
            pdf_content = get_file_content(file_path)
            if pdf_content:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(pdf_content)
                    tmp_path = tmp_file.name
                
                # Display PDF using the temporary file
                pdf_viewer(tmp_path)
                
                # Clean up the temporary file
                os.unlink(tmp_path)
            else:
                st.error(f"Failed to retrieve PDF content.")
                logger.error(f"Failed to retrieve PDF content for path: {file_path}")
        except Exception as e:
            logger.error(f"Error displaying PDF: {str(e)}")
    else:
        st.error("No file path specified for this section") 