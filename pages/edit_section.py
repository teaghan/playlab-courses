import streamlit as st
from streamlit_lexical import streamlit_lexical

# Page configuration
st.set_page_config(page_title="Edit Section", 
                   page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/favicon.png", 
                   layout="wide", initial_sidebar_state='collapsed')

from utils.frontend.menu import menu
from utils.data.session_manager import SessionManager as sm
from utils.data.aws import update_section, update_section_assistant
from utils.frontend.playlab import display_conversation
from utils.core.config import open_config
from utils.core.error_handling import catch_error
from utils.frontend.assistants import display_assistant_selection

# Check user state
sm.check_state(check_user=True)

# Display page buttons
menu()

if 'update_editor' not in st.session_state:
    st.session_state['update_editor'] = True
if 'editor_initialized' not in st.session_state:
    st.session_state['editor_initialized'] = False

def on_change_editor():
    # Only update editor content and set update_editor to False if the editor has been initialized
    if st.session_state['editor_initialized']:
        st.session_state['editor_content'] = st.session_state['editor']
        st.session_state['update_editor'] = False
    else:
        st.session_state['editor_initialized'] = True

# Get section details from session state
course_code = st.session_state.get("course_code")
section = st.session_state.get("section")
unit_id = section.unit_id

# Display section title
st.markdown(f"<h1 style='text-align: center; color: grey;'>{section.title}</h1>", unsafe_allow_html=True)

if st.columns((1, 3))[0].button('Return to Course Editor', use_container_width=True, type='primary'):
    st.switch_page('pages/edit_course.py')

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


# Save button
if st.button("Save Section", type="primary", use_container_width=True):
    try:
        
        if update_section(
            course_code=course_code,
            unit_id=unit_id,
            section_id=section.id,
            title=section_title,
            overview=section_overview,
            content=st.session_state.get('editor_content')
        ):
            # Update the assistant for this section
            if update_section_assistant(
                course_code=course_code,
                unit_id=unit_id,
                section_id=section.id,
                assistant_id=selected_assistant_id
            ):
                st.session_state.section_updated = True
                st.rerun()
            else:
                catch_error()
        else:
            catch_error()
    except Exception as e:
        catch_error()

if st.session_state.get('section_updated', False):
    st.success("Section updated successfully!")
    st.session_state.section_updated = False

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('### Assistant')
    with st.container(height=650):
        response = display_conversation(open_config()['playlab']['section_editor'], user='teacher', section_title=section_title)

# Section Editor
with col2:
    st.markdown('### Editor')
    # Create an instance of our component
    streamlit_lexical(
        value=st.session_state['editor_content'] if st.session_state.get('update_editor', True) else None,
        placeholder="Enter section content",
        key='editor',
        height=600,
        overwrite=True,
        on_change=on_change_editor
    )


st.markdown('### Preview:')
with st.container(height=750):
    st.markdown(st.session_state.get('editor_content'), unsafe_allow_html=True)
