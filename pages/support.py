import streamlit as st

# Streamlit page configuration
st.set_page_config(
    page_title='Support',
    page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.frontend.menu import menu
from utils.data.session_manager import SessionManager as sm
from utils.core.emailing import send_email_support
from utils.core.error_handling import catch_error

sm.check_state()
menu()

# Title
st.markdown("<h1 style='text-align: center; color: grey;'>Support</h1>", unsafe_allow_html=True)


with st.columns((1, 6, 1))[1]:

    with st.container(border=True):

        # Check if user email is available
        collect_email = False
        if 'user_email' not in st.session_state or st.session_state.user_email is None:
            collect_email = True

        request = st.empty()
        text = st.empty()
        if collect_email:
            email = st.empty()
        button = st.empty()

        request.markdown("""
Please send us a message if you:
- Have a question
- Want to request a feature
- Found a bug to report
        """)
        if collect_email:
            user_email = email.text_input("Email (optional):", value="", placeholder='Your email address')
        else:
            user_email = st.session_state.user_email
        message = text.text_area("Message:", value="", height=100, 
                                 key="1", placeholder='👋 All questions and suggestions welcome here!',  label_visibility='collapsed')

        if button.button("Send Message 📤", type="primary", use_container_width=True):
            try:
                with st.spinner("Sending message..."):
                    send_email_support(user_email, message)
                if user_email:
                    st.success("Message sent! We'll be back in touch soon 📨")
                else:
                    st.success("Message sent! Thank you for your feedback 🙏")
                request.empty()
                if collect_email:
                    email.empty()
                text.empty()
                button.empty()
            except Exception as e:
                catch_error()