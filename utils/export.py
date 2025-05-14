import os
import tempfile
import zipfile
from utils.aws import get_course_details, get_course_units, get_unit_lessons, s3, bucket_name
from utils.docx import markdownToWordFromString

def export_course(course_code):
    """
    Export a course's content to a zip file containing text files for each lesson,
    organized in folders by unit. For file-based lessons, includes the PDF files.
    
    Args:
        course_code (str): The course code to export
        
    Returns:
        bytes: The zip file contents as bytes
    """
    # Create a temporary directory to store the files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Get course details
        course_details = get_course_details(course_code)
        if not course_details:
            raise ValueError("Course not found")
            
        # Get course metadata
        metadata = next((item for item in course_details if item["SK"] == "METADATA"), None)
        if not metadata:
            raise ValueError("Course metadata not found")
            
        # Create a zip file in memory
        zip_buffer = tempfile.SpooledTemporaryFile()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add course metadata
            metadata_content = f"Course Name: {metadata.get('name', '')}\n"
            metadata_content += f"Description: {metadata.get('description', '')}\n"
            metadata_content += f"Grade Level: {metadata.get('grade_level', '')}\n"
            
            zip_file.writestr('course_info.txt', metadata_content)
            
            # Get all units
            units = get_course_units(course_code)
            if units:
                # Sort units by order
                units.sort(key=lambda x: x.get('order', 0))
                
                # Process each unit
                for unit in units:
                    unit_id = unit['SK'].replace('UNIT#', '')
                    unit_title = unit.get('title', '')
                    
                    # Create unit directory name (sanitized)
                    unit_dir = f"Unit_{unit_id}_{unit_title.replace(' ', '_')}"
                    
                    # Add unit info
                    unit_content = f"Unit Title: {unit_title}\n"
                    unit_content += f"Description: {unit.get('description', '')}\n\n"
                    
                    # Get all lessons for this unit
                    lessons = get_unit_lessons(course_code, unit_id)
                    if lessons:
                        # Sort lessons by order
                        lessons.sort(key=lambda x: x.get('order', 0))
                        
                        # Add lessons list to unit info
                        unit_content += "Lessons:\n"
                        for i, lesson in enumerate(lessons, 1):
                            unit_content += f"\n{i}. {lesson.get('title', '')}\n"
                            unit_content += f"   {lesson.get('overview', '')}\n"
                            if lesson.get('lesson_type') == 'file':
                                unit_content += f"   [File-based lesson]\n"
                    
                    zip_file.writestr(f'{unit_dir}/unit_info.txt', unit_content)
                    
                    # Process each lesson
                    if lessons:
                        for lesson in lessons:
                            lesson_title = lesson.get('title', '')
                            lesson_type = lesson.get('lesson_type', 'content')
                            
                            # Create lesson file name (sanitized)
                            lesson_filename = f"{lesson_title.replace(' ', '_')}"
                            
                            if lesson_type == 'file':
                                # For file-based lessons, download the PDF from S3
                                file_path = lesson.get('file_path')
                                if file_path:
                                    try:
                                        # Extract the key from the S3 URL
                                        key = file_path.split(f'https://{bucket_name}.s3.amazonaws.com/')[-1]
                                        
                                        # Download the file from S3
                                        response = s3.get_object(Bucket=bucket_name, Key=key)
                                        pdf_content = response['Body'].read()
                                        
                                        # Add PDF to zip
                                        zip_file.writestr(f'{unit_dir}/{lesson_filename}.pdf', pdf_content)
                                    except Exception as e:
                                        print(f"Error processing PDF for {lesson_title}: {str(e)}")
                            else:
                                # For content-based lessons, add text and docx files
                                lesson_content = lesson.get('content', '')
                                
                                # Add markdown file to zip
                                zip_file.writestr(f'{unit_dir}/{lesson_filename}.txt', lesson_content)
                                
                                # Convert markdown to Word document
                                try:
                                    # Create a temporary file for the Word document
                                    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
                                        # Convert markdown to Word
                                        markdownToWordFromString(lesson_content, temp_docx.name)
                                        
                                        # Read the Word document and add it to the zip
                                        with open(temp_docx.name, 'rb') as docx_file:
                                            zip_file.writestr(f'{unit_dir}/{lesson_filename}.docx', docx_file.read())
                                            
                                    # Clean up the temporary file
                                    os.unlink(temp_docx.name)
                                except Exception as e:
                                    print(f"Error converting {lesson_title} to Word: {str(e)}")
        
        # Reset buffer position and read contents
        zip_buffer.seek(0)
        return zip_buffer.read() 