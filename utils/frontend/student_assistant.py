import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from utils.frontend.playlab import display_conversation
from utils.core.config import open_config

def display_student_assistant():
    pr_color = st.get_option('theme.primaryColor')
    bg_color = st.get_option('theme.backgroundColor')
    
    with stylable_container(key="my_styled_popover", 
                            css_styles=f"""button {{
        background-color: {pr_color} !important;
        color: {bg_color} !important; 
        border-radius: 0.25rem !important;
        padding: 0.5rem 1rem !important;
    }}
    """):
        po = st.popover("💬 Ask a question", 
                        help="Ask AI about this section",
                        use_container_width=not st.session_state.on_mobile)
        with po:
            display_conversation(open_config()['playlab']['student_assistant'], user='student', 
                                section_title=st.session_state.section.title,
                                section_type=st.session_state.section.section_type)