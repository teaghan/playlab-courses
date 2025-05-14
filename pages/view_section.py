import streamlit as st
from utils.aws import get_file_content, s3, bucket_name
from streamlit_pdf_viewer import pdf_viewer
import tempfile
import os
from utils.logger import logger
from utils.session import check_state
from utils.docx import markdownToWordFromString

st.set_page_config(page_title=f"{st.session_state['section_title']}", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", layout="wide")

# Check user state
check_state(check_user=False)

# Display page buttons
from utils.menu import menu
menu()


# Download Dialog
@st.dialog("Download Section")
def download_dialog(section_type, section_title, content=None, file_path=None):
    if 'download_complete' not in st.session_state:
        st.session_state.download_complete = False
    
    if not st.session_state.download_complete:
        if section_type == 'content':
            with st.spinner("Preparing document..."):
                # Create a temporary file for the DOCX
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    markdownToWordFromString(content, tmp_file.name)
                    with open(tmp_file.name, 'rb') as docx_file:
                        docx_bytes = docx_file.read()
                    os.unlink(tmp_file.name)
                    st.download_button(
                        label="Download as DOCX",
                        data=docx_bytes,
                        file_name=f"{section_title}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        type="primary",
                        on_click=lambda: setattr(st.session_state, 'download_complete', True)
                    )
        elif section_type == 'file' and file_path:
            with st.spinner("Preparing PDF..."):
                if st.session_state['pdf_content']:
                    st.download_button(
                        label="Download PDF",
                        data=st.session_state['pdf_content'],
                        file_name=os.path.basename(file_path),
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary",
                        on_click=lambda: setattr(st.session_state, 'download_complete', True)
                    )
                else:
                    st.error("Failed to retrieve PDF content")
    else:
        if st.button("Close", use_container_width=True, type="primary"):
            st.session_state.download_complete = False
            st.rerun()

# Display section content based on type
if st.session_state['section_type'] == 'content':
    # Add download button
    if st.columns((3,1))[1].button("Download .docx", use_container_width=True, type="secondary"):
        download_dialog(
            section_type='content',
            section_title=st.session_state['section_title'],
            content=st.session_state['section_content']
        )
    # Display markdown content
    st.markdown(st.session_state['section_content'], unsafe_allow_html=True)
    
elif st.session_state['section_type'] == 'file':
    # Display PDF file
    file_path = st.session_state['section_file_path']
    if file_path:
        try:
            # Get PDF content from S3
            if st.session_state['pdf_content']:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(st.session_state['pdf_content'])
                    tmp_path = tmp_file.name
                
                # Add download button
                if st.button("Download PDF", use_container_width=True, type="secondary"):
                    download_dialog(
                        section_type='file',
                        section_title=st.session_state['section_title'],
                        file_path=file_path
                    )

                # Display PDF using the temporary file
                pdf_viewer(tmp_path)
                
                # Clean up the temporary file
                os.unlink(tmp_path)
            else:
                st.error(f"Failed to retrieve PDF content.")
                logger.error(f"Failed to retrieve PDF content for path: {file_path}")
        except Exception as e:
            logger.error(f"Error displaying PDF: {str(e)}")
    else:
        st.error("No file path specified for this section") 