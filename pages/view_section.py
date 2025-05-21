import tempfile
import os
import re
import streamlit as st


st.set_page_config(
    page_title="View Section", 
    page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png", 
    layout="wide", 
)

from streamlit_pdf_viewer import pdf_viewer
from utils.data.session_manager import SessionManager as sm
from utils.core.error_handling import catch_error
from utils.frontend.download_section import download_dialog
from utils.frontend.student_assistant import display_student_assistant
from utils.frontend.menu import menu

# Get section ID from query params
params = st.query_params
if params and 'section_loaded' not in st.session_state:
    section_id = next(iter(params))
    sm.clear_user_context()
    try:
        section_loaded = sm.initialize_section_from_id(section_id)
    except Exception as e:
        catch_error()
        section_loaded = False
    
    if section_loaded:
        st.session_state['section_loaded'] = True
    
# Check user state
sm.check_state(check_user=False)

# Display page buttons
menu()

# Get section from session state
section = st.session_state.get("section")
if section is None:
    st.switch_page('pages/enter_course.py')

# Navigation
if st.columns((1, 3))[0].button('Return to Course', use_container_width=True, type='primary'):
    st.switch_page('pages/view_course.py')

# Display section content based on type
if section.section_type == 'content':
    # Add download button
    if st.columns((3,1))[1].button("Download .docx", use_container_width=True, type="secondary"):
        try:
            download_dialog(
                section_type='content',
                section_title=section.title,
                content=section.content
            )
        except Exception as e:
            catch_error()
    if st.session_state.section.assistant_instructions is not None and st.session_state.on_mobile:
        display_student_assistant()
    st.markdown(section.content or '', unsafe_allow_html=True)
elif section.section_type == 'file':
    if st.session_state.get('pdf_content'):
        # Add download button
        if st.columns((3,1))[1].button("Download PDF", use_container_width=True, type="secondary"):
            # Sanitize the section title for use as a filename
            safe_title = re.sub(r'[^\w\-_.]', '_', section.title)
            temp_filename = f"{safe_title}.pdf"
            
            # Create temporary file only when downloading
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix=f"{safe_title}_") as tmp_file:
                    tmp_file.write(st.session_state.pdf_content)
                    tmp_path = tmp_file.name
                    try:
                        download_dialog(
                            section_type='file',
                            section_title=section.title,
                            file_path=tmp_path
                        )
                    finally:
                        # Clean up the temporary file after download
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
            except Exception as e:
                catch_error()
                
        if st.session_state.section.assistant_instructions is not None and st.session_state.on_mobile:
            display_student_assistant()
        # Display PDF
        try:
            pdf_viewer(st.session_state.pdf_content)
        except Exception as e:
            catch_error()
            st.error("Error displaying PDF")
    else:
        st.error("File content not found") 