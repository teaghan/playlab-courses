import streamlit as st
from utils.data.session_manager import SessionManager as sm
from utils.data.aws import get_course_details

st.set_page_config(
    page_title="Enter Course Code",
    page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png",
    layout="wide"
)

# Check user state
sm.check_state(check_user=False)

# Center the content
st.markdown("<h1 style='text-align: center; color: grey;'>Enter Course Code</h1>", unsafe_allow_html=True)

# Create a form for course code input
with st.form("course_code_form"):
    course_code = st.text_input(
        "Course Code",
        placeholder="Enter the course code provided by your instructor",
        help="The course code is typically a short string of characters provided by your instructor"
    )
    
    submitted = st.form_submit_button("View Course", type="primary", use_container_width=True)

# Handle form submission
if submitted:
    if not course_code:
        st.error("Please enter a course code")
    else:
        # Check if course exists
        course_details = get_course_details(course_code)
        if not course_details:
            st.error("Invalid course code. Please check and try again.")
        else:
            # Store course code in session state and redirect to view_course
            st.session_state.course_code = course_code
            st.switch_page("pages/view_course.py")