import streamlit as st
from st_equation_editor import mathfield
import tempfile
from playlab_api import PlaylabApp
import time
from utils.data.session_manager import SessionManager as sm
from utils.frontend.styling import button_style
from utils.core.logger import logger
from tempfile import NamedTemporaryFile
import os
from utils.core.error_handling import catch_error

custom_button = button_style()

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

def message_fn(message, role='student', section_title='', section_type='content', json=False):
    if role == 'teacher':
        message = f'''{{
        "message": """{message}""",
        "course_name": """{st.session_state.get('course_name', '')}""",
        "student_grade": """{st.session_state.get('grade_level', '')}""",
        "unit_title": """{st.session_state.section.unit_title}""",
        "module_title": """{section_title}""",
        "content": """{st.session_state.get("editor_content", "")}""",
        "template_content": """{st.session_state.get("template_content", "")}"""
    }}'''
    
    elif role == 'student':
        if len(st.session_state.messages) > 2:
            message = f'''{{
            "message": """{message}"""
            }}'''
        else:
            if section_type == 'file':
                message = f'''{{
                "message": """{message}""",
                "student_grade": """{st.session_state.get('grade_level', '')}""",
                "course_name": """{st.session_state.get('course_name', '')}""",
                "unit_title": """{st.session_state.section.unit_title}""",
                "module_title": """{section_title}""",
                "teacher_instructions": """{st.session_state.section.assistant_instructions}"""
                }}'''
            else:
                message = f'''{{
                "message": """{message}""",
                "student_grade": """{st.session_state.get('grade_level', '')}""",
                "course_name": """{st.session_state.get('course_name', '')}""",
                "unit_title": """{st.session_state.section.unit_title}""",
                "module_title": """{section_title}""",
                "content": """{st.session_state.section.content}""",
                "teacher_instructions": """{st.session_state.section.assistant_instructions}"""
                }}'''
    if json:
        return json.dumps(message)
    return message

def response_fn(response, role='student'):
    if role == 'teacher':
        if 'content' in response:
            st.session_state['editor_content'] = response['content']
            st.session_state['update_editor'] = True

def parse_ai_response(text: str) -> dict:
    """
    Parse a string to extract 'message' and 'content' values.
    Returns a dictionary containing the found keys and their values.
    Expects values to be surrounded by triple quotes.
    
    Args:
        text (str): Input string to parse
        
    Returns:
        dict: Dictionary with 'message' and/or 'content' keys and their corresponding values
    """
    result = {}
    keys = ['message', 'content']
    
    for key in keys:
        key_with_quotes = f'"{key}":'
        if key_with_quotes in text:
            # Find the start position after the key
            start_idx = text.index(key_with_quotes) + len(key_with_quotes)
            
            # Skip whitespace to find the triple quote
            while start_idx < len(text) and text[start_idx].isspace():
                start_idx += 1
            
            # Skip the opening triple quote
            if text.startswith('"""', start_idx):
                start_idx += 3
                
                # Find the closing triple quote
                end_idx = text.find('"""', start_idx)
                if end_idx != -1:
                    value = text[start_idx:end_idx]
                    result[key] = value
    
    return result

# Display conversation
def display_conversation(project_id, user='student', section_title='', section_type='content', max_retries=3):
    # Avatar images
    avatar = {"user": f"https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/{user}_avatar.png",
            "assistant": "https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/ai_avatar.png"}

    if user == 'teacher':
        math_input = False
    else:
        math_input = False

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "math_attachments" not in st.session_state:
        st.session_state.math_attachments = []
    if "drop_file" not in st.session_state:
        st.session_state.drop_file = False
    if "model_loaded" not in st.session_state:
        st.session_state.model_loaded = False
    if "file_upload_key" not in st.session_state:
        st.session_state.file_upload_key = 0

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
            sm.reset_chatbot()
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
                    key=f"file_upload_{st.session_state.file_upload_key}")
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
        # Process dropped file
        file_path = None
        temp_file = None
        if dropped_files:
            try:
                with st.session_state.chat_spinner, st.spinner(f"Processing: {dropped_files.name}"):
                    # Create a temporary file with the same extension
                    file_extension = dropped_files.name.split('.')[-1]
                    temp_file = NamedTemporaryFile(suffix=f'.{file_extension}', delete=False)
                    # Read the entire file content first
                    file_content = dropped_files.read()
                    # Write the content to the temporary file
                    temp_file.write(file_content)
                    temp_file.close()  # Close the file to ensure it's written
                    file_path = temp_file.name
            except Exception as e:
                st.error(f"Error processing {dropped_files.name}: {str(e)}")
                st.exception(e)
                if temp_file and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            del st.session_state[f'file_upload_{st.session_state.file_upload_key}']
            st.session_state.file_upload_key += 1
            st.session_state.drop_file = False

        # Add the math attachments to the prompt
        if st.session_state.math_attachments:
            prompt += f'\n\n#### Math Attachments:\n\n'
            for i, attachment in enumerate(st.session_state.math_attachments):
                prompt += f'Expression {i+1}: ${attachment}$\n\n'
            st.session_state.math_attachments = []

        if section_type == 'file' and len(st.session_state.messages) < 2:
            first_message = "Here is the file I am looking at, please let me know when you are ready to start."
            first_message = message_fn(first_message, user, section_title, section_type)
            logger.info(f'DEFAULT FIRST MESSAGE:\n\n{first_message}\n\n')
            with st.session_state.chat_spinner, st.spinner(f"Reading the PDF..."):
                # Load pdf to temporary file
                try:
                    # Get PDF content from S3
                    if st.session_state['pdf_content']:
                        # Create a temporary file
                        with tempfile.NamedTemporaryFile(delete=True, suffix='.pdf') as tmp_file:
                            tmp_file.write(st.session_state['pdf_content'])
                            tmp_path = tmp_file.name
                            _ = st.session_state.ai_app.send_message(first_message, file_path=tmp_path)
                except Exception as e:
                    logger.error(f"Error loading file: {str(e)}")
                    st.exception(e)

        # Add the user's prompt to the conversation
        st.session_state.messages.append({"role": "user", "content": prompt})
        with next_user_message:
            st.chat_message("user", avatar=avatar["user"]).markdown(escape_markdown(prompt))

        # Get the response from the tutor
        prompt = message_fn(prompt, user, section_title, section_type)

        retries = 0
        while retries < max_retries:
            with st.session_state.chat_spinner, st.spinner(f"Thinking..."):
                try:
                    logger.info(f'PROMPT:\n\n{prompt}\n\n')
                    response = st.session_state.ai_app.send_message(prompt, file_path=file_path)
                    logger.info(fr'RESPONSE: {response['content']}')
                    response = parse_ai_response(response['content'])
                    logger.info(fr'PARSED RESPONSE: {response}')
                except:
                    catch_error()
                # Check if "message" key is present
                if 'message' in response and response['message']:
                    break
                retries += 1
                prompt = 'There was an issue with the previous response. Perhaps the parsing was not able to interpret the response correctly. Please try again. Write your response to the user again.'
                
        
        # Set default error message if all retries failed
        if retries == max_retries:
            response['message'] = 'I am sorry, I am having trouble producing a response right now. Please try again later.'
        # Clean up the temporary file after we're done with it
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.error(f"Error deleting temporary file: {str(e)}")
        
        st.session_state.messages.append({"role": "assistant", "content": rf"{response['message']}"})    
        st.session_state.email_sent = False
        # Display the response letter by letter
        with next_assistant_message.chat_message("assistant", avatar=avatar["assistant"]):
            with st.empty():
                for sentence in stream_text(response['message']):
                    st.markdown(sentence)
                    time.sleep(0.005)

        response_fn(response, user)
        st.rerun()

    #st.header(' ', anchor='bottom')
    #scroll_to('bottom')

    return response