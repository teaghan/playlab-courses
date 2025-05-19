import streamlit as st
from utils.frontend.display_units import display_units
from utils.core.error_handling import catch_error
from utils.data.session_manager import SessionManager as sm

try:
    # Get course code from query params
    params = st.query_params
    if params:
        course_code = next(iter(params))
        sm.clear_user_context()
    else:
        # Get course code from session state
        course_code = st.session_state.get("course_code")

    if not course_code:
        st.switch_page("pages/enter_course.py")

    if not sm.initialize_course(course_code):
        st.switch_page("pages/enter_course.py")
    
    # Set page config
    st.set_page_config(
        page_title=st.session_state.course_name,
        page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png",
        layout="wide"
    )

    # Check user state
    sm.check_state(check_user=False)

    # Display course header
    st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state.course_name}</h1>", 
                unsafe_allow_html=True)

    # Course description
    st.markdown(st.session_state.course_description, unsafe_allow_html=True)
    st.markdown("---")
    
    # Display units and sections
    display_units(course_code, allow_editing=False)
    
except Exception as e:
    catch_error() 