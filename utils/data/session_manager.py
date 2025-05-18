import streamlit as st
from utils.data.course_manager import CourseManager, Unit, Section
from utils.data.user_manager import UserManager
from utils.data.aws import get_file_content
from utils.frontend.styling import load_style
from utils.core.memory_manager import initialize_memory_and_heartbeat, update_session_activity
from utils.frontend.check_window import on_mobile

class SessionManager:
    @staticmethod
    def initialize_user(user_email: str):
        """Initialize user-related session state"""
        UserManager.initialize_user(user_email)
    
    @staticmethod
    def initialize_course(course_code: str):
        """Initialize course-related session state"""
        return CourseManager.initialize_course(course_code)
    
    @staticmethod
    def initialize_section(unit_id: str, section_id: str):
        """Initialize section-related session state"""
        return CourseManager.initialize_section(st.session_state.course_code, unit_id, section_id)
    
    @staticmethod
    def set_unit_context(unit: Unit):
        """Set unit-related session state"""
        st.session_state.update({
            'unit_id': unit.id,
            'unit_title': unit.title
        })

    @staticmethod
    def get_section(unit_id: str, section_id: str):
        """Get a section by course code, unit ID, and section ID"""
        return CourseManager.get_section(st.session_state.course_code, unit_id, section_id)
    
    @staticmethod
    def set_section_context(section: Section):
        """Set section-related session state"""
        st.session_state.update({
            'section_id': section.id,
            'section_title': section.title,
            'section_overview': section.overview,
            'section_content': section.content,
            'section_file_path': section.file_path,
            'section_type': section.section_type,
            'assistant_instructions': section.assistant_instructions,
            'pdf_content': get_file_content(section.file_path) if section.section_type == 'file' else None
        })
    
    @staticmethod
    def clear_section_context():
        """Clear section-related session state"""
        keys_to_remove = [
            'section_id', 'section_title', 'section_overview',
            'section_content', 'section_file_path', 'section_type',
            'assistant_instructions', 'pdf_content'
        ]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def clear_unit_context():
        """Clear unit-related session state"""
        keys_to_remove = ['unit_id', 'unit_title']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def clear_course_context():
        """Clear course-related session state"""
        keys_to_remove = [
            'course_code', 'course_name', 'course_description',
            'grade_level', 'course_units'
        ]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def clear_user_context():
        """Clear user-related session state"""
        UserManager.reset_user()

    @staticmethod
    def check_state(check_user=False, reset_chat=False, user_reset=False):
        """Check and initialize session state"""
        if "authentication_status" not in st.session_state:
            st.session_state['authentication_status'] = False
        
        if "role" not in st.session_state:
            st.session_state['role'] = 'student'

        if user_reset:
            SessionManager.clear_user_context()
        
        # Load styling
        load_style()
        
        # Check if user is on mobile
        on_mobile()

        # Reset info
        if reset_chat:
            SessionManager.reset_chatbot()

        # Start periodic cleanup only once per session
        if "cleanup_initialized" not in st.session_state:
            # Initialize memory and heartbeat managers
            initialize_memory_and_heartbeat()

        # Update activity on any user interaction
        update_session_activity()
        
        # Check if user is signed in
        if check_user:
            if not st.session_state.authentication_status:
                st.switch_page("app.py")

    @staticmethod
    def reset_chatbot():
        """Reset chatbot-related session state"""
        st.session_state['messages'] = []
        st.session_state['drop_file'] = False
        st.session_state['math_attachments'] = []
        st.session_state['model_loaded'] = False