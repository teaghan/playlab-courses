from dataclasses import dataclass
from typing import List, Optional
import streamlit as st
from utils.data.aws import get_course_details, get_course_units, get_unit_sections, course_table, get_custom_assistants, get_section_location, get_file_content, get_open_courses
from utils.core.config import open_config

@dataclass
class Section:
    id: str
    title: str
    overview: str
    content: Optional[str]
    file_path: Optional[str]
    section_type: str
    order: int
    unit_id: str
    unit_title: str
    assistant_id: Optional[str] = None
    assistant_name: Optional[str] = None
    assistant_instructions: Optional[str] = None

@dataclass
class SectionSmall:
    id: str
    title: str
    section_type: str
    unit_id: str
    unit_title: str

@dataclass
class SectionSummary:
    id: str
    title: str
    overview: str
    order: int
    section_type: str
    unit_id: str
    unit_title: str

@dataclass
class Unit:
    id: str
    title: str
    description: str
    order: int
    sections: List[Section]

@dataclass
class Course:
    code: str
    name: str
    description: str
    grade_level: int
    availability: str
    units: List[Unit]

class CourseManager:
    
    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_course(course_code: str) -> Course:
        """Get complete course structure with caching"""
        # Get course details
        course_details = get_course_details(course_code)
        metadata = next((item for item in course_details if item["SK"] == "METADATA"), None)
        
        if not metadata:
            return None
            
        # Get units
        units_data = get_course_units(course_code)
        units_data.sort(key=lambda x: x.get('order', 0))
        
        units = []
        for unit_data in units_data:
            unit_id = unit_data['SK'].replace('UNIT#', '')
            
            # Get sections for this unit
            sections_data = get_unit_sections(course_code, unit_id)
            sections_data.sort(key=lambda x: x.get('order', 0))
            
            sections = []
            for section_data in sections_data:
                section_id = section_data['SK'].replace('SECTION#', '')
                section = SectionSummary(
                    id=section_id,
                    title=section_data.get('title', ''),
                    overview=section_data.get('overview', ''),
                    order=section_data.get('order', 0),
                    section_type=section_data.get('section_type', 'content'),
                    unit_id=unit_id,
                    unit_title=unit_data.get('title', '')
                )
                sections.append(section)
            
            unit = Unit(
                id=unit_id,
                title=unit_data.get('title', ''),
                description=unit_data.get('description', ''),
                order=unit_data.get('order', 0),
                sections=sections
            )
            units.append(unit)
        
        return Course(
            code=course_code,
            name=metadata.get('name', ''),
            description=metadata.get('description', ''),
            grade_level=metadata.get('grade_level', 6),
            availability=metadata.get('availability', 'requires_code'),
            units=units
        )
    
    @staticmethod
    def initialize_course(course_code: str):
        """Initialize course-related session state"""
        course = CourseManager.get_course(course_code)
        if course:
            st.session_state.update({
                'course_code': course.code,
                'course_name': course.name,
                'course_description': course.description,
                'grade_level': course.grade_level,
                'course_availability': course.availability,
                'course_units': course.units
            })
            return True
        else:
            return False
    
    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_section(course_code: str, unit_id: str, section_id: str) -> Optional[Section]:
        """
        Get a specific section by course code, unit ID, and section ID.
        Results are cached for 1 hour.
        """
        # Get section details from AWS
        response = course_table.get_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'SECTION#{section_id}'
            }
        )
        
        section_data = response.get('Item')
        if not section_data:
            return None
            
        # Get assistant details if present
        assistant_id = section_data.get('assistant_id')
        assistant_name = None
        assistant_instructions = None
        if assistant_id:
            if 'default' in assistant_id.lower():
                assistant_instructions = open_config()['playlab']['student_assistant_default_system_prompt']
                assistant_name = 'Default'
            else:
                # Get assistant details from custom assistants
                custom_assistants = get_custom_assistants(course_code)
                for assistant in custom_assistants:
                    if assistant['assistant_id'] == assistant_id:
                        assistant_name = assistant.get('name')
                        assistant_instructions = assistant.get('instructions')
                        break
        
        # Create and return Section object
        # Get unit title from course units in session state if available
        unit_title = ''
        if 'course_units' in st.session_state:
            for unit in st.session_state.course_units:
                if unit.id == unit_id:
                    unit_title = unit.title
                    break

        return Section(
            id=section_id,
            title=section_data.get('title', ''),
            overview=section_data.get('overview', ''),
            content=section_data.get('content'),
            file_path=section_data.get('file_path'),
            section_type=section_data.get('section_type', 'content'),
            order=section_data.get('order', 0),
            assistant_id=assistant_id,
            assistant_name=assistant_name,
            assistant_instructions=assistant_instructions,
            unit_id=unit_id,
            unit_title=unit_title
        )
    
    def initialize_section(course_code: str, unit_id: str, section_id: str):
        """Initialize section-related session state"""
        section = CourseManager.get_section(course_code, unit_id, section_id)
        if section:
            st.session_state.section = section
            return True
        else:
            return False
        
    @staticmethod
    def initialize_section_from_id(section_id: str):
        course_code, unit_id = get_section_location(section_id)
        if CourseManager.initialize_course(course_code):
            if CourseManager.initialize_section(course_code, unit_id, section_id):
                if st.session_state.section.section_type == 'file':
                    st.session_state['pdf_content'] = get_file_content(st.session_state.section.file_path)
                else:
                    st.session_state['pdf_content'] = '' 
                return True
        return False
    
    
    @staticmethod
    def clear_cache():
        """Clear the course cache"""
        st.cache_data.clear()

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_open_courses() -> List[Course]:
        """
        Get all courses that are marked as 'open_to_all'
        Returns a list of Course dataclass objects
        """
        # Get all open courses from AWS
        open_course_data = get_open_courses()
        
        # Convert each course to a Course dataclass
        courses = []
        for course_data in open_course_data:
            course_code = course_data['SK'].replace('COURSE#', '')
            # Use existing get_course method to get full course structure
            course = CourseManager.get_course(course_code)
            if course:
                courses.append(course)
        
        return courses