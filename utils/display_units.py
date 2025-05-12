import streamlit as st
import uuid
from utils.aws import get_course_units, get_unit_lessons, create_unit, create_lesson, delete_unit, delete_lesson

def display_units(course_code):
    """
    Display units and lessons for a course with management options
    """
    # Get and display units
    units = get_course_units(course_code)
    if units:
        # Sort units by order
        units.sort(key=lambda x: x.get('order', 0))
        
        for unit in units:
            # Unit container
            with st.container():
                # Unit header with title and description
                st.markdown(f"### 📚 {unit.get('title')}")
                st.markdown(unit.get('description', ''))
                
                cols = st.columns((1,1,1))
                # Add Lesson button for this unit
                if cols[0].button("Add Lesson", key=f"add_lesson_{unit.get('SK')}", use_container_width=True, type="primary"):
                    add_lesson_dialog(unit.get('SK').replace('UNIT#', ''))
                
                if cols[1].button("Edit Unit Home Page", key=f"edit_unit_home_{unit.get('SK')}", use_container_width=True, type="secondary"):
                    pass
                
                if cols[2].button("Delete Unit", key=f"delete_unit_{unit.get('SK')}", use_container_width=True, type="secondary"):
                    delete_unit_confirm(unit.get('title'), course_code, unit.get('SK').replace('UNIT#', ''))
                
                # Get and display lessons for this unit
                unit_id = unit.get('SK').replace('UNIT#', '')
                lessons = get_unit_lessons(course_code, unit_id)
                if lessons:
                    # Sort lessons by order
                    lessons.sort(key=lambda x: x.get('order', 0))
                    
                    # Indent lessons using columns
                    with st.columns((1, 4))[1]:
                        for lesson in lessons:
                            with st.container():
                                st.markdown('---')
                                st.markdown(f"#### 📝 {lesson.get('title')}")
                                st.markdown(lesson.get('content', ''))
                                
                                # Create columns for lesson actions
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Edit Lesson", key=f'edit_lesson_{lesson.get("SK")}', use_container_width=True, type="primary"):
                                        # Set lesson details in session state
                                        st.session_state["unit_id"] = unit_id
                                        st.session_state["unit_title"] = unit.get('title')
                                        st.session_state["lesson_id"] = lesson.get("SK").replace("LESSON#", "")
                                        st.session_state["lesson_title"] = lesson.get('title')
                                        st.session_state["lesson_content"] = lesson.get('content', '')
                                        st.switch_page('pages/edit_lesson.py')
                                with col2:
                                    if st.button("Delete Lesson", key=f'delete_lesson_{lesson.get("SK")}', use_container_width=True):
                                        delete_lesson_confirm(
                                            lesson.get('title'),
                                            course_code,
                                            unit_id,
                                            lesson.get("SK").replace("LESSON#", "")
                                        )
                
                st.markdown('---')

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
                units = get_course_units(st.session_state.course_code)
                next_order = len(units) + 1
                
                # Create the unit using order as ID
                create_unit(
                    course_code=st.session_state.course_code,
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
                lessons = get_unit_lessons(st.session_state.course_code, unit_id)
                next_order = len(lessons) + 1
                
                # Create the lesson
                create_lesson(
                    course_code=st.session_state.course_code,
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