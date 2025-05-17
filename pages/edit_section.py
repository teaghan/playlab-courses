import streamlit as st
from streamlit_lexical import streamlit_lexical

# Page configuration
st.set_page_config(page_title="Edit Section", 
                   page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", 
                   layout="wide", initial_sidebar_state='collapsed')

from utils.menu import menu
from utils.session import check_state
from utils.aws import update_section, update_section_assistant
from utils.playlab import display_conversation
from utils.config import open_config
from utils.error_handling import catch_error
from utils.assistants import get_assistant_options

# Check user state
check_state(check_user=True)

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

# Display section title
st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state['section_title']}</h1>", unsafe_allow_html=True)

if st.columns((1, 3))[0].button('Return to Course Editor', use_container_width=True, type='primary'):
    st.switch_page('pages/edit_course.py')

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

# AI Assistant Selection
st.markdown('##### AI Assistant')
assistant_options = get_assistant_options(st.session_state['course_code'])

# Get current assistant if set
current_assistant = st.session_state.get('assistant_id', "Default")
if not any(a['id'] == current_assistant for a in assistant_options):
    current_assistant = "Default"

selected_assistant = st.selectbox(
    "Select an AI assistant for this section",
    options=[a['name'] for a in assistant_options],
    index=[a['id'] for a in assistant_options].index(current_assistant),
    help="Choose which AI assistant will help students with this section"
)

# Get the selected assistant ID
selected_assistant_id = assistant_options[[a['name'] for a in assistant_options].index(selected_assistant)]['id']

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

# Save button
if st.button("Save Section", type="primary", use_container_width=True):
    try:
        if update_section(
            course_code=st.session_state['course_code'],
            unit_id=st.session_state['unit_id'],
            section_id=st.session_state['section_id'],
            title=st.session_state['section_title'],
            overview=st.session_state['section_overview'],
            content=st.session_state['editor_content']
        ):
            # Update the assistant for this section
            if update_section_assistant(
                course_code=st.session_state['course_code'],
                unit_id=st.session_state['unit_id'],
                section_id=st.session_state['section_id'],
                assistant_id=selected_assistant_id
            ):
                st.success("Section updated successfully!")
            else:
                catch_error()
        else:
            catch_error()
    except Exception as e:
        catch_error()

st.markdown('### Preview:')
with st.container(height=750):
    st.markdown(st.session_state['editor_content'], unsafe_allow_html=True)
