import streamlit as st
from streamlit_lexical import streamlit_lexical

# Page configuration
st.set_page_config(page_title="Edit Lesson", page_icon="https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png", layout="wide")

from utils.menu import menu
from utils.session import check_state
from utils.aws import update_lesson
from utils.playlab import display_conversation
from utils.config import open_config

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

# Display lesson title
st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state['lesson_title']}</h1>", unsafe_allow_html=True)

if st.columns((3, 1))[1].button('Return to Course Editor', use_container_width=True, type='primary'):
    st.switch_page('pages/edit_course.py')

# Lesson Details Section
st.markdown('### Lesson Details')
st.markdown('##### Lesson Title')
lesson_title = st.text_input(
    "Title",
    value=st.session_state['lesson_title'],
    label_visibility='collapsed'
)
st.markdown('##### Lesson Overview')
lesson_overview = st.text_area(
    "Overview",
    value=st.session_state['lesson_overview'],
    height=100,
    label_visibility='collapsed'
)

col1, col2 = st.columns([1, 1])

def message_fn(message):
    return f'''{{
    "message": "{message}",
    "course_name": "{st.session_state.get('course_name', '')}",
    "unit_title": "{st.session_state.get('unit_title', '')}",
    "lesson_title": "{lesson_title}",
    "content": "{st.session_state.get("editor_content", "")}"
}}'''

def response_fn(response):
    if 'content' in response:
        print("Found content!")
        st.session_state['editor_content'] = response['content']
        st.session_state['update_editor'] = True
        st.rerun()

with col1:
    st.markdown('### Lesson Assistant')
    with st.container(height=800):
        response = display_conversation(open_config()['playlab']['lesson_editor'], message_fn, math_input=False, user='teacher', response_fn=response_fn)

# Lesson Editor
with col2:
    st.markdown('### Lesson Editor')
    # Create an instance of our component
    streamlit_lexical(
        value=st.session_state['editor_content'] if st.session_state.get('update_editor', True) else None,
        placeholder="Enter lesson content",
        key='editor',
        height=750,
        overwrite=True,
        on_change=on_change_editor
    )

# Save button
if st.button("Save Lesson", type="primary", use_container_width=True):
    try:
        if update_lesson(
            course_code=st.session_state['course_code'],
            unit_id=st.session_state['unit_id'],
            lesson_id=st.session_state['lesson_id'],
            title=st.session_state['lesson_title'],
            overview=st.session_state['lesson_overview'],
            content=st.session_state['editor_content']
        ):
            st.success("Lesson updated successfully!")
            #st.switch_page('pages/edit_course.py')
        else:
            st.error("Failed to update lesson")
    except Exception as e:
        st.error(f"Error updating lesson: {str(e)}")

st.markdown('### Lesson Preview')
with st.expander("Show Lesson Preview", expanded=False):
    st.markdown(st.session_state['editor_content'], unsafe_allow_html=True)
