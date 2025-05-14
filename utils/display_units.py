import streamlit as st
import uuid
from utils.aws import get_course_units, get_unit_lessons, create_unit, create_lesson, delete_unit, delete_lesson, update_unit, update_lesson, update_lesson_orders, upload_content_file
from utils.reorder_items import create_sortable_list
from utils.session import reset_chatbot

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
                st.markdown(f"### {unit.get('title')}")
                st.markdown(unit.get('description', ''))
                
                # Add expander for editing unit details
                with st.expander("Edit Unit Details"):
                    st.markdown('##### Unit Title')
                    unit_title = st.text_input(
                        "Title",
                        value=unit.get('title'),
                        label_visibility='collapsed'
                    )
                    st.markdown('##### Unit Description')
                    unit_description = st.text_area(
                        "Description",
                        value=unit.get('description', ''),
                        height=100,
                        label_visibility='collapsed'
                    )
                    
                    # Get lessons for this unit
                    unit_id = unit.get('SK').replace('UNIT#', '')
                    lessons = get_unit_lessons(course_code, unit_id)
                    if lessons:
                        # Sort lessons by order
                        lessons.sort(key=lambda x: x.get('order', 0))
                        
                        # Add lesson reordering
                        st.markdown('##### Reorder Lessons')
                        lesson_items = [lesson.get('title') for lesson in lessons]
                        with st.columns((1,1))[0]:
                            st.markdown("Drag and drop lessons to reorder them")
                            sorted_lesson_items = create_sortable_list(lesson_items, key=f'lesson_sort_{unit_id}')
                        
                        # If the order has changed, update the database
                        if sorted_lesson_items != lesson_items:
                            # Create a mapping of lesson titles to their IDs
                            title_to_id = {lesson.get('title'): lesson.get('SK').replace('LESSON#', '') for lesson in lessons}
                            
                            # Create list of (lesson_id, new_order) tuples
                            lesson_orders = [(title_to_id[title], i+1) for i, title in enumerate(sorted_lesson_items)]
                            
                            if update_lesson_orders(course_code, unit_id, lesson_orders):
                                st.rerun()
                            else:
                                st.error("Failed to update lesson order")
                    
                    # Unit action buttons in columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Save Changes", key=f'save_unit_{unit.get("SK")}', type="primary", use_container_width=True):
                            if update_unit(
                                course_code=course_code,
                                unit_id=unit.get('SK').replace('UNIT#', ''),
                                title=unit_title,
                                description=unit_description
                            ):
                                st.rerun()
                            else:
                                st.error("Failed to update unit")
                    
                    with col2:
                        if st.button("Edit Unit Home Page", key=f"edit_unit_home_{unit.get('SK')}", use_container_width=True, type="secondary"):
                            pass
                    
                    with col3:
                        if st.button("Delete Unit", key=f"delete_unit_{unit.get('SK')}", use_container_width=True, type="secondary"):
                            delete_unit_confirm(unit.get('title'), course_code, unit.get('SK').replace('UNIT#', ''))
                
                # Display lessons
                if lessons:
                    # Sort lessons by order
                    lessons.sort(key=lambda x: x.get('order', 0))
                    
                    # Indent lessons using columns
                    with st.columns((1, 4))[1]:
                        st.markdown('---')
                        for lesson in lessons:
                            with st.container():
                                st.markdown(f"#### {lesson.get('title')}")
                                st.markdown(lesson.get('overview', ''))
                                
                                # Display lesson content based on type
                                lesson_type = lesson.get('lesson_type', 'content')

                                # Add expander for editing lesson details
                                with st.expander("Edit Lesson Details"):
                                    st.markdown('##### Lesson Title')
                                    lesson_title = st.text_input(
                                        "Title",
                                        value=lesson.get('title'),
                                        label_visibility='collapsed'
                                    )
                                    st.markdown('##### Lesson Overview')
                                    lesson_overview = st.text_area(
                                        "Overview",
                                        value=lesson.get('overview', ''),
                                        height=100,
                                        label_visibility='collapsed'
                                    )
                                    
                                    # Lesson action buttons in columns
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if st.button("Save Changes", key=f'save_lesson_{lesson.get("SK")}', type="primary", use_container_width=True):
                                            if update_lesson(
                                                course_code=course_code,
                                                unit_id=unit_id,
                                                lesson_id=lesson.get("SK").replace("LESSON#", ""),
                                                title=lesson_title,
                                                overview=lesson_overview
                                            ):
                                                st.rerun()
                                            else:
                                                st.error("Failed to update lesson")
                                    
                                    with col2:
                                        # Only show edit button for content-type lessons
                                        if lesson_type == 'content':
                                            if st.button("Edit Lesson Content", key=f'edit_lesson_content_{lesson.get("SK")}', use_container_width=True, type="secondary"):
                                                # Reset chat bot
                                                reset_chatbot()
                                                # Set lesson details in session state
                                                st.session_state["unit_id"] = unit_id
                                                st.session_state["unit_title"] = unit.get('title')
                                                st.session_state["lesson_id"] = lesson.get("SK").replace("LESSON#", "")
                                                st.session_state["lesson_title"] = lesson.get('title')
                                                st.session_state["lesson_overview"] = lesson.get('overview', '')
                                                st.session_state["editor_content"] = lesson.get('content', '')
                                                st.session_state["update_editor"] = True
                                                st.switch_page('pages/edit_lesson.py')
                                    
                                    with col3:
                                        if st.button("Delete Lesson", key=f'delete_lesson_{lesson.get("SK")}', use_container_width=True, type="secondary"):
                                            delete_lesson_confirm(
                                                lesson.get('title'),
                                                course_code,
                                                unit_id,
                                                lesson.get("SK").replace("LESSON#", "")
                                            )
                                st.markdown('---')
                with st.columns((1, 4))[1]:
                    # Add Lesson button
                    if st.button("Add Lesson", key=f"add_lesson_{unit.get('SK')}", use_container_width=True, type="primary"):
                        add_lesson_dialog(course_code, unit.get('SK').replace('UNIT#', ''))
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
def add_lesson_dialog(course_code, unit_id):
    st.markdown("### Add New Lesson")
    lesson_name = st.text_input("Lesson Name", placeholder="e.g. The Solar System")
    lesson_overview = st.text_area("Lesson Overview", placeholder="Enter the lesson overview...", height=100)
    
    st.markdown("Either **create your lesson with your files and AI**")

    st.session_state.add_lesson_banner = st.empty()
    
    if st.button("Create Lesson with AI", type="primary", use_container_width=True):
        if lesson_name and lesson_overview:
            dropped_file = []
            # Generate a unique lesson ID
            lesson_id = str(uuid.uuid4())
            # Get the next order number
            lessons = get_unit_lessons(course_code, unit_id)
            next_order = len(lessons) + 1
            
            # Get unit details
            units = get_course_units(course_code)
            unit = next((u for u in units if u.get('SK') == f'UNIT#{unit_id}'), None)
            if not unit:
                st.session_state.add_lesson_banner.error("Failed to get unit details")
                return
            
            # Create the lesson
            if create_lesson(
                course_code=course_code,
                unit_id=unit_id,
                lesson_id=lesson_id,
                title=lesson_name,
                overview=lesson_overview,
                order=next_order,
                lesson_type="content"
            ):
                # Reset chat bot
                reset_chatbot()
                # Set lesson details in session state
                st.session_state["unit_id"] = unit_id
                st.session_state["unit_title"] = unit.get('title')
                st.session_state["lesson_id"] = lesson_id
                st.session_state["lesson_title"] = lesson_name
                st.session_state["lesson_overview"] = lesson_overview
                st.session_state["editor_content"] = ""
                st.session_state["update_editor"] = True
                # Navigate to edit lesson page
                st.switch_page('pages/edit_lesson.py')
            else:
                st.session_state.add_lesson_banner.error("Failed to create lesson")
        else:
            st.session_state.add_lesson_banner.error("Please enter both lesson name and overview")

    st.markdown("Or upload a pdf to represent your lesson")
    dropped_file = st.file_uploader("File Uploader",
                    help="Attach a file to your message", 
                    label_visibility='collapsed',
                    accept_multiple_files=False, 
                    type=["pdf"],
                    key="file_upload")

    if dropped_file:
        if st.button("Create Lesson with File", type="primary", use_container_width=True):
            if lesson_name and lesson_overview:
                # Generate a unique lesson ID
                lesson_id = str(uuid.uuid4())
                # Get the next order number
                lessons = get_unit_lessons(course_code, unit_id)
                next_order = len(lessons) + 1
                
                # Upload file to S3
                file_path = upload_content_file(dropped_file, course_code, f"{lesson_id}.pdf")
                if file_path:
                    # Create the lesson with file
                    create_lesson(
                        course_code=course_code,
                        unit_id=unit_id,
                        lesson_id=lesson_id,
                        title=lesson_name,
                        overview=lesson_overview,
                        order=next_order,
                        lesson_type="file",
                        file_path=file_path
                    )
                    st.rerun()
                else:
                    st.session_state.add_lesson_banner.error("Failed to upload file")
            else:
                st.session_state.add_lesson_banner.error("Please enter both lesson name and overview")

    if st.button("Cancel", use_container_width=True):
        dropped_file = []
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