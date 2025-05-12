import streamlit as st
import json
from st_equation_editor import mathfield
from playlab_api import PlaylabApp
import time
from utils.session import reset_chatbot
from utils.styling import button_style, columns_style, scroll_to

custom_button = button_style()
#custom_columns = columns_style()

# Load model
def load_model(project_id):
    app = PlaylabApp(project_id=project_id, verbose=False)
    return app

# Function to stream text letter by letter
def stream_text(text):
    sentence = ""
    for letter in text:
        sentence += letter
        yield sentence

def escape_markdown(text: str) -> str:
    """
    Escapes markdown special characters in text to prevent markdown formatting.
    
    Args:
        text (str): The text to escape
        
    Returns:
        str: Text with markdown special characters escaped
    """
    # List of markdown special characters that need escaping
    markdown_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', 
                     '-', '.', '!', '|', '>', '~', '^']
    
    add_math = False
    if '\n\n#### Math Attachments:\n\n' in text:
        add_math = True
    
    if add_math:
        escaped_text, math_attachments = text.split('\n\n#### Math Attachments:\n\n')
    else:    
       escaped_text = text

    for char in markdown_chars:
        escaped_text = escaped_text.replace(char, '\\' + char)

    if add_math:
        escaped_text = escaped_text + '\n\n#### Math Attachments:\n\n' + math_attachments
    
    return escaped_text

# Equation Editor
@st.dialog("Math Editor", width='small' if st.session_state.get('on_mobile', False) else 'large')
def equation_editor(on_mobile):

    if on_mobile:
        attach_math_button = st.button("Attach Math", 
                                    type='primary',
                                    use_container_width=True)
    else:
        attach_math_button = st.columns((1,1,1))[1].button("Attach Math", 
                                                    type='primary',
                                                    use_container_width=True)
    tex, _ = mathfield("")

    if attach_math_button:
        if tex:
            # Strip \mathrm{}
            st.session_state.math_attachments.append(tex)
        st.rerun()

# Display conversation
def display_conversation(project_id, message_fn, math_input=False):
    # Avatar images
    avatar = {"user": "https://raw.githubusercontent.com/teaghan/ai-tutors/main/images/AIT_student_avatar1.png",
            "assistant": "https://raw.githubusercontent.com/teaghan/ai-tutors/main/images/AIT_avatar2.png"}

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "math_attachments" not in st.session_state:
        st.session_state.math_attachments = []
    if "drop_file" not in st.session_state:
        st.session_state.drop_file = False
    if "model_loaded" not in st.session_state:
        st.session_state.model_loaded = False

    if not st.session_state.model_loaded:
        st.session_state.ai_app = load_model(project_id)
        st.session_state.messages.append({"role": "assistant", "content": rf"{st.session_state.ai_app.initial_message}"})    
        st.session_state.model_loaded = True

    if len(st.session_state.messages)>0:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.chat_message(msg["role"], avatar=avatar[msg["role"]]).markdown(escape_markdown(rf"{msg["content"]}"))
            else:
                st.chat_message(msg["role"], avatar=avatar[msg["role"]]).markdown(rf"{msg["content"]}")
        next_user_message = st.empty()
        next_assistant_message = st.empty()
        st.session_state.chat_spinner = st.container()

    on_mobile = st.session_state.get('on_mobile', False)
    print(f'on_mobile: {on_mobile}')

    # Organize buttons based on screen size
    if on_mobile:
        #custom_columns()
        col1, col2, col3 = st.columns((1, 1, 1))
    else:
        col1, col2, col3 = st.columns((1, 1, 1))

    # File upload button
    with col1:
        custom_button()
        if st.button("📎", help="Attach file"):
            st.session_state.drop_file = True

    # Reset chat button
    with col2:
        custom_button()
        if st.button("🔄", use_container_width=False, help="Reset chat"):
            reset_chatbot()
            st.rerun()
        
    # Calculator button
    if math_input:
        with col3:
            custom_button()
            if st.button("![Calculator](https://raw.githubusercontent.com/teaghan/ai-tutors/main/images/calculator.png)",
                        help="Type an equation"):
                equation_editor(on_mobile)

    if st.session_state.drop_file:
        # File uploader
        dropped_files = st.file_uploader("File Uploader",
                    help="Attach a file to your message", 
                    label_visibility='collapsed',
                    accept_multiple_files=False, 
                    type=["pdf", "docx", "pptx", "png", "jpg", "csv", "txt", "xlsx", "tsv", "gif", "webp"],
                    key="file_upload")
    else:
        dropped_files = []
    # Create a container for both audio and chat input
    input_container = st.container()

    with input_container:

        # Text input
        prompt = st.chat_input(key='chat_input_text')

        # Display math attachments
        if st.session_state.math_attachments:
            st.markdown("#### Math Attachments:")
            for i, attachment in enumerate(st.session_state.math_attachments):
                col1, col2 = st.columns([1, 8])
                with col2:
                    st.markdown(f'**Expression {i+1}:**  ${attachment}$')
                with col1:
                    if st.button("Remove", key=f"delete_math_{i}", 
                                use_container_width=False):
                        st.session_state.math_attachments.pop(i)
                        st.rerun()

    response = {'message': ''}
    if prompt:
        # Process dropped files
        file_path = None
        if dropped_files:
            for file in dropped_files:
                try:
                    with st.session_state.chat_spinner, st.spinner(f"Processing: {file.name}"):
                        file_path = 'test'
                except Exception as e:
                    st.error(f"Error processing {file.name}: {str(e)}")
                    st.exception(e)
            del st.session_state[f'file_upload']
            st.session_state.drop_file = False

        # Add the math attachments to the prompt
        if st.session_state.math_attachments:
            prompt += f'\n\n#### Math Attachments:\n\n'
            for i, attachment in enumerate(st.session_state.math_attachments):
                prompt += f'Expression {i+1}: ${attachment}$\n\n'
            st.session_state.math_attachments = []

        # Add the user's prompt to the conversation
        st.session_state.messages.append({"role": "user", "content": prompt})
        with next_user_message:
            st.chat_message("user", avatar=avatar["user"]).markdown(escape_markdown(prompt))

        # Get the response from the tutor
        if message_fn:
            prompt = message_fn(prompt)
        print(prompt)
        response = st.session_state.ai_app.send_message(prompt, file_path=file_path)

        # The response string can be parsed directly
        response = json.loads(response['content'])
        st.session_state.messages.append({"role": "assistant", "content": rf"{response['message']}"})    
        st.session_state.email_sent = False
        # Display the response letter by letter
        with next_assistant_message.chat_message("assistant", avatar=avatar["assistant"]):
            with st.empty():
                for sentence in stream_text(response['message']):
                    st.markdown(sentence)
                    time.sleep(0.02)

        # Re-run the app to update the conversation
        st.rerun()

    st.header(' ', anchor='bottom')
    scroll_to('bottom')

    return response