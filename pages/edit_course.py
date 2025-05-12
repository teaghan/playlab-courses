import streamlit as st
import uuid
from utils.session import check_state
from utils.menu import menu
from utils.aws import get_course_details, create_unit, get_course_units, create_lesson, get_unit_lessons, update_course, delete_unit, delete_lesson
from utils.display_courses import share_window
from utils.display_units import display_units

st.set_page_config(page_title="Edit Course", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", layout="wide")

# Check user state
check_state(check_user=True)

# Display page buttons
menu()

# Get course code from session state
course_code = st.session_state.get("course_code")

# Get course details
course_details = get_course_details(course_code)
if not course_details:
    st.error("Course not found")
    st.stop()

# Get course metadata
metadata = next((item for item in course_details if item["SK"] == "METADATA"), None)
if not metadata:
    st.error("Course metadata not found")
    st.stop()

# Store course metadata in session state if not already present
if "course_name" not in st.session_state:
    st.session_state.course_name = metadata.get('name', '')
if "course_description" not in st.session_state:
    st.session_state.course_description = metadata.get('description', '')
if "grade_level" not in st.session_state:
    st.session_state.grade_level = metadata.get('grade_level', 6)

# Display course header
st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state.course_name}</h1>", unsafe_allow_html=True)

with st.columns((5,1))[1]:
    if st.button("Share", key=f'share_{course_code}', use_container_width=True, type="primary"):
        share_window(course_code)

# Course editing form
with st.form("edit_course_form"):
    st.markdown("### Edit Course Details")
    
    # Course Name
    st.markdown('#### Course Name')
    course_name = st.text_input(
        'Name:',
        value=st.session_state.course_name,
        label_visibility='collapsed'
    )
    
    # Grade Level
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
    st.markdown('#### Course Description')
    course_description = st.text_area(
        'Description:',
        value=st.session_state.course_description,
        height=100,
        label_visibility='collapsed'
    )
    
    with st.columns((4,1))[1]:
        # Submit button
        submit_button = st.form_submit_button("Save Course Details", type="primary", use_container_width=True)
        
        if submit_button:
            try:
                # Update course with new details
                if update_course(
                    email=st.session_state.user_email,
                    course_code=course_code,
                    name=course_name,
                    description=course_description,
                    grade=student_grade
                ):
                    st.success("Course details updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update course details")
            except Exception as e:
                st.error(f"Error updating course: {str(e)}")

st.markdown("---")

st.markdown("## Course Home")
with st.columns((1,1,1))[1]:
    if st.button("Edit Course Home Page", key=f'edit_home_page_{course_code}', use_container_width=True, type="primary"):
        pass

st.markdown("---")

# Add Unit Dialog
@st.dialog("Add Unit")
def add_unit_dialog():
    st.markdown("### Add New Unit")
    unit_name = st.text_input("Unit Name", placeholder="e.g. Introduction to Astronomy")
    unit_description = st.text_area("Unit Description", placeholder="Describe what this unit covers...", height=100)
    st.session_state.add_unit_banner = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Unit", type="primary", use_container_width=True, key='add_unit'):
            if unit_name:
                # Get the next order number
                units = get_course_units(course_code)
                next_order = len(units) + 1
                
                # Create the unit using order as ID
                create_unit(
                    course_code=course_code,
                    unit_id=str(next_order),
                    title=unit_name,
                    description=unit_description,
                    order=next_order
                )
                st.rerun()
            else:
                st.session_state.add_unit_banner.error("Please enter a unit name")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# Add Lesson Dialog
@st.dialog("Add Lesson")
def add_lesson_dialog(unit_id):
    st.markdown("### Add New Lesson")
    lesson_name = st.text_input("Lesson Name", placeholder="e.g. The Solar System")
    lesson_overview = st.text_area("Lesson Overview", placeholder="Enter the lesson overview...", height=100)
    
    st.session_state.add_lesson_banner = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Lesson", type="primary", use_container_width=True):
            if lesson_name and lesson_overview:
                # Generate a unique lesson ID
                lesson_id = str(uuid.uuid4())
                # Get the next order number
                lessons = get_unit_lessons(course_code, unit_id)
                next_order = len(lessons) + 1
                
                # Create the lesson
                create_lesson(
                    course_code=course_code,
                    unit_id=unit_id,
                    lesson_id=lesson_id,
                    title=lesson_name,
                    overview=lesson_overview,
                    order=next_order
                )
                st.rerun()
            else:
                st.session_state.add_lesson_banner.error("Please enter both lesson name and content")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# Delete Unit Dialog
@st.dialog("Delete Unit")
def delete_unit_confirm(unit_name, course_code, unit_id):
    """
    Show confirmation dialog for unit deletion
    """
    st.markdown(f'Are you sure you want to delete the unit, "*{unit_name}*"?')
    st.warning("This will also delete all lessons in this unit.")
    st.session_state.delete_banner = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete Unit", type="primary", use_container_width=True):
            if delete_unit(course_code, unit_id):
                st.rerun()
            else:
                st.session_state.delete_banner.error("Failed to delete unit")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# Delete Lesson Dialog
@st.dialog("Delete Lesson")
def delete_lesson_confirm(lesson_name, course_code, unit_id, lesson_id):
    """
    Show confirmation dialog for lesson deletion
    """
    st.markdown(f'Are you sure you want to delete the lesson, "*{lesson_name}*"?')
    st.session_state.delete_banner = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete Lesson", type="primary", use_container_width=True):
            if delete_lesson(course_code, unit_id, lesson_id):
                st.rerun()
            else:
                st.session_state.delete_banner.error("Failed to delete lesson")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# Display units and lessons
st.markdown("## Course Units")
display_units(course_code)

with st.columns((1,1,1))[0]:
    # Add Unit button
    if st.button("Add Unit", type="primary", use_container_width=True):
        add_unit_dialog()