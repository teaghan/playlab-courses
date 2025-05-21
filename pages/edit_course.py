import streamlit as st
import os
from utils.data.aws import update_course, update_unit_orders
from utils.frontend.display_units import display_units, clear_sort_session_state
from utils.documents.export import export_course
from utils.core.config import domain_url
from utils.frontend.clipboard import to_clipboard
from utils.core.error_handling import catch_error
from utils.frontend.assistants import display_assistant_management
from utils.data.session_manager import SessionManager as sm
from st_draggable_list import DraggableList

st.set_page_config(
    page_title="Edit Course", 
    page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png", 
    layout="wide", 
    initial_sidebar_state='collapsed'
)

# Check user state
sm.check_state(check_user=True)

# Display page buttons
from utils.frontend.menu import menu
menu()

# Get course code from session state
course_code = st.session_state.get("course_code")
if not course_code:
    st.error("No course selected")
    st.switch_page("app.py")

# Initialize course data
try:
    course_init = sm.initialize_course(course_code)
except:
    catch_error()
    course_init = False

if not course_init:
    st.error("Course not found")
    st.switch_page("app.py")

# Display course header
st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state.course_name}</h1>", 
            unsafe_allow_html=True)

# Add Unit Dialog
@st.dialog("Export Course Files")
def export_dialog():
    if 'export_complete' not in st.session_state:
        st.session_state.export_complete = False
    if not st.session_state.export_complete:
        with st.spinner("Processing files..."):
            zip_path = export_course(course_code, st.session_state.course_name)
            # Read the zip file contents
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            # Clean up the temporary file
            os.unlink(zip_path)
            st.session_state.export_complete = True
        st.download_button(label="Download Files", 
                        data=zip_data, 
                        file_name=f"{st.session_state.course_name}.zip",
                        use_container_width=True,
                        type="primary")
    else:
        if st.button("Close", use_container_width=True, type="primary"):
            st.session_state.export_complete = False
            st.rerun()

_,col1, col2 = st.columns((3,1,1))
with col1:
    course_url = f"{domain_url()}/view_course?{course_code}"
    if st.button("Copy Course URL", key=f'copy_url_{course_code}', use_container_width=True, type="primary"):
        to_clipboard(course_url)

with col2:
    if st.button("Export Course", 
                 help="Download the course files as docx and txt",
                 key=f'download_{course_code}', use_container_width=True, type="secondary"):
        export_dialog()

# Course Details Section
st.markdown(st.session_state.course_description, unsafe_allow_html=True)

# Course editing expander
with st.expander("Edit Course Details"):
    st.markdown('##### Course Name')
    course_name = st.text_input(
        'Name',
        value=st.session_state.course_name,
        label_visibility='collapsed'
    )
    
    st.markdown('##### Student Grade Level')
    student_grade = st.columns((1,10,1))[1].select_slider(
        'Grade',
        label_visibility='collapsed',
        options=list(range(0, 14)),
        format_func=lambda x: 'K' if x == 0 else 'Adult' if x == 13 else x,
        value=st.session_state.grade_level,
        help='Select the grade level for this course'
    )
    
    st.markdown('##### Course Availability')
    availability = st.selectbox(
        'Availability',
        options=['requires_code', 'open_to_all'],
        format_func=lambda x: 'Requires Course Code' if x == 'requires_code' else 'Open to All',
        index=0 if st.session_state.get('course_availability', 'requires_code') == 'requires_code' else 1,
        label_visibility='collapsed',
        help='Control who can access this course'
    )
    
    st.markdown('##### Course Description')
    course_description = st.text_area(
        'Description',
        value=st.session_state.course_description,
        height=100,
        label_visibility='collapsed'
    )
    
    # Unit Reordering
    st.markdown('#### Reorder Units')
    if st.session_state.course_units:
        # Sort units by order
        sorted_units = sorted(st.session_state.course_units, key=lambda x: x.order)
        
        # Create a list of unit titles for sorting
        unit_items = [{"id": unit.id, "name": unit.title, "order": int(unit.order)} for unit in sorted_units]
        # Add the sortable list
        with st.columns((1,1))[0]:
            st.markdown("Drag and drop units to reorder them")
            sorted_unit_items = DraggableList(unit_items, key='unit_sort')
    
    # Action buttons in columns
    with st.columns((1,2,1))[1]:
        if st.button("Save Changes", type="primary", use_container_width=True):
            try:
                # Update course with new details
                if update_course(
                    email=st.session_state.user_email,
                    course_code=course_code,
                    name=course_name,
                    description=course_description,
                    grade=student_grade,
                    availability=availability
                ):
                    # If unit order has changed, update it
                    if st.session_state.course_units and sorted_unit_items != unit_items:                                
                        # Create list of (unit_id, new_order) tuples
                        unit_orders = [(item['id'], i+1) for i, item in enumerate(sorted_unit_items)]
                        
                        if update_unit_orders(course_code, unit_orders):
                            st.session_state.course_updated = True
                            clear_sort_session_state()
                            st.rerun()
                        else:
                            catch_error()
                    else:
                        st.session_state.course_updated = True
                        st.rerun()
                else:
                    catch_error()
            except Exception as e:
                catch_error()
        if st.session_state.get('course_updated', False):
            st.success("Course updated successfully")
            st.session_state.course_updated = False
st.markdown('---')
# AI Assistant Management Section
display_assistant_management(course_code)
st.markdown('---') 
# Display units and sections
st.markdown("## 📚 Course Content")
st.markdown('---')
display_units(course_code)