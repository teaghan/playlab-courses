import streamlit as st
from utils.aws import get_file_content, upload_content_file, update_section, delete_content_file
from streamlit_pdf_viewer import pdf_viewer
import tempfile
import os
from utils.logger import logger
from utils.session import check_state

st.set_page_config(page_title="Edit Section", 
                   page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", 
                   layout="wide", initial_sidebar_state='collapsed')

# Check user state
check_state(check_user=True)

# Display page buttons
from utils.menu import menu
menu()

# Initialize session state variables if they don't exist
if "unit_id" not in st.session_state:
    st.error("No unit selected. Please return to the course page.")
    st.switch_page("app.py")

if "section_id" not in st.session_state:
    st.error("No section selected. Please return to the course page.")
    st.switch_page("app.py")

# Get section details
unit_id = st.session_state["unit_id"]
section_id = st.session_state["section_id"]
course_code = st.session_state.get("course_code")
file_path = st.session_state.get("section_file_path")

# Navigation
if st.columns((1, 3))[0].button('Return to Course Editor', use_container_width=True, type='primary'):
    st.session_state['template_content'] = ''
    st.switch_page('pages/edit_course.py')

# Display section title
st.markdown(f"# {st.session_state['section_title']}")

# Section Details Section
st.markdown('##### Section Title')
section_title = st.text_input(
    "Title",
    value=st.session_state['section_title'],
    label_visibility='collapsed'
)
st.markdown('##### Section Overview')
section_overview = st.text_area(
    "Overview",
    value=st.session_state['section_overview'],
    height=100,
    label_visibility='collapsed'
)


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
            section_id=section_id,
            title=section_title,
            overview=section_overview
        ):
            # If a new file was uploaded, handle the file update
            if new_file:
                # Delete old file
                if file_path:
                    # Extract filename from path
                    old_file_name = file_path.split('/')[-1]
                    delete_content_file(course_code, old_file_name)
                
                # Upload new file
                new_file_path = upload_content_file(new_file, course_code, f"{section_id}.pdf")
                if new_file_path:
                    # Update section with new file path
                    update_section(
                        course_code=course_code,
                        unit_id=unit_id,
                        section_id=section_id,
                        file_path=new_file_path
                    )
                    st.success("Section and file updated successfully!")
                    st.session_state['template_content'] = ''
                    st.switch_page('pages/edit_course.py')
                else:
                    st.error("Failed to upload new file")
            else:
                st.success("Section details updated successfully!")
                st.session_state['template_content'] = ''
        else:
            st.error("Failed to update section")
    except Exception as e:
        logger.error(f"Error updating section: {str(e)}")
        st.error(f"Error updating section: {str(e)}") 

# Display current PDF
st.markdown('### Current PDF')
if file_path:
    try:
        # Get PDF content from S3
        pdf_content = get_file_content(file_path)
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