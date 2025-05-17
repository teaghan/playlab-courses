import streamlit as st
import time
import traceback
import sys
from utils.emailing import send_error_email
from utils.logger import logger

def catch_error():
    """
    Handles errors by displaying a warning message and redirecting the user after a countdown.
    Also sends an error notification email to the admin.
    """
    # Display warning message
    st.warning("Sorry, there seems to be an error. Our team is working on it. You will be redirected back to the home page now.")
    
    # Get the full error traceback including the exception chain
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error_traceback = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.error(f"Error traceback: {error_traceback}")
    
    # Send error notification email
    try:
        send_error_email(error_traceback, dict(st.session_state))
    except Exception as e:
        # If sending email fails, log it but don't show to user
        logger.error(f"Failed to send error email: {str(e)}")
    
    # Create a countdown container
    countdown_container = st.empty()
    
    # Countdown from 3 to 1
    for i in range(3, 0, -1):
        countdown_container.write(f"Redirecting in {i}...")
        time.sleep(1)
    
    # Clear the countdown
    countdown_container.empty()
    
    # Redirect based on user role
    if st.session_state.get('role') == 'student':
        st.switch_page("pages/enter_course.py")
    else:
        st.switch_page("app.py")
