from dataclasses import dataclass
from typing import List
import streamlit as st
from utils.data.aws import get_user_courses
from utils.data.course_manager import CourseManager, Course
import re

@dataclass
class User:
    user_email: str
    role: str
    user_courses: List[Course]
    is_mobile: bool
    authentication_status: bool

class UserManager:
    @staticmethod
    def initialize_user(user_email: str):
        """Initialize user-related session state"""
        st.session_state.update({
            'authentication_status': True,
            'user_email': user_email,
            'role': 'teacher',
            'user_courses': []
        })
        UserManager.collect_user_courses()

    @staticmethod
    def collect_user_courses():
        """Collect and store user's courses in session state"""
        course_codes = get_user_courses(st.session_state.user_email)
        st.session_state.user_courses = [CourseManager.get_course(course_code) for course_code in course_codes]

    @staticmethod
    def reset_user():
        """Reset user-related session state"""
        st.session_state.update({
            'authentication_status': False,
            'user_email': None,
            'role': 'student',
            'user_courses': [],
        })


def is_valid_email(email: str) -> bool:
    """
    Validate an email address using a robust regex pattern based on RFC 5322.
    
    Args:
        email (str): The email address string to validate.
    
    Returns:
        bool: True if the email is valid according to the regex; False otherwise.
    """
    # This regex covers a wide range of valid email formats
    email_regex = re.compile(
        r"(?:[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"
        r'|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]'
        r'|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")'
        r'@(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?'
        r'|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|'
        r'[a-zA-Z0-9-]*[a-zA-Z0-9]:'
        r'(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]'
        r'|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'
    )
    # Using fullmatch ensures the entire string conforms to the pattern.
    return re.fullmatch(email_regex, email) is not None