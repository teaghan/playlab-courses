import streamlit as st
# Page info
st.set_page_config(page_title="Playlab Courses", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", layout="wide")

from utils.session import check_state, user_reset

# If necessary, load tutor data, user data, styling, memory manager, etc.
check_state(reset_teacher=False)

params = st.query_params
if 'code' in params:
    user_reset()
    st.session_state.role = 'student'
    st.session_state['authentication_status'] = False
    access_code = params["code"]

st.markdown("<h1 style='text-align: center; color: grey;'>Playlab Courses</h1>", unsafe_allow_html=True)


st.markdown("----")

# Select role
col1, col2, col3 = st.columns((1.4, 2, 1.4))
with col2:
    if st.button(f"Students", use_container_width=True, type="primary"):
        user_reset()
        st.session_state.role = 'student'
        st.session_state['authentication_status'] = False
        st.switch_page("pages/explore_tutors.py")
    if st.button(f"Teachers", use_container_width=True):
        st.session_state.role = 'teacher'
        if st.session_state['authentication_status']:
            st.switch_page("pages/dashboard.py")
        else:
            st.switch_page("pages/login.py")
