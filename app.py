import streamlit as st

# Page info
st.set_page_config(page_title="Playlab Courses", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", layout="wide")

from utils.session import check_state, user_reset
from utils.aws import get_course_details
# If necessary, load tutor data, user data, styling, memory manager, etc.
check_state(reset_teacher=False)

params = st.query_params
# Check for both short format (?astro-12) and long format (?code=astro-12)
course_code = None
if 'code' in params:
    course_code = params["code"]
else:
    # Check if there's a single parameter without a key
    for key in params:
        if key == 'code':
            continue
        course_code = key
        break

if course_code:
    st.session_state.role = 'student'
    st.session_state['authentication_status'] = False
    # Check if course exists
    course_details = get_course_details(course_code)
    if not course_details:
        st.error("Invalid course code. Please check and try again.")
    else:
        # Store course code in session state and redirect to view_course
        st.session_state.course_code = course_code
        st.switch_page("pages/view_course.py")

st.markdown("<h1 style='text-align: center; color: grey;'>Playlab Courses</h1>", unsafe_allow_html=True)

st.markdown("----")

# Select role
col1, col2, col3 = st.columns((1.4, 2, 1.4))
with col2:
    if st.button(f"Students", use_container_width=True, type="primary"):
        user_reset()
        st.session_state.role = 'student'
        st.session_state['authentication_status'] = None
        st.switch_page("pages/enter_course.py")
    if st.button(f"Teachers", use_container_width=True):
        st.session_state.role = 'teacher'
        if st.session_state['authentication_status']:
            st.switch_page("pages/dashboard.py")
        else:
            st.switch_page("pages/login.py")
