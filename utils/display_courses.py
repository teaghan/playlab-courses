import streamlit as st
from utils.aws import get_user_courses, get_course_details, delete_course, validate_course_code, create_course, copy_course_contents
from utils.config import domain_url
#from utils.clipboard import to_clipboard
from st_copy_to_clipboard import st_copy_to_clipboard

from utils.logger import logger

def load_editor(course_code, create_copy=False):
    """
    Load course editor
    """
    course_details = get_course_details(course_code)
    if not course_details:
        st.error("Course not found")
        return
    
    # Store course details in session state
    st.session_state["course_code"] = course_code if not create_copy else f"{course_code}-copy"
    
    # Get the course metadata
    metadata = next((item for item in course_details if item["SK"] == "METADATA"), None)
    if metadata:
        st.session_state["course_name"] = metadata.get("name", "")
        st.session_state["course_description"] = metadata.get("description", "")
        st.session_state["grade_level"] = metadata.get("grade_level", 6)
    
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
    st.markdown(f'What course code will you use for "*{course.get("name")} (Copy)*"?')
    new_course_code = st.text_input("Course Code", value=f"{course_code}-copy")
    st.session_state.copy_banner = st.empty()
    
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
                    # Create the new course with copied metadata
                    create_course(
                        email=st.session_state.user_email,
                        course_code=new_course_code,
                        name=f"{course.get('name')} (Copy)",
                        description=course.get('description', ''),
                        grade=course.get('grade_level', 6)
                    )
                    
                    # Copy all units and sections
                    if copy_course_contents(course_code, new_course_code):
                        st.session_state.copy_banner.success("Course copied successfully!")
                        st.rerun()
                    else:
                        st.session_state.copy_banner.error("Failed to copy course contents")
                                    
                except Exception as e:
                    logger.error(f"Failed to copy course: {str(e)}")
                    st.session_state.copy_banner.error(f"Failed to copy course. Try again later.")
    with col2:
        if st.button("Close", use_container_width=True):
            st.rerun()


def display_courses(allow_edit=False, allow_copy=False):
    """
    Display courses with various interaction options
    """
    # Get user's email from session state
    user_email = st.session_state.get("user_email")
    if not user_email:
        st.error("User not logged in")
        return

    # Get courses for the user
    courses = get_user_courses(user_email)
    
    if not courses:
        st.info("No courses found. Create your first course!")
        return

    for course in courses:
        course_code = course["SK"].replace("COURSE#", "")
        with st.container():
            st.markdown(f"### **{course.get('name')}**")
            st.markdown(f"*{course_code}*")
            st.markdown(course.get("description"))
            
            # Create columns for buttons
            col1, col2, col3, col4 = st.columns(4)

            # Edit button
            if allow_edit:
                with col1:
                    if st.button("Edit", key=f'edit_{course_code}', use_container_width=True, type="primary"):
                        load_editor(course_code)

            # Share button
            with col2:
                course_url = f"{domain_url()}?{course_code}"
                if st_copy_to_clipboard(course_url, before_copy_label="Copy Course URL", after_copy_label="Copied!"):
                    st.success("Copied!")
                #if st.button("Copy Course URL", key=f'copy_url_{course_code}', use_container_width=True, type="primary"):
                #    course_url = f"{domain_url()}?{course_code}"
                #    to_clipboard(course_url)
                #    st.success("Copied!")

            # Copy button
            if allow_copy:
                with col3:
                    if st.button("Create a Copy", key=f'copy_{course_code}', use_container_width=True):
                        copy_course(course_code, course)

            # Delete button
            if allow_edit:
                with col4:
                    if st.button("Delete", key=f'delete_{course_code}', use_container_width=True):
                        delete_course_confirm(course.get("name"), course_code)

            st.markdown('---') 