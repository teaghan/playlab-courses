import streamlit as st
from utils.styling import load_style
from utils.memory_manager import initialize_memory_and_heartbeat, update_session_activity
from utils.check_window import on_mobile

def user_reset():
    st.session_state.authentication_status = None
    st.session_state.user_email = None
    st.session_state.access_code = None

def check_state(check_user=False, reset_chat=False, 
                reset_teacher=True, reset_course=False):
    
    if "authentication_status" not in st.session_state:
        st.session_state['authentication_status'] = None
    
    # Load styling
    load_style()

    # Reset info
    if reset_teacher:
        reset_teacher_email()
    if reset_chat:
        reset_chatbot()
    if reset_course:
        course_reset()

    # Start periodic cleanup only once per session
    if "cleanup_initialized" not in st.session_state:
        # Initialize memory and heartbeat managers
        initialize_memory_and_heartbeat()

    # Update activity on any user interaction
    update_session_activity()
    
    # Check if user is signed in
    if check_user:
        if st.session_state.authentication_status is None:
            st.switch_page("app.py")

    # Check if user is on mobile
    on_mobile()

def reset_teacher_email():
    st.session_state['teacher_email'] = None

def course_reset():
    st.session_state['course_code'] = ''
    st.session_state['course_name'] = ''
    st.session_state['course_description'] = ''
    st.session_state['student_grade'] = 6

def reset_chatbot():
    st.session_state['messages'] = []
    st.session_state['drop_file'] = False
    st.session_state['math_attachments'] = []
    st.session_state['model_loaded'] = False
