import streamlit as st
from utils.data.session_manager import SessionManager as sm
from utils.data.user_manager import is_valid_email
from utils.frontend.access_codes import access_code_dialog, create_access_code
from utils.core.error_handling import catch_error
from utils.core.config import open_config

st.set_page_config(page_title="OpenCource", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png",  layout="wide")

try:
    sm.check_state(reset_chat=True)

    # Display logo
    col1, col2, col3 = st.columns((1,1,1))
    col2.image(open_config()['images']['logo_full'], use_container_width=True)


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
except Exception as e:
    catch_error()