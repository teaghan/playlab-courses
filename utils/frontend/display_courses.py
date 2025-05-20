import streamlit as st
from utils.data.aws import get_course_details, delete_course, validate_course_code, create_course, copy_course_contents
from utils.core.config import domain_url
from utils.frontend.clipboard import to_clipboard
from utils.core.logger import logger
from utils.data.session_manager import SessionManager as sm
import traceback
def load_editor(course_code, create_copy=False):
    """
    Load course editor
    """
    
    # Store course details in session state
    st.session_state["course_code"] = course_code if not create_copy else f"{course_code}-copy"
    
    st.session_state['template_content'] = ''
    st.switch_page('pages/edit_course.py')

@st.dialog("Delete Course")
def delete_course_confirm(course_name, course_code):
    """
    Show confirmation dialog for course deletion
    """
    st.markdown(f'Are you sure you want to delete "*{course_name}*"?')
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete Course", type="primary", use_container_width=True):
            user_email = st.session_state.get("user_email")
            if delete_course(user_email, course_code):
                st.success("Course deleted successfully!")
                sm.initialize_user(st.session_state.user_email)
                st.rerun()
            else:
                st.error("Failed to delete course")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Copy Course")
def copy_course(course_code, course):
    """
    Show confirmation dialog for course copy
    """
    st.markdown(f'What course code will you use for "*{course.name} (Copy)*"?')
    new_course_code = st.text_input("Course Code", value=f"{course_code}-copy")
    st.session_state.copy_banner = st.empty()
    st.session_state.copy_spinner = st.container()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Copy Course", type="primary", use_container_width=True):
            course_code_status = validate_course_code(new_course_code)
            if course_code_status == 'Invalid':
                st.session_state.copy_banner.error('Course code must start with a letter, contain only lowercase letters, numbers, and hyphens, and be 3-20 characters long.')
            elif course_code_status == 'In Use':
                st.session_state.copy_banner.error("Course code is already in use")
            else:
                try:
                    with st.session_state.copy_spinner, st.spinner(f"Copying course..."):
                        # Create the new course with copied metadata
                        create_course(
                                email=st.session_state.user_email,
                            course_code=new_course_code,
                            name=f"{course.name} (Copy)",
                            description=course.description,
                            grade=course.grade_level
                        )
                    
                        # Copy all units and sections
                        if copy_course_contents(course_code, new_course_code):
                            st.session_state.copy_banner.success("Course copied successfully!")
                            sm.initialize_user(st.session_state.user_email)
                            st.rerun()
                        else:
                            st.session_state.copy_banner.error("Failed to copy course contents")
                                        
                except Exception as e:
                    # Print traceback
                    traceback.print_exc()
                    logger.error(f"Failed to copy course: {str(e)}")
                    st.session_state.copy_banner.error(f"Failed to copy course. Try again later.")
    with col2:
        if st.button("Close", use_container_width=True):
            st.rerun()

def display_courses(allow_edit=False, allow_copy=False):
    """
    Display courses with various interaction options
    """

    if not st.session_state.user_courses:
        st.info("No courses found. Create your first course!")
        return
    
    for course in st.session_state.user_courses:
        course_code = course.code
        with st.container():
            st.markdown(f"### **{course.name}**")
            st.markdown(f"*{course_code}*")
            
            col1, col2, col3, col4 = st.columns(4)

            # Edit button
            if allow_edit:
                with col1:
                    if st.button("Edit", key=f'edit_{course_code}', use_container_width=True, type="primary"):
                        load_editor(course_code)

            # Share button
            with col2:
                course_url = f"{domain_url()}/view_course?{course_code}"
                if st.button("Copy Course URL", key=f'copy_url_{course_code}', use_container_width=True, type="secondary"):
                    to_clipboard(course_url)

            # Copy button
            if allow_copy:
                with col3:
                    if st.button("Create a Copy", key=f'copy_{course_code}', use_container_width=True):
                        copy_course(course_code, course)

            # Delete button
            if allow_edit:
                with col4:
                    if st.button("Delete", key=f'delete_{course_code}', use_container_width=True):
                        delete_course_confirm(course.name, course_code)

            st.markdown('---') 


def explore_courses():
    """
    Display courses with various interaction options
    """

    for course in sm.get_open_courses():
        course_code = course.code
        with st.container():
            st.markdown(f"### **{course.name}**")
            st.markdown(f"*{course_code}*")
            with st.expander("Description"):
                st.markdown(f"{course.description}", unsafe_allow_html=True)

            # In explore mode, show different buttons based on role
            if st.session_state.get('role') == 'teacher':
                col1, col2, col3 = st.columns(3)

                with col2:
                    course_url = f"{domain_url()}/view_course?{course_code}"
                    if st.button("Copy Course URL", key=f'copy_url_{course_code}', use_container_width=True, type="secondary"):
                        to_clipboard(course_url)
                with col3:
                    if st.button("Create a Copy", key=f'copy_{course_code}', use_container_width=True):
                        copy_course(course_code, course)
            else:
                col1 = st.columns(1)[0]
            with col1:
                if st.button("View", key=f'view_{course_code}', use_container_width=True, type="primary"):
                    # Store course code in session state and redirect to view_course
                    st.session_state.course_code = course_code
                    st.switch_page("pages/view_course.py")

            st.markdown('---') 