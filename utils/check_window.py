import streamlit as st
from utils.js_eval import evaluate_js

def on_mobile():

    page_width = st.session_state.get('page_width', None)

    if page_width is None or page_width > 768:
        st.session_state['on_mobile'] = False
        
    # Get page width
    if 'page_width' not in st.session_state or st.session_state['page_width'] is None:
        st.session_state['page_width'] = evaluate_js("window.innerWidth", 
                                                     default=None, key="width", height=0)
        page_width = st.session_state['page_width']

    # Create sidebar navigation bar
    if page_width is not None and page_width <= 768:
        st.session_state['on_mobile'] = True