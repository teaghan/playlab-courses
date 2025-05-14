import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from utils.session import user_reset
from utils.playlab import display_conversation
from utils.config import open_config

def logout():
    user_reset()
    st.switch_page("app.py")

def teacher_menu():
    st.sidebar.page_link("pages/dashboard.py", label="Dashboard")
    st.sidebar.page_link("pages/support.py", label="Contact Us")
    if st.sidebar.button('Logout', use_container_width=True, type='primary'):
        logout()

def student_menu():
    
    pr_color = st.get_option('theme.primaryColor')
    bg_color = st.get_option('theme.backgroundColor')

    with st.sidebar:
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
                            use_container_width=True)
            with po:
                display_conversation(open_config()['playlab']['student_assistant'], user='student', 
                                     section_title=st.session_state['section_title'],
                                     section_type=st.session_state['section_type'])
    
    # Home button to go back to view course
    if st.sidebar.button(f'{st.session_state.course_name}', icon="🏠", use_container_width=False, type='secondary'):
        st.switch_page('pages/view_course.py')
    # Display course structure if available
    if "course_structure" in st.session_state:
        with st.sidebar:
            
            # Get course structure from session state
            course_structure = st.session_state.course_structure
            
            # Display each unit and its sections
            for unit_id, unit_data in course_structure.items():
                # Create an expander for each unit
                with st.expander(f"**{unit_data['title']}**"):
                    # Display each section in the unit
                    for section_id, section_data in unit_data['sections'].items():
                        if st.button(
                            f"{section_data['title']}", 
                            key=f"section_{unit_id}_{section_id}",
                            use_container_width=True
                        ):
                            # Store section details in session state
                            st.session_state.download_complete = False
                            st.session_state["unit_id"] = unit_id
                            st.session_state["unit_title"] = unit_data['title']
                            st.session_state["section_id"] = section_id
                            st.session_state["section_title"] = section_data['title']
                            # Navigate to view_section page
                            st.switch_page('pages/view_section.py')

def menu():
    # Determine if a user is logged in or not, then show the correct menu
    if st.session_state.role=='student':
        student_menu()
    else:
        teacher_menu()
    return