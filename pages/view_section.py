import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from utils.data.session_manager import SessionManager as sm

st.set_page_config(
    page_title="View Section", 
    page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", 
    layout="wide", 
)

# Check user state
sm.check_state(check_user=False)

# Display page buttons
from utils.frontend.menu import menu
menu()

# Get section from session state
section = st.session_state.get("section")

# Navigation
if st.columns((1, 3))[0].button('Return to Course', use_container_width=True, type='primary'):
    st.switch_page('pages/view_course.py')

# Display section content based on type
if section.section_type == 'content':
    st.markdown(section.content or '', unsafe_allow_html=True)
elif section.section_type == 'file':
    if st.session_state.get('pdf_content'):
        pdf_viewer(st.session_state.pdf_content)
    else:
        st.error("File content not found") 