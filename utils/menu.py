import streamlit as st
from utils.session import user_reset

def logout():
    user_reset()
    st.switch_page("app.py")

def teacher_menu():
    st.sidebar.page_link("pages/dashboard.py", label="Dashboard")
    st.sidebar.page_link("pages/support.py", label="Get Support")
    if st.sidebar.button('Logout', use_container_width=True, type='primary'):
        logout()

def student_menu():
    st.sidebar.page_link("app.py", label="Home")

def menu():
    # Determine if a user is logged in or not, then show the correct menu
    if st.session_state.role=='student':
        student_menu()
    else:
        teacher_menu()
    return