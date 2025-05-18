import streamlit as st
from utils.data.session_manager import SessionManager as sm
from utils.data.user_manager import is_valid_email
from utils.frontend.access_codes import access_code_dialog, create_access_code

st.set_page_config(page_title="Playlab Courses", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png",  layout="wide")

sm.check_state(reset_chat=True)

st.markdown("<h1 style='text-align: center; color: grey;'>Playlab Courses</h1>", unsafe_allow_html=True)


# Email entry form
with st.columns((1,10,1))[1]:
    with st.form("email_form"):
        st.markdown("Email:")
        email = st.text_input("Email:", label_visibility="collapsed", placeholder='Enter your email address')
        email = email.strip().lower()
        with st.columns((1,1,1))[1]:
            submit_button = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submit_button:
            if email:
                if not is_valid_email(email):
                    st.error("Invalid email address")
                else:
                    if create_access_code(email):
                        access_code_dialog(email)
            else:
                st.error("Please enter your email address")