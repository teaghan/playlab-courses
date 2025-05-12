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

# Get lesson details from session state
lesson_id = st.session_state.get("lesson_id")
unit_id = st.session_state.get("unit_id")
course_code = st.session_state.get("course_code")

if not all([lesson_id, unit_id, course_code]):
    st.error("Lesson details not found. Please return to the course editor.")
    st.stop()

# Initialize session state for editor
if 'editor_content' not in st.session_state:
    st.session_state['editor_content'] = st.session_state.get("lesson_content", "")
st.session_state['update_editor'] = True

def on_change_editor():
    st.session_state['editor_content'] = st.session_state['editor']
    st.session_state['update_editor'] = False

# Display lesson title
st.markdown(f"<h1 style='text-align: center; color: grey;'>{st.session_state.get('lesson_title', 'Edit Lesson')}</h1>", unsafe_allow_html=True)

if st.columns((5, 1))[1].button('Return to Course Editor', use_container_width=True, type='primary'):
    st.switch_page('pages/edit_course.py')

col1, col2 = st.columns([1, 1])

def message_fn(message):
    return f'''{{
    "message": "{message}",
    "course_name": "{st.session_state.get('course_name', '')}",
    "unit_title": "{st.session_state.get('unit_title', '')}",
    "lesson_title": "{st.session_state.get('lesson_title', '')}",
    "lesson_content": "{st.session_state.get("editor_content", "")}"
}}'''

with col1:
    st.markdown('### Lesson Assistant')
    with st.container(height=800):
        response = display_conversation(open_config()['playlab']['lesson_editor'], message_fn, math_input=False)

if 'lesson_content' in response:
    pass
    #st.session_state['editor_content'] = response['lesson_content']

# Lesson Editor
with col2:
    st.markdown('### Lesson Editor')
    # Create an instance of our component
    streamlit_lexical(
        value=st.session_state['editor_content'] if st.session_state.get('update_editor', True) else None,
        placeholder="Enter lesson content",
        key='editor',
        height=800,
        overwrite=False,
        on_change=on_change_editor
    )

st.markdown('### Lesson Preview')
with st.expander("Show Lesson Preview", expanded=False):
    st.markdown(st.session_state['editor_content'], unsafe_allow_html=True)

# Save button
if st.button("Save Lesson", type="primary", use_container_width=True):
    try:
        if update_lesson(
            course_code=course_code,
            unit_id=unit_id,
            lesson_id=lesson_id,
            content=st.session_state['editor_content']
        ):
            st.success("Lesson updated successfully!")
            st.switch_page('pages/edit_course.py')
        else:
            st.error("Failed to update lesson")
    except Exception as e:
        st.error(f"Error updating lesson: {str(e)}")

# Cancel button
if st.button("Cancel", use_container_width=True):
    st.switch_page('pages/edit_course.py')