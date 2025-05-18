import streamlit as st
from utils.data.session_manager import SessionManager as sm
from utils.frontend.display_courses import display_courses

# Streamlit info
st.set_page_config(page_title='Dashboard', 
                   page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", 
                   layout="wide", initial_sidebar_state='collapsed')

sm.check_state(check_user=True)

# Display page buttons
from utils.frontend.menu import menu
menu()

st.markdown("## My Courses")

with st.columns((1,1,1))[1]:
    if st.button("Add Course", use_container_width=True, type="primary"):
        st.switch_page("pages/create_course.py")

# Display courses
display_courses(
    allow_edit=True,
    allow_copy=True
)