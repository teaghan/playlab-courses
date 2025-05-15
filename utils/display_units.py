import streamlit as st
import uuid
from utils.aws import get_course_units, get_unit_sections, create_unit, create_section, delete_unit, delete_section, update_unit, get_file_content, update_section_orders, upload_content_file
from utils.reorder_items import create_sortable_list
from utils.session import reset_chatbot

def display_units(course_code, allow_editing=True):
    """
    Display units and sections for a course with management options
    """
    # Get and display units
    units = get_course_units(course_code)
    if units:
        # Sort units by order
        units.sort(key=lambda x: x.get('order', 0))
        
        for unit in units:
            # Get sections for this unit
            unit_id = unit.get('SK').replace('UNIT#', '')
            sections = get_unit_sections(course_code, unit_id)
            # Unit container
            with st.container():
                # Unit header with title and description
                st.markdown(f"### {unit.get('title')}")
                st.markdown(unit.get('description', ''))
                
                # Add expander for editing unit details only if editing is allowed
                if allow_editing:
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
                        
                        if sections:
                            # Sort sections by order
                            sections.sort(key=lambda x: x.get('order', 0))
                            
                            # Add section reordering
                            st.markdown('##### Reorder Sections')
                            section_items = [section.get('title') for section in sections]
                            with st.columns((1,1))[0]:
                                st.markdown("Drag and drop sections to reorder them")
                                sorted_section_items = create_sortable_list(section_items, key=f'section_sort_{unit_id}')
                            
                            # If the order has changed, update the database
                            if sorted_section_items != section_items:
                                # Create a mapping of section titles to their IDs
                                title_to_id = {section.get('title'): section.get('SK').replace('SECTION#', '') for section in sections}
                                
                                # Create list of (section_id, new_order) tuples
                                section_orders = [(title_to_id[title], i+1) for i, title in enumerate(sorted_section_items)]
                                
                                if update_section_orders(course_code, unit_id, section_orders):
                                    st.rerun()
                                else:
                                    st.error("Failed to update section order")
                        
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
                        
                        with col3:
                            if st.button("Delete Unit", key=f"delete_unit_{unit.get('SK')}", use_container_width=True, type="secondary"):
                                delete_unit_confirm(unit.get('title'), course_code, unit.get('SK').replace('UNIT#', ''))
                
                # Display sections
                if sections:
                    # Sort sections by order
                    sections.sort(key=lambda x: x.get('order', 0))
                    
                    # Indent sections using columns
                    with st.columns((1, 4))[1]:
                        with st.expander("**Sections**"):
                            st.markdown('---')
                            for section in sections:
                                with st.container():
                                    st.markdown(f"#### {section.get('title')}")
                                    st.markdown(section.get('overview', ''))
                                    
                                    # Display section content based on type
                                    section_type = section.get('section_type', 'content')                                
                                    
                                    # Other section action buttons only shown if editing is allowed
                                    if allow_editing:
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            # Show edit button based on section type
                                            if section_type == 'content':
                                                if st.button("Edit", key=f'edit_section_{section.get("SK")}', use_container_width=True, type="primary"):
                                                    # Reset chat bot
                                                    reset_chatbot()
                                                    # Set section details in session state
                                                    st.session_state["unit_id"] = unit_id
                                                    st.session_state["unit_title"] = unit.get('title')
                                                    st.session_state["section_id"] = section.get("SK").replace("SECTION#", "")
                                                    st.session_state["section_title"] = section.get('title')
                                                    st.session_state["section_overview"] = section.get('overview', '')
                                                    st.session_state["editor_content"] = section.get('content', '')
                                                    st.session_state["update_editor"] = True
                                                    st.session_state['pdf_content'] = None
                                                    st.switch_page('pages/edit_section.py')
                                            elif section_type == 'file':
                                                if st.button("Edit", key=f'edit_file_{section.get("SK")}', use_container_width=True, type="primary"):
                                                    # Set section details in session state
                                                    st.session_state["unit_id"] = unit_id
                                                    st.session_state["unit_title"] = unit.get('title')
                                                    st.session_state["section_id"] = section.get("SK").replace("SECTION#", "")
                                                    st.session_state["section_title"] = section.get('title')
                                                    st.session_state["section_overview"] = section.get('overview', '')
                                                    st.session_state["section_file_path"] = section.get('file_path')
                                                    st.session_state['pdf_content'] = get_file_content(st.session_state["section_file_path"])
                                                    st.switch_page('pages/edit_file.py')
                                        
                                        with col2:
                                            if st.button("Delete", key=f'delete_section_{section.get("SK")}', use_container_width=True, type="secondary"):
                                                delete_section_confirm(
                                                    section.get('title'),
                                                    course_code,
                                                    unit_id,
                                                    section.get("SK").replace("SECTION#", "")
                                                    )
                                    else:
                                        # View Section button is always available
                                        if st.button("View", key=f'view_section_{section.get("SK")}', type="primary", use_container_width=True):
                                            st.session_state["unit_id"] = unit_id
                                            st.session_state["unit_title"] = unit.get('title')
                                            st.session_state["section_id"] = section.get("SK").replace("SECTION#", "")
                                            st.session_state['section_title'] = section.get('title')
                                            st.session_state['section_content'] = section.get('content', '')
                                            st.session_state["section_file_path"] = section.get('file_path', '')
                                            st.session_state['section_type'] = section.get('section_type')
                                            if st.session_state['section_type'] == 'file':
                                                st.session_state['pdf_content'] = get_file_content(st.session_state["section_file_path"])
                                            else:
                                                st.session_state['pdf_content'] = None
                                            reset_chatbot()
                                            st.switch_page('pages/view_section.py')
                                    st.markdown('---')
                if allow_editing:
                    with st.columns((1, 4))[1]:
                        # Add Section button
                        if st.button("Add Section", key=f"add_section_{unit.get('SK')}", use_container_width=True, type="primary"):
                            add_section_dialog(course_code, unit.get('SK').replace('UNIT#', ''))
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


@st.dialog("Add Section")
def add_section_dialog(course_code, unit_id):

    if 'add_section_step' not in st.session_state:
        st.session_state.add_section_step = 1

    section_name_container = st.empty()
    section_overview_container = st.empty()
    st.session_state.add_section_banner = st.empty()
    next_button_container = st.empty()
    if st.session_state.add_section_step == 1:
        
        with st.container():
            st.session_state.new_section_name = section_name_container.text_input("Section Title", placeholder="e.g. The Solar System")
            st.session_state.new_section_overview = section_overview_container.text_area("Section Overview", placeholder="Enter the section overview...", height=100)
            next_button = next_button_container.button("Next", use_container_width=True, type="primary")
        if next_button:
            if st.session_state.new_section_name and st.session_state.new_section_overview:
                section_name_container.empty()
                section_overview_container.empty()
                next_button_container.empty()
                st.session_state.add_section_step = 2
            else:
                st.session_state.add_section_banner.error("Please enter both section name and overview")

    if st.session_state.add_section_step==2:

        with st.container():
            st.markdown(f"### Create your \"{st.session_state.new_section_name}\" section with existing files and AI assistance")
            
            # Check for existing content sections across all units in the course
            all_units = get_course_units(course_code)
            content_sections = []
            for unit in all_units:
                unit_sections = get_unit_sections(course_code, unit.get('SK').replace('UNIT#', ''))
                content_sections.extend([
                    {
                        'title': s.get('title'),
                        'content': s.get('content', ''),
                        'unit_title': unit.get('title')
                    }
                    for s in unit_sections 
                    if s.get('section_type') == 'content' and s.get('content')
                ])
            
            if content_sections:
                st.markdown("You can use an existing section as a template:")
                # Create a list of formatted options that include both section and unit titles
                template_options = [f"{s['title']} (from {s['unit_title']})" for s in content_sections]
                template_section = st.selectbox(
                    "Select a template section",
                    options=template_options,
                    label_visibility='collapsed',
                    index=None,
                    placeholder="Choose a template section..."
                )
                
                if template_section:
                    # Extract the section title from the selected option
                    selected_title = template_section.split(" (from ")[0]
                    selected_section = next(s for s in content_sections if s['title'] == selected_title)
                    st.session_state['template_content'] = selected_section['content']
            
            if st.button("Create Section with AI", type="primary", use_container_width=True):
                dropped_file = []
                # Generate a unique section ID
                section_id = str(uuid.uuid4())
                # Get the next order number
                sections = get_unit_sections(course_code, unit_id)
                next_order = len(sections) + 1
                
                # Get unit details
                units = get_course_units(course_code)
                unit = next((u for u in units if u.get('SK') == f'UNIT#{unit_id}'), None)
                if not unit:
                    st.session_state.add_section_banner.error("Failed to get unit details")
                    return
                
                # Create the section
                if create_section(
                    course_code=course_code,
                    unit_id=unit_id,
                    section_id=section_id,
                    title=st.session_state.new_section_name,
                    overview=st.session_state.new_section_overview,
                    order=next_order,
                    section_type="content"
                ):
                    # Reset chat bot
                    reset_chatbot()
                    # Set section details in session state
                    st.session_state["unit_id"] = unit_id
                    st.session_state["unit_title"] = unit.get('title')
                    st.session_state["section_id"] = section_id
                    st.session_state["section_title"] = st.session_state.new_section_name
                    st.session_state["section_overview"] = st.session_state.new_section_overview
                    # Use template content if available, otherwise empty string
                    st.session_state["editor_content"] = ''
                    st.session_state.add_section_step = 1
                    st.session_state["update_editor"] = True
                    st.session_state.new_section_name = None
                    st.session_state.new_section_overview = None
                    # Navigate to edit section page
                    st.switch_page('pages/edit_section.py')
                else:
                    st.session_state.add_section_banner.error("Failed to create section")

            st.markdown("---")
            st.markdown("### Or upload a pdf to represent your section")
            dropped_file = st.file_uploader("File Uploader",
                            help="Attach a file to your message", 
                            label_visibility='collapsed',
                            accept_multiple_files=False, 
                            type=["pdf"],
                            key="file_upload")

            if dropped_file:
                if st.button("Create Section with File", type="primary", use_container_width=True):
                    # Generate a unique section ID
                    section_id = str(uuid.uuid4())
                    # Get the next order number
                    sections = get_unit_sections(course_code, unit_id)
                    next_order = len(sections) + 1
                    
                    # Upload file to S3
                    file_path = upload_content_file(dropped_file, course_code, f"{section_id}.pdf")
                    if file_path:
                        # Create the section with file
                        if create_section(
                            course_code=course_code,
                            unit_id=unit_id,
                            section_id=section_id,
                            title=st.session_state.new_section_name,
                            overview=st.session_state.new_section_overview,
                            order=next_order,
                            section_type="file",
                            file_path=file_path
                        ):
                            # Reset chat bot
                            reset_chatbot()
                            # Set section details in session state
                            st.session_state["unit_id"] = unit_id
                            st.session_state["unit_title"] = unit.get('title')
                            st.session_state["section_id"] = section_id
                            st.session_state["section_title"] = st.session_state.new_section_name
                            st.session_state["section_overview"] = st.session_state.new_section_overview
                            # Use template content if available, otherwise empty string
                            st.session_state.add_section_step = 1
                            st.session_state.new_section_name = None
                            st.session_state.new_section_overview = None

                            # Set section details in session state
                            st.session_state["section_file_path"] = file_path
                            st.session_state['pdf_content'] = get_file_content(st.session_state["section_file_path"])
                            st.switch_page('pages/edit_file.py')
                        else:
                            st.session_state.add_section_banner.error("Failed to upload file")
    
    if st.button("Cancel", use_container_width=True):
        dropped_file = []
        st.session_state.new_section_name = None
        st.session_state.new_section_overview = None
        st.session_state.add_section_step = 1
        st.session_state.template_content = None
        st.rerun()

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