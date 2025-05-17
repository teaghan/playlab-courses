import streamlit as st
import re
from utils.session import check_state
from utils.emailing import send_access_code
from utils.config import domain_url
from utils.access_code import AccessCodeManager
from utils.logger import logger
from utils.error_handling import catch_error

st.set_page_config(page_title="Playlab Courses", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png",  layout="wide")

# Initialize access code manager
access_code_manager = AccessCodeManager()

# If necessary, load tutor data, user data, etc.
check_state(reset_chat=True)

st.markdown("<h1 style='text-align: center; color: grey;'>Playlab Courses</h1>", unsafe_allow_html=True)

def create_access_code():
    """Generate and send a new access code"""
    try:
        access_code = access_code_manager.generate_access_code(st.session_state.user_email)
        with st.spinner("Sending access code..."):
            send_access_code(access_code, st.session_state.user_email)
        st.success("Access code sent!")
        return True
    except Exception as e:
        catch_error()
        return False

def is_valid_email(email: str) -> bool:
    """
    Validate an email address using a robust regex pattern based on RFC 5322.
    
    Args:
        email (str): The email address string to validate.
    
    Returns:
        bool: True if the email is valid according to the regex; False otherwise.
    """
    # This regex covers a wide range of valid email formats
    email_regex = re.compile(
        r"(?:[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"
        r'|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]'
        r'|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")'
        r'@(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?'
        r'|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|'
        r'[a-zA-Z0-9-]*[a-zA-Z0-9]:'
        r'(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]'
        r'|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'
    )
    # Using fullmatch ensures the entire string conforms to the pattern.
    return re.fullmatch(email_regex, email) is not None

# Access code dialog
@st.dialog("Enter Access Code")
def access_code_dialog():
    st.info(f"An access code has been sent to {st.session_state.user_email}. \n\nPlease **keep this tab open** to verify your access code.")
    
    with st.form("access_code_form"):
        entered_code = st.text_input("Enter Access Code:", placeholder='Enter the 6-digit code')
        verify_button = st.form_submit_button("Verify Code", type="primary", use_container_width=True)
        new_code_button = st.form_submit_button("Send New Code", use_container_width=True)
        
        if verify_button:
            try:
                if access_code_manager.verify_access_code(st.session_state.user_email, entered_code):
                    st.session_state.authentication_status = True
                    st.switch_page("pages/dashboard.py")
                else:
                    st.error("Invalid access code or code has expired")
            except Exception as e:
                catch_error()
        
        if new_code_button:
            create_access_code()

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
                    st.session_state.user_email = email

                    if "localhost" in domain_url():
                        st.session_state.authentication_status = True
                        st.switch_page("pages/dashboard.py")
                    else:
                        if create_access_code():
                            access_code_dialog()
            else:
                st.error("Please enter your email address")