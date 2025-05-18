import streamlit as st
from utils.data.access_code import AccessCodeManager
from utils.core.emailing import send_access_code
from utils.core.error_handling import catch_error
from utils.core.config import domain_url
from utils.data.session_manager import SessionManager as sm

def create_access_code(user_email):
    """Generate and send a new access code"""
    try:
        access_code = AccessCodeManager().generate_access_code(user_email)
        with st.spinner("Sending access code..."):
            send_access_code(access_code, user_email)
        st.success("Access code sent!")
        return True
    except Exception as e:
        catch_error()
        return False
    
# Access code dialog
@st.dialog("Enter Access Code")
def access_code_dialog(email):
    st.info(f"An access code has been sent to {email}. \n\nPlease **keep this tab open** to verify your access code.")
    
    with st.form("access_code_form"):
        entered_code = st.text_input("Enter Access Code:", placeholder='Enter the 6-digit code')
        verify_button = st.form_submit_button("Verify Code", type="primary", use_container_width=True)
        new_code_button = st.form_submit_button("Send New Code", use_container_width=True)
        
        if verify_button:
            if 'localhost' in domain_url():
                sm.initialize_user(email)
                st.switch_page("pages/dashboard.py")
            else:
                try:
                    if AccessCodeManager().verify_access_code(email, entered_code):
                        sm.initialize_user(email)
                        st.switch_page("pages/dashboard.py")
                    else:
                        st.error("Invalid access code or code has expired")
                except Exception as e:
                    catch_error()
        
        if new_code_button:
            create_access_code()