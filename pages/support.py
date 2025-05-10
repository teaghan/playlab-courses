import streamlit as st
from utils.menu import menu
from utils.session import check_state
from utils.emailing import send_email_support

# Streamlit page configuration
st.set_page_config(
    page_title='Support',
    page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

check_state()
menu()

# Title
st.markdown("<h1 style='text-align: center; color: grey;'>Support</h1>", unsafe_allow_html=True)


with st.columns((1, 6, 1))[1]:

    with st.container(border=True):

        request = st.empty()
        text = st.empty()
        email = st.empty()
        button = st.empty()

        request.markdown("""
Please send us a message if you:
- Have a question
- Want to request a feature
- Found a bug to report
        """)
        user_email = email.text_input("Email (optional):", value="", placeholder='Your email address')
        message = text.text_area("Message:", value="", height=100, 
                                 key="1", placeholder='👋 All questions and suggestions welcome here!',  label_visibility='collapsed')

        if button.button("Send Message 📤", type="primary", use_container_width=True):
            with st.spinner("Sending message..."):
                send_email_support(user_email, message)
            if user_email:
                st.success("Message sent! We'll be back in touch soon 📨")
            else:
                st.success("Message sent! Thank you for your feedback 🙏")
            request.empty()
            email.empty()
            text.empty()
            button.empty()