import tempfile
import os
import streamlit as st
from utils.documents.docx import markdownToWordFromString

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