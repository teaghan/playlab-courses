import streamlit as st
from utils.data.session_manager import SessionManager as sm
from utils.data.aws import get_course_details
from utils.core.error_handling import catch_error
from utils.core.config import open_config
st.set_page_config(
    page_title="Enter Course Code",
    page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png",
    layout="wide"
)

# Check user state
sm.check_state(check_user=False)

# Display logo
col1, col2, col3 = st.columns((1,1,1))
col2.image(open_config()['images']['logo_full'], use_container_width=True)
st.markdown("#")

# Create a form for course code input
with st.form("course_code_form"):
    st.markdown("Enter your course code:")
    course_code = st.text_input(
        "Course Code",
        placeholder="Enter the course code provided by your instructor",
        help="The course code is typically a short string of characters provided by your instructor",
        label_visibility="collapsed"
    )
    
    submitted = st.form_submit_button("View Course", type="primary", use_container_width=True)

# Handle form submission
if submitted:
    if not course_code:
        st.error("Please enter a course code")
    else:
        # Check if course exists
        try:
            course_details = get_course_details(course_code)
        except Exception as e:
            catch_error()
            course_details = None
            
        if not course_details:
            st.error("Invalid course code. Please check and try again.")
        else:
            # Store course code in session state and redirect to view_course
            st.session_state.course_code = course_code
            st.switch_page("pages/view_course.py")

st.markdown("#")
st.markdown("<h3 style='text-align: center; color: grey;'>Or Explore Our Open Courses</h3>", unsafe_allow_html=True)

if st.columns((1,3,1))[1].button("Explore", use_container_width=True, type="primary"):
    st.switch_page("pages/explore.py")