import streamlit as st
from utils.session import check_state
from utils.aws import get_course_details, create_unit, get_course_units, update_course, delete_unit, delete_section, update_unit_orders
from utils.display_units import display_units
from utils.reorder_items import create_sortable_list
from utils.export import export_course
from utils.config import domain_url
from utils.clipboard import to_clipboard

st.set_page_config(page_title="Edit Course", 
                   page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", 
                   layout="wide", initial_sidebar_state='collapsed')

# Check user state
check_state(check_user=True)

# Display page buttons
from utils.menu import menu
menu()

# Get course code from session state
course_code = st.session_state.get("course_code")

# Get course details
course_details = get_course_details(course_code)
if not course_details:
    st.error("Course not found")
    st.switch_page("app.py")

# Get course metadata
metadata = next((item for item in course_details if item["SK"] == "METADATA"), None)
if not metadata:
    st.error("Course metadata not found")
    st.switch_page("app.py")

# Store course metadata in session state if not already present
if "course_name" not in st.session_state:
    st.session_state.course_name = metadata.get('name', '')
if "course_description" not in st.session_state:
    st.session_state.course_description = metadata.get('description', '')
if "grade_level" not in st.session_state:
    st.session_state.grade_level = metadata.get('grade_level', 6)

# Display course header
st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state.course_name}</h1>", unsafe_allow_html=True)

# Add Unit Dialog
@st.dialog("Export Course Files")
def export_dialog():
    if 'export_complete' not in st.session_state:
        st.session_state.export_complete = False
    if not st.session_state.export_complete:
        with st.spinner("Processing files..."):
            zip_data = export_course(course_code, st.session_state.course_name)
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
    if st.button("Copy Course URL", key=f'copy_url_{course_code}', use_container_width=True, type="primary"):
        course_url = f"{domain_url()}?{course_code}"
        to_clipboard(course_url)
        st.success("Copied!")
with col2:
    if st.button("Export Course", 
                 help="Download the course files as docx and txt",
                 key=f'download_{course_code}', use_container_width=True, type="secondary"):
        export_dialog()

# Course Details Section
st.markdown(st.session_state.course_description)

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
    
    st.markdown('##### Course Description')
    course_description = st.text_area(
        'Description',
        value=st.session_state.course_description,
        height=100,
        label_visibility='collapsed'
    )
    
    # Unit Reordering
    st.markdown('#### Reorder Units')
    units = get_course_units(course_code)
    if units:
        # Sort units by order
        units.sort(key=lambda x: x.get('order', 0))
        
        # Create a list of unit titles for sorting
        unit_items = [unit.get('title') for unit in units]
        
        # Add the sortable list
        with st.columns((1,1))[0]:
            st.markdown("Drag and drop units to reorder them")
            sorted_items = create_sortable_list(unit_items, key='unit_sort')
            
            # Store the sorted items in session state for form submission
            st.session_state.sorted_unit_items = sorted_items
    
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
                    grade=student_grade
                ):
                    # If unit order has changed, update it
                    if 'sorted_unit_items' in st.session_state and st.session_state.sorted_unit_items != unit_items:
                        # Create a mapping of unit titles to their IDs
                        title_to_id = {unit.get('title'): unit.get('SK').replace('UNIT#', '') for unit in units}
                        
                        # Create list of (unit_id, new_order) tuples
                        unit_orders = [(title_to_id[title], i+1) for i, title in enumerate(st.session_state.sorted_unit_items)]
                        
                        if update_unit_orders(course_code, unit_orders):
                            st.rerun()
                        else:
                            st.error("Course details updated but failed to update unit order")
                    else:
                        st.rerun()
                else:
                    st.error("Failed to update course details")
            except Exception as e:
                st.error(f"Error updating course: {str(e)}")

# Display units and sections
st.markdown("## Course Content")
display_units(course_code)

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

with st.columns((1,2,1))[1]:
    # Add Unit button
    if st.button("Add Unit", type="primary", use_container_width=True):
        add_unit_dialog()

# Delete Unit Dialog
@st.dialog("Delete Unit")
def delete_unit_confirm(unit_name, course_code, unit_id):
    """
    Show confirmation dialog for unit deletion
    """
    st.markdown(f'Are you sure you want to delete the unit, "*{unit_name}*"?')
    st.warning("This will also delete all sections in this unit.")
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

# Delete Section Dialog
@st.dialog("Delete Section")
def delete_section_confirm(section_name, course_code, unit_id, section_id):
    """
    Show confirmation dialog for section deletion
    """
    st.markdown(f'Are you sure you want to delete the section, "*{section_name}*"?')
    st.session_state.delete_banner = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete Section", type="primary", use_container_width=True):
            if delete_section(course_code, unit_id, section_id):
                st.rerun()
            else:
                st.session_state.delete_banner.error("Failed to delete section")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()