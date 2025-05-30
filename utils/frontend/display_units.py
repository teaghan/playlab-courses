import streamlit as st
import uuid
from utils.data.aws import create_section, delete_unit, delete_section, update_unit, get_file_content, update_section_orders, upload_content_file
from utils.data.session_manager import SessionManager as sm
from utils.frontend.clipboard import to_clipboard
from utils.data.aws import create_unit
from utils.core.config import domain_url
from st_draggable_list import DraggableList
from utils.frontend.playlab import moderate_content
from utils.data.course_manager import SectionSmall

def display_units(course_code: str, allow_editing: bool = True):
    """Display units and sections for a course with management options"""
    # Get and display units
    if st.session_state.course_units:
        # Sort units by order
        sorted_units = sorted(st.session_state.course_units, key=lambda x: x.order)
        
        for unit in sorted_units:
            # Unit container
            with st.container():
                # Unit header with title and description
                st.markdown(f'#### Unit {unit.order}')
                st.markdown(f"### {unit.title}")
                st.markdown(unit.description)
                
                # Add expander for editing unit details only if editing is allowed
                if allow_editing:
                    with st.expander("Edit Unit Details"):
                        st.markdown('##### Unit Title')
                        unit_title = st.text_input(
                            "Title",
                            value=unit.title,
                            label_visibility='collapsed',
                            key=f'unit_title_{unit.order}'
                        )
                        st.markdown('##### Unit Description')
                        unit_description = st.text_area(
                            "Description",
                            value=unit.description,
                            height=100,
                            label_visibility='collapsed',
                            key=f'unit_description_{unit.order}'
                        )
                        
                        if unit.sections:
                            # Sort sections by order
                            sorted_sections = sorted(unit.sections, key=lambda x: x.order)
                            
                            # Add section reordering
                            st.markdown('##### Reorder Sections')
                            # Convert sections to list of dictionaries for DraggableList
                            section_items = [{"id": section.id, "name": section.title, "order": int(section.order)} for section in sorted_sections]
                            #st.code(section_items)
                            with st.columns((1,1))[0]:
                                st.markdown("Drag and drop sections to reorder them")
                                sorted_section_items = DraggableList(section_items, key=f'section_sort_{unit.id}')
                            #st.code(sorted_section_items)

                        # Unit action buttons in columns
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("Save Changes", key=f'save_unit_{unit.id}', type="primary", use_container_width=True):
                                if update_unit(
                                    course_code=course_code,
                                    unit_id=unit.id,
                                    title=unit_title,
                                    description=unit_description
                                ):
                                    # If the order has changed, update the database
                                    if unit.sections and sorted_sections != section_items:
                                        # Create list of (section_id, new_order) tuples from the sorted items
                                        section_orders = [(item['id'], i+1) for i, item in enumerate(sorted_section_items)]
                                        
                                        if update_section_orders(course_code, unit.id, section_orders):
                                            clear_sort_session_state()
                                        else:
                                            st.error("Failed to update section order")
                                    st.session_state[f'unit_updated_{unit.id}'] = True
                                    st.rerun()
                                else:
                                    st.error("Failed to update unit")
                        
                        with col3:
                            if st.button("Delete Unit", key=f"delete_unit_{unit.id}", use_container_width=True, type="secondary"):
                                delete_unit_confirm(unit.title, course_code, unit.id)
                        if st.session_state.get(f'unit_updated_{unit.id}', False):
                            st.success("Unit updated successfully")
                            st.session_state.pop(f'unit_updated_{unit.id}')
                
                # Display sections
                if unit.sections:
                    # Sort sections by order
                    sorted_sections = sorted(unit.sections, key=lambda x: x.order)
                    
                    # Indent sections using columns
                    with st.columns((1, 4))[1]:
                        with st.expander("**Sections**"):
                            st.markdown('---')
                            for section in sorted_sections:
                                with st.container():
                                    st.markdown(f"#### {section.title}")
                                    st.markdown(section.overview)
                                    
                                    # Display section content based on type
                                    section_type = section.section_type
                                    
                                    # Other section action buttons only shown if editing is allowed
                                    if allow_editing:
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            # Show edit button based on section type
                                            if section_type == 'content':
                                                if st.button("Edit", key=f'edit_section_{section.id}', use_container_width=True, type="primary"):
                                                    # Reset chat bot
                                                    sm.reset_chatbot()
                                                    # Initialize section in session state
                                                    sm.initialize_section(unit.id, section.id)
                                                    st.session_state["editor_content"] = st.session_state.section.content
                                                    st.session_state["update_editor"] = True
                                                    st.session_state["template_content"] = ''
                                                    st.switch_page('pages/edit_section.py')
                                            elif section_type == 'file':
                                                if st.button("Edit", key=f'edit_file_{section.id}', use_container_width=True, type="primary"):
                                                    # Initialize section in session state
                                                    sm.initialize_section(unit.id, section.id)
                                                    st.session_state["section_file_path"] = st.session_state.section.file_path
                                                    st.session_state['pdf_content'] = get_file_content(st.session_state.section.file_path)
                                                    st.switch_page('pages/edit_file.py')
                                        
                                        with col2:
                                            if st.button("Delete", key=f'delete_section_{section.id}', use_container_width=True, type="secondary"):
                                                delete_section_confirm(
                                                    section.title,
                                                    course_code,
                                                    unit.id,
                                                    section.id
                                                )
                                        with col3:
                                            if st.button("🔗", help='Share link to section', 
                                                         key=f'share_section_{section.id}', use_container_width=False, type="secondary"):
                                                section_url = f"{domain_url()}/view_section?{section.id}"
                                                to_clipboard(section_url)
                                                st.success("Section URL copied to clipboard")
                                    else:
                                        # View Section button is always available
                                        if st.button("View", key=f'view_section_{section.id}', type="primary", use_container_width=True):
                                            # Reset chat bot
                                            sm.reset_chatbot()
                                            # Initialize section in session state
                                            sm.initialize_section(unit.id, section.id)
                                            if st.session_state.section.section_type == 'file':
                                                st.session_state['pdf_content'] = get_file_content(st.session_state.section.file_path)
                                            else:
                                                st.session_state['pdf_content'] = ''                                            
                                            st.switch_page('pages/view_section.py')
                                    st.markdown('---')
                if allow_editing:
                    with st.columns((1, 4))[1]:
                        # Add Section button
                        if st.button("Add Section", key=f"add_section_{unit.id}", use_container_width=True, type="primary"):
                            add_section_dialog(course_code, unit.id)
                st.markdown('---')
    if allow_editing:
        with st.columns((1,2,1))[1]:
            # Add Unit button
            if st.button("Add Unit", type="primary", use_container_width=True):
                add_unit_dialog()

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
                next_order = len(st.session_state.course_units) + 1
                
                # Create the unit using order as ID
                create_unit(
                    course_code=st.session_state.course_code,
                    unit_id=str(next_order),
                    title=unit_name,
                    description=unit_description,
                    order=next_order
                )
                clear_sort_session_state()
                st.rerun()
            else:
                st.session_state.add_unit_banner.error("Please enter a unit name")
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Add Section")
def add_section_dialog(course_code: str, unit_id: str):
    """Show dialog for adding a new section"""
    if 'add_section_step' not in st.session_state:
        st.session_state.add_section_step = 1

    section_name_container = st.empty()
    section_overview_container = st.empty()
    st.session_state.add_section_banner = st.empty()
    next_button_container = st.empty()
    
    if st.session_state.add_section_step == 1:
        with st.container():
            st.session_state.new_section_name = section_name_container.text_input(
                "Section Title", 
                placeholder="e.g. The Solar System"
            )
            st.session_state.new_section_overview = section_overview_container.text_area(
                "Section Overview", 
                placeholder="Enter the section overview...", 
                height=100
            )
            next_button = next_button_container.button("Next", use_container_width=True, type="primary")
            
        if next_button:
            if st.session_state.new_section_name and st.session_state.new_section_overview:
                section_name_container.empty()
                section_overview_container.empty()
                next_button_container.empty()
                st.session_state.add_section_step = 2
            else:
                st.session_state.add_section_banner.error("Please enter both section name and overview")

    if st.session_state.add_section_step == 2:
        with st.container():
            st.markdown(f"### Create your \"{st.session_state.new_section_name}\" section with existing files and AI assistance")
            
            # Get all content sections
            content_sections = []
            for unit in st.session_state.course_units:
                content_sections.extend([
                    {
                        'title': section.title,
                        'unit_title': unit.title,
                        'unit_id': unit.id,
                        'section_id': section.id
                    }
                    for section in unit.sections 
                    if section.section_type == 'content'
                ])
            
            if content_sections:
                st.markdown("You can use an existing section as a template:")
                template_options = [f"{s['title']} (from {s['unit_title']})" for s in content_sections]
                template_section = st.selectbox(
                    "Select a template section",
                    options=template_options,
                    label_visibility='collapsed',
                    index=None,
                    placeholder="Choose a template section..."
                )
                
                if template_section:
                    selected_title = template_section.split(" (from ")[0]
                    selected_section = next(s for s in content_sections if s['title'] == selected_title)
                    st.session_state['template_content'] = sm.get_section(selected_section['unit_id'], selected_section['section_id']).content
            
            if st.button("Create Section with AI", type="primary", use_container_width=True):
                # Generate a unique section ID
                section_id = str(uuid.uuid4())
                
                # Get the next order number by finding the current unit and its sections
                current_unit = next((u for u in st.session_state.course_units if u.id == unit_id), None)
                next_order = len(current_unit.sections) + 1 if current_unit and current_unit.sections else 1
                
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
                    # Reset dialog state
                    st.session_state.add_section_step = 1
                    st.session_state.new_section_name = None
                    st.session_state.new_section_overview = None
                    # Reset chat bot
                    sm.reset_chatbot()
                    # Initialize section in session state
                    sm.initialize_section(unit_id, section_id)
                    st.session_state["editor_content"] = ''
                    st.session_state["update_editor"] = True
                    st.switch_page('pages/edit_section.py')
                else:
                    st.session_state.add_section_banner.error("Failed to create section")

            st.markdown("---")
            st.markdown("### Or upload a pdf to represent your section")
            dropped_file = st.file_uploader(
                "File Uploader",
                help="Attach a file to your message", 
                label_visibility='collapsed',
                accept_multiple_files=False, 
                type=["pdf"],
                key="file_upload"
            )

            if dropped_file:
                if st.button("Create Section with File", type="primary", use_container_width=True):
                    # Generate a unique section ID
                    section_id = str(uuid.uuid4())
                    
                    # Get the next order number by finding the current unit and its sections
                    current_unit = next((u for u in st.session_state.course_units if u.id == unit_id), None)
                    next_order = len(current_unit.sections) + 1 if current_unit and current_unit.sections else 1
                    
                    # Moderator
                    st.session_state.moderator_spinner = st.container()
                    st.session_state.section = SectionSmall(
                    id=section_id,
                    title=st.session_state.new_section_name,
                    section_type='file',
                    unit_id=unit_id,
                    unit_title=current_unit.title
                )
                    is_appropriate, feedback = moderate_content(
                        section_title=st.session_state.new_section_name,
                        section_type='file',
                        file_obj=dropped_file
                    )
                    
                    if not is_appropriate:
                        st.session_state.add_section_banner.error(f'Your file could not be saved. {feedback}')
                    else:
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
                                
                                st.session_state.add_section_step = 1
                                st.session_state.new_section_name = None
                                st.session_state.new_section_overview = None
                                # Initialize section in session state
                                sm.initialize_section(unit_id, section_id)
                                st.session_state["section_file_path"] = st.session_state.section.file_path
                                st.session_state['pdf_content'] = get_file_content(st.session_state.section.file_path)
                                st.switch_page('pages/edit_file.py')
                            else:
                                st.session_state.add_section_banner.error("Failed to upload file")
    
    if st.button("Cancel", use_container_width=True):
        st.session_state.new_section_name = None
        st.session_state.new_section_overview = None
        st.session_state.add_section_step = 1
        st.session_state.template_content = None
        st.rerun()

@st.dialog("Delete Unit")
def delete_unit_confirm(unit_name: str, course_code: str, unit_id: str):
    """Show confirmation dialog for unit deletion"""
    st.markdown(f'Are you sure you want to delete the unit, "*{unit_name}*"?')
    st.warning("This will also delete all sections in this unit.")
    st.session_state.delete_banner = st.empty()
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Delete Unit", type="primary", use_container_width=True):
            if delete_unit(course_code, unit_id):
                clear_sort_session_state()
                st.rerun()
            else:
                st.session_state.delete_banner.error("Failed to delete unit")
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("Delete Section")
def delete_section_confirm(section_name: str, course_code: str, unit_id: str, section_id: str):
    """Show confirmation dialog for section deletion"""
    st.markdown(f'Are you sure you want to delete the section, "*{section_name}*"?')
    st.session_state.delete_banner = st.empty()
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Delete Section", type="primary", use_container_width=True):
            if delete_section(course_code, unit_id, section_id):
                clear_sort_session_state()
                st.rerun()
            else:
                st.session_state.delete_banner.error("Failed to delete section")
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def clear_sort_session_state():
    """Clear sorting-related session state variables."""
    # Remove unit sort if it exists
    if 'unit_sort' in st.session_state:
        del st.session_state['unit_sort']
    
    # Find and remove all section sort keys
    section_sort_keys = [key for key in st.session_state.keys() if key.startswith('section_sort_')]
    for key in section_sort_keys:
        del st.session_state[key] 