from browser_detection import browser_detection_engine
import streamlit as st

def on_mobile():

    if 'on_mobile' not in st.session_state:
        info = browser_detection_engine()
        if info.get("isMobile"):
            st.session_state['on_mobile'] = True
        else:
            st.session_state['on_mobile'] = False