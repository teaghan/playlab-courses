import streamlit as st

# Page info
st.set_page_config(page_title="OpenCource", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png", layout="wide")

from utils.core.config import open_config
from utils.data.session_manager import SessionManager as sm

# If necessary, load tutor data, user data, styling, memory manager, etc.
sm.check_state(user_reset=False)

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
    if not sm.initialize_course(course_code):
        st.error("Invalid course code. Please check and try again.")
    else:
        st.switch_page("pages/view_course.py")

# Display logo
col1, col2, col3 = st.columns((1,1,1))
col2.image(open_config()['images']['logo_full'], use_container_width=True)

st.markdown("----")

# Select role
col1, col2, col3 = st.columns((1.4, 2, 1.4))
with col2:
    if st.button(f"Students", use_container_width=True, type="primary"):
        sm.clear_user_context()
        st.switch_page("pages/enter_course.py")
    if st.button(f"Teachers", use_container_width=True):
        st.session_state.role = 'teacher'
        if st.session_state['authentication_status']:
            st.switch_page("pages/dashboard.py")
        else:
            st.switch_page("pages/login.py")
