import os
import streamlit as st
from utils.data.aws import get_file_content
from utils.data.session_manager import SessionManager as sm
from utils.frontend.student_assistant import display_student_assistant
from utils.core.image_paths import get_image_base64

def logout():
    sm.clear_user_context()
    st.switch_page("app.py")

def teacher_menu_old():
    st.sidebar.page_link("pages/dashboard.py", label="Dashboard")
    st.sidebar.page_link("pages/support.py", label="Contact Us")
    if st.sidebar.button('Logout', use_container_width=True, type='primary'):
        logout()

def student_menu():

    if 'section' in st.session_state and st.session_state.section is not None and st.session_state.section.assistant_instructions is not None and not st.session_state.on_mobile:
        with st.sidebar:
            display_student_assistant()
            st.sidebar.markdown('---')
    
    # Only show course structure if we have a course code
    course_code = st.session_state.get("course_code", '')
    if course_code:
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

def teacher_menu():
    
    pages = {
        "Dashboard": "pages/dashboard.py",
        "Explore": "pages/explore.py",
        "Contact Us": "pages/support.py",
        "Log Out": "app.py"
    }

    # Add custom CSS for navigation styling
    st.markdown(
        """
        <style>
        /* ───── Remove header & padding on top ───── */
        [data-testid="stHeader"] {display: none;}
        [data-testid="stMainBlockContainer"] {padding-top: 0.5rem;}
        
        /* ───── Style the top navigation bar ───── */
        .stNavigation {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: white;
            z-index: 999;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stNavigation .element-container {
            margin: 0;
        }
        
        .stNavigation button {
            background: none;
            border: none;
            padding: 0.5rem 1rem;
            margin: 0 0.5rem;
            cursor: pointer;
        }
        
        .stNavigation button:hover {
            color: #ff4b4b;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Format image as base64 and create linked logo
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(parent_dir, "../../images/opencource_logo_full.png")
    img_base64 = get_image_base64(image_path)
    logo_html = f"""
        <a href="." target="_self">
            <img src="{img_base64}" width="200">
        </a>
    """

    if not st.session_state.get("on_mobile", False):
        # Create top navigation bar
        col_widths = tuple([1] + [0.12*len(p)**(1/2) for p in pages])
        cols = st.columns(col_widths)
        cols[0].markdown(logo_html, unsafe_allow_html=True)
        
        # Navigation links
        for idx, (page_name, page_path) in enumerate(pages.items()):
            with cols[idx+1]:
                if page_name == "Log Out":
                    if st.button(page_name, use_container_width=True, type="primary"):
                        logout()
                else:
                    st.page_link(page_path, label=page_name, use_container_width=True)
        st.markdown('----')

    # Create sidebar navigation bar
    else:
        # Navigation links
        for idx, (page_name, page_path) in enumerate(pages.items()):
            with st.sidebar:
                st.markdown(logo_html, unsafe_allow_html=True)
                #st.page_link("app.py", label=f"![Logo](data:image/png;base64,{img_base64})", use_container_width=True)
                st.markdown('----')
                if page_name == "Log Out":
                    if st.button(page_name, use_container_width=True, type="primary"):
                        logout()
                else:
                    st.page_link(page_path, label=page_name, use_container_width=True)

def menu():
    # Determine if a user is logged in or not, then show the correct menu
    if st.session_state.role=='teacher':
        teacher_menu()
    else:
        student_menu()
    return