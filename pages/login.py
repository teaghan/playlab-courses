import streamlit as st
import random
import string
import re

from utils.session import check_state
from utils.emailing import send_access_code
from utils.config import domain_url
st.set_page_config(page_title="Playlab Courses", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png",  layout="wide")

# If necessary, load tutor data, user data, etc.
check_state(reset_chat=True)

st.markdown("<h1 style='text-align: center; color: grey;'>Playlab Courses</h1>", unsafe_allow_html=True)

# Initialize session state for access code if not exists
if 'access_code' not in st.session_state:
    st.session_state.access_code = None

def create_access_code():
    access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    st.session_state.access_code = access_code

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
            if entered_code == st.session_state.access_code:
                st.session_state.authentication_status = True
                st.switch_page("pages/dashboard.py")
            else:
                st.error("Invalid access code")
        
        if new_code_button:
            create_access_code()
            with st.spinner("Sending access code..."):
                send_access_code(st.session_state.access_code, st.session_state.user_email)
            st.success("Access code sent!")

# Email entry form
with st.columns((1,10,1))[1]:
    with st.form("email_form"):
        st.markdown("Email:")
        email = st.text_input("Email:", label_visibility="collapsed", placeholder='Enter your email address')
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

                        # Generate a random 6-digit code
                        create_access_code()
                        
                        # Send email with access code
                        with st.spinner("Sending access code..."):
                            send_access_code(st.session_state.access_code, st.session_state.user_email)
                        
                        access_code_dialog()
            else:
                st.error("Please enter your email address")