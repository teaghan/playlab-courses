import streamlit as st

from utils.session import check_state
from utils.config import domain_url
from utils.aws import create_course, validate_course_code

st.set_page_config(page_title="Create Course", 
                   page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", 
                   layout="wide", initial_sidebar_state='collapsed')

# Check user state
check_state(check_user=True)

# Display page buttons
from utils.menu import menu
menu()

st.markdown("<h1 style='text-align: center; color: grey;'>Create a New Course</h1>", unsafe_allow_html=True)

# Initialize session state for form data if not exists
if 'course_name' not in st.session_state:
    st.session_state.course_name = ""
if 'course_code' not in st.session_state:
    st.session_state.course_code = ""
if 'grade_level' not in st.session_state:
    st.session_state.grade_level = 6
if 'course_description' not in st.session_state:
    st.session_state.course_description = ""

# Course creation form
with st.form("course_form"):
    # Course Name
    st.markdown('#### Course Name')
    course_name = st.text_input(
        'Name:',
        placeholder='e.g. "Introduction to Astronomy"',
        value=st.session_state.course_name,
        label_visibility='collapsed'
    )

    # Course Code
    st.markdown('#### Course Code')
    st.markdown(f'This will be used in the course URL (e.g., {domain_url()}?astro-12)')
    course_code = st.text_input(
        'Code:',
        placeholder='e.g. "astro-12"',
        value=st.session_state.course_code,
        label_visibility='collapsed'
    )
    if course_code:
        course_code_status = validate_course_code(course_code)
        if course_code_status == 'Invalid':
            st.error('Course code must start with a letter, contain only lowercase letters, numbers, and hyphens, and be 3-20 characters long.')
        elif course_code_status == 'In Use':
            st.error('Course code is already in use.')

    # Grade
    st.markdown('#### Student Grade Level')
    student_grade = st.columns((1,10,1))[1].select_slider(
            'Select grade:',
            label_visibility='collapsed',
            options=list(range(0, 14)),
            format_func=lambda x: 'K' if x == 0 else 'Adult' if x == 13 else x,
            value=st.session_state.grade_level,
            help='Select the grade level for this course'
        )

    # Course Description
    st.markdown('#### Course Description (optional)')
    course_description = st.text_area(
        'Description:',
        placeholder='e.g. "This course is an introduction to astronomy offered as a specialized science 12 course."',
        value=st.session_state.course_description,
        height=100,
        label_visibility='collapsed'
    )

    # Submit button
    submit_button = st.form_submit_button("Create Course", type="primary", use_container_width=True)

    if submit_button:
        course_code_status = validate_course_code(course_code)
        if not course_name:
            st.error("Please enter a course name")
        elif not course_code:
            st.error("Please enter a course code")
        elif 'Good' not in course_code_status:
            st.error("Please enter a valid course code")
        else:
            # Store form data in session state
            st.session_state.course_name = course_name
            st.session_state.course_code = course_code
            st.session_state.grade_level = student_grade
            st.session_state.course_description = course_description
            
            try:
                # Get current user email from session state
                user_email = st.session_state.user_email
                
                # Create course in DynamoDB
                create_course(
                    email=st.session_state.user_email,
                    course_code=st.session_state.course_code,
                    name=st.session_state.course_name,
                    description=st.session_state.course_description,
                    grade=st.session_state.grade_level
                )
                
                st.success("Course created successfully!")
                # Redirect to course page or dashboard
                st.switch_page("pages/dashboard.py") 
            except Exception as e:
                st.error(f"Error creating course: {str(e)}") 