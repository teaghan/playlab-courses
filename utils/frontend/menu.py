import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from utils.frontend.playlab import display_conversation
from utils.core.config import open_config
from utils.data.aws import get_file_content
from utils.data.session_manager import SessionManager as sm
from utils.data.course_manager import CourseManager

def logout():
    sm.clear_user_context()
    st.switch_page("app.py")

def teacher_menu():
    st.sidebar.page_link("pages/dashboard.py", label="Dashboard")
    st.sidebar.page_link("pages/support.py", label="Contact Us")
    if st.sidebar.button('Logout', use_container_width=True, type='primary'):
        logout()

def student_menu():
    pr_color = st.get_option('theme.primaryColor')
    bg_color = st.get_option('theme.backgroundColor')

    if st.session_state.section.assistant_instructions is not None:
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
                                        section_title=st.session_state.section.title,
                                        section_type=st.session_state.section.section_type)
    
    # Only show course structure if we have a course code
    course_code = st.session_state.get("course_code")
    if course_code:
        st.sidebar.markdown('---')
        # Home button to go back to view course
        if st.sidebar.columns((1,7,1))[1].button(f'{st.session_state.course_name}', icon="🏠", use_container_width=True, type='secondary'):
            st.switch_page('pages/view_course.py')
        
        with st.sidebar:
            # Display units and sections
            for unit in st.session_state.course_units:
                st.markdown(f'#### Unit {unit.order}')
                with st.expander(f"**{unit.title}**"):
                    for section in unit.sections:
                        if st.button(
                            f"{section.title}", 
                            key=f"section_{unit.id}_{section.id}",
                            use_container_width=True
                        ):
                            # Reset chat bot
                            sm.reset_chatbot()
                            # Initialize section in session state
                            sm.initialize_section(unit.id, section.id)
                            if st.session_state.section.section_type == 'file':
                                st.session_state['pdf_content'] = get_file_content(st.session_state.section.file_path)
                            else:
                                st.session_state['pdf_content'] = ''                                            
                            st.switch_page('pages/view_section.py')

def menu():
    # Determine if a user is logged in or not, then show the correct menu
    if st.session_state.role=='teacher':
        teacher_menu()
    else:
        student_menu()
    return