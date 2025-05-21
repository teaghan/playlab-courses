import streamlit as st
from streamlit_lexical import streamlit_lexical
from utils.data.aws import create_custom_assistant, get_custom_assistants, delete_custom_assistant
from utils.core.config import open_config
from utils.core.error_handling import catch_error

@st.dialog("Add New Assistant", width='large')
def add_assistant_dialog(course_code, custom_assistants):
    """
    Dialog for creating a new AI assistant
    """
    st.markdown("### Create New Assistant")
    st.markdown("#### Assistant Name")
    assistant_name = st.text_input("Assistant Name", label_visibility='collapsed', placeholder="e.g. Assignment Helper")
    st.markdown("#### Assistant Instructions")
    assistant_instructions = streamlit_lexical(
        value=open_config()['playlab']['student_assistant_default_system_prompt'],
        key='assistant_instructions',
        height=400,
        overwrite=True,
    )

    if st.button("Create Assistant", type="primary", use_container_width=True):
        if not assistant_name:
            st.error("Please enter an assistant name")
        elif not assistant_instructions:
            st.error("Please enter assistant instructions")
        else:
            # Check if name already exists
            if any(a['name'] == assistant_name for a in custom_assistants):
                st.error("An assistant with this name already exists")
            else:
                assistant_id = create_custom_assistant(course_code, assistant_name, assistant_instructions)
                if assistant_id:
                    st.success("Assistant created successfully!")
                    st.rerun()
                else:
                    catch_error()

@st.dialog("Edit Assistant", width='large')
def edit_assistant_dialog(assistant):
    """
    Dialog for editing an existing AI assistant
    """
    st.markdown("### Edit Assistant")
    st.markdown("#### Assistant Name")
    assistant_name = st.text_input("Assistant Name", value=assistant['name'], label_visibility='collapsed')
    st.markdown("#### Assistant Instructions")
    assistant_instructions = streamlit_lexical(
        value=assistant['instructions'],
        key='edit_assistant_instructions',
        height=400,
        overwrite=True,
    )

    if st.button("Save Changes", key='save_changes', type="primary", use_container_width=True):
        if not assistant_name:
            st.error("Please enter an assistant name")
        elif not assistant_instructions:
            st.error("Please enter assistant instructions")
        else:
            # Check if new name conflicts with other assistants
            custom_assistants = get_custom_assistants(st.session_state['course_code'])
            if assistant_name != assistant['name'] and any(a['name'] == assistant_name for a in custom_assistants):
                st.error("An assistant with this name already exists")
            else:
                # Delete old assistant and create new one with updated info
                if delete_custom_assistant(st.session_state['course_code'], assistant['assistant_id']):
                    new_assistant_id = create_custom_assistant(st.session_state['course_code'], assistant_name, assistant_instructions)
                    if new_assistant_id:
                        st.success("Assistant updated successfully!")
                        st.rerun()
                    else:
                        catch_error()
                else:
                    catch_error()

def display_assistant_management(course_code):
    """
    Display the AI assistant management section
    """
    st.markdown("## 🤖 AI Assistants")

    with st.expander("Manage the Course AI Assistants"):
        st.markdown("Create and manage custom AI assistants for your course. These assistants will be available for your students to use while viewing course content.")

        # Get existing custom assistants
        custom_assistants = get_custom_assistants(course_code)

        # Display existing assistants
        if custom_assistants:
            st.markdown("### Your Custom Assistants")
            st.markdown("---")
            for assistant in custom_assistants:
                st.markdown(f"#### **{assistant['name']}**")
                col1, col2, col3 = st.columns((1,1,2))
                with col1:
                    if st.button("Edit Assistant", key=f"edit_{assistant['assistant_id']}", type="primary", use_container_width=True):
                        edit_assistant_dialog(assistant)
                with col2:
                    if st.button("Delete Assistant", key=f"delete_{assistant['assistant_id']}", type="secondary", use_container_width=True):
                        if delete_custom_assistant(course_code, assistant['assistant_id']):
                            st.success("Assistant deleted successfully!")
                            st.rerun()
                        else:
                            catch_error()
                st.markdown("---")

        # Add New Assistant button
        if st.columns((1,2,1))[1].button("Add New Assistant", type="primary", use_container_width=True):
            add_assistant_dialog(course_code, custom_assistants)

def display_assistant_selection(course_code, section):
    # AI Assistant Selection
    st.markdown('##### AI Assistant')
    assistant_options = get_assistant_options(course_code)

    # Get current assistant if set
    current_assistant = section.assistant_id if section.assistant_id is not None else "Default"

    # Find the index of the current assistant in the options
    try:
        current_index = next(i for i, a in enumerate(assistant_options) if str(a['id']) == str(current_assistant))
    except StopIteration:
        current_index = next(i for i, a in enumerate(assistant_options) if a['id'] == "Default")

    selected_assistant = st.selectbox(
        "Select an AI assistant for this section",
        options=[a['name'] for a in assistant_options],
        index=current_index,
        help="Choose which AI assistant will help students with this section"
    )

    # Get the selected assistant ID
    selected_assistant_id = assistant_options[[a['name'] for a in assistant_options].index(selected_assistant)]['id']

    return selected_assistant_id


def get_assistant_options(course_code):
    """
    Get list of available assistant options for a section
    """
    assistant_options = [
        {"id": "None", "name": "None"},
        {"id": "Default", "name": "Default"}
    ]
    custom_assistants = get_custom_assistants(course_code)
    assistant_options.extend([{"id": a['assistant_id'], "name": a['name']} for a in custom_assistants])
    return assistant_options

def get_assistant_instructions(course_code, section):
    """
    Get instructions for a specific assistant
    """
    # Get assistant_id, handling both dictionary and Section objects
    if hasattr(section, 'assistant_id'):
        assistant_id = section.assistant_id
    else:
        assistant_id = section.get('assistant_id')
    
    # Handle None case first
    if assistant_id is None:
        return open_config()['playlab']['student_assistant_default_system_prompt']
    
    # Handle specific assistant IDs
    if assistant_id == "None":
        return None
    elif assistant_id == "Default":
        return open_config()['playlab']['student_assistant_default_system_prompt']
    else:
        # Get instructions from custom assistant
        custom_assistants = get_custom_assistants(course_code)
        for assistant in custom_assistants:
            if assistant['assistant_id'] == assistant_id:
                return assistant['instructions']
        # Fallback to default if assistant not found
        return open_config()['playlab']['student_assistant_default_system_prompt']