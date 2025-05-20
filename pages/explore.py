import streamlit as st
from utils.data.session_manager import SessionManager as sm
from utils.frontend.display_courses import explore_courses
from utils.core.error_handling import catch_error
from utils.core.config import open_config

# Streamlit info
st.set_page_config(page_title='Explore Open Courses', 
                   page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png", 
                   layout="wide", initial_sidebar_state='collapsed')

try:
    sm.check_state(check_user=False, reset_course=True)

    # Display page buttons
    from utils.frontend.menu import menu
    menu()

    # Display logo
    col1, col2, col3 = st.columns((1,1,1))
    col2.image(open_config()['images']['logo_full'], use_container_width=True)

    st.markdown("----")

    # Display courses
    explore_courses()
except Exception as e:
    catch_error()