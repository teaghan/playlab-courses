import streamlit as st
from utils.data.aws import get_file_content, upload_content_file, update_section, delete_content_file, update_section_assistant
from streamlit_pdf_viewer import pdf_viewer
import tempfile
import os
from utils.core.logger import logger
from utils.data.session_manager import SessionManager as sm
from utils.frontend.assistants import display_assistant_selection

st.set_page_config(page_title="Edit Section", 
                   page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png", 
                   layout="wide", initial_sidebar_state='collapsed')

# Check user state
sm.check_state(check_user=True)

# Display page buttons
from utils.frontend.menu import menu
menu()

# Get section details from session state
course_code = st.session_state.get("course_code")
section = st.session_state.get("section")
unit_id = section.unit_id

# Navigation
if st.columns((1, 3))[0].button('Return to Course Editor', use_container_width=True, type='primary'):
    st.switch_page('pages/edit_course.py')

# Display section title
st.markdown(f"# {section.title}")

# Section Details Section
st.markdown('##### Section Title')
section_title = st.text_input(
    "Title",
    value=section.title,
    label_visibility='collapsed'
)
st.markdown('##### Section Overview')
section_overview = st.text_area(
    "Overview",
    value=section.overview,
    height=100,
    label_visibility='collapsed'
)

# AI Assistant Selection
selected_assistant_id = display_assistant_selection(course_code, section)
# File upload section
st.markdown('### Change PDF File')
st.markdown('Upload a new PDF file to replace the current one.')
new_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    help="Select a PDF file to upload",
    label_visibility='collapsed'
)

# Save button
if st.button("Save Changes", type="primary", use_container_width=True):
    try:
        # Update section details
        if update_section(
            course_code=course_code,
            unit_id=unit_id,
            section_id=section.id,
            title=section_title,
            overview=section_overview
        ):
            # Update the assistant for this section
            if update_section_assistant(
                course_code=course_code,
                unit_id=unit_id,
                section_id=section.id,
                assistant_id=selected_assistant_id
            ):
                # If a new file was uploaded, handle the file update
                if new_file:
                    # Delete old file
                    if section.file_path:
                        # Extract filename from path
                        old_file_name = section.file_path.split('/')[-1]
                        delete_content_file(course_code, old_file_name)
                    
                    # Upload new file
                    new_file_path = upload_content_file(new_file, course_code, f"{section.id}.pdf")
                    if new_file_path:
                        # Update section with new file path
                        update_section(
                            course_code=course_code,
                            unit_id=unit_id,
                            section_id=section.id,
                            file_path=new_file_path
                        )
                        st.switch_page('pages/edit_course.py')
                    else:
                        st.error("Failed to upload new file")
                else:
                    st.session_state.section_updated = True
                    st.rerun()
            else:
                st.error("Failed to update section assistant")
        else:
            st.error("Failed to update section")
    except Exception as e:
        logger.error(f"Error updating section: {str(e)}")
        st.error(f"Error updating section: {str(e)}")

if st.session_state.get('section_updated', False):
    st.success("Section updated successfully!")
    st.session_state.section_updated = False

# Display current PDF
st.markdown('### Current PDF')
if section.file_path:
    try:
        # Get PDF content from S3
        pdf_content = get_file_content(section.file_path)
        if pdf_content:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_content)
                tmp_path = tmp_file.name
            
            # Display PDF using the temporary file
            pdf_viewer(tmp_path)
            
            # Clean up the temporary file
            os.unlink(tmp_path)
        else:
            st.error("Failed to retrieve current PDF")
    except Exception as e:
        logger.error(f"Error displaying PDF: {str(e)}")
        st.error("Error displaying current PDF")