import os
import tempfile
import zipfile
from utils.data.aws import get_course_details, get_course_units, get_unit_sections, s3, bucket_name
from utils.documents.docx import markdownToWordFromString
from utils.core.logger import logger

def export_course(course_code, course_name):
    """
    Export a course's content to a zip file containing text files for each section,
    organized in folders by unit. For file-based sections, includes the PDF files.
    
    Args:
        course_code (str): The course code to export
        course_name (str): The course name to include in the course info file
        
    Returns:
        str: The path to the created zip file
    """
    # Create a temporary file for the zip
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    temp_zip.close()  # Close the file handle before using it with ZipFile
    
    try:
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            # Get course details
            course_details = get_course_details(course_code)
            course_metadata = next((item for item in course_details if item['SK'] == 'METADATA'), None)
            
            if not course_metadata:
                raise Exception("Course metadata not found")
            
            # Create course info file
            course_info = f"""Course: {course_name}
Code: {course_code}
Grade Level: {course_metadata.get('grade_level', '')}
Description: {course_metadata.get('description', '')}

"""
            zip_file.writestr('course_info.txt', course_info)
            
            # Get all units
            units = get_course_units(course_code)
            if units:
                # Sort units by order
                units.sort(key=lambda x: x.get('order', 0))
                
                # Create units info file
                units_info = "Units:\n"
                for i, unit in enumerate(units, 1):
                    units_info += f"\n{i}. {unit.get('title', '')}\n"
                    units_info += f"   {unit.get('description', '')}\n"
                zip_file.writestr('units_info.txt', units_info)
                
                # Process each unit
                for unit in units:
                    unit_id = unit['SK'].replace('UNIT#', '')
                    unit_title = unit.get('title', '')
                    
                    # Create unit directory
                    unit_dir = f"Unit_{unit_id}_{unit_title.replace(' ', '_')}"
                    
                    # Create unit info file
                    unit_content = f"""Unit: {unit_title}
Description: {unit.get('description', '')}

"""
                    
                    # Get all sections for this unit
                    sections = get_unit_sections(course_code, unit_id)
                    if sections:
                        # Sort sections by order
                        sections.sort(key=lambda x: x.get('order', 0))
                        
                        # Add sections list to unit info
                        unit_content += "Sections:\n"
                        for i, section in enumerate(sections, 1):
                            unit_content += f"\n{i}. {section.get('title', '')}\n"
                            unit_content += f"   {section.get('overview', '')}\n"
                            if section.get('section_type') == 'file':
                                unit_content += f"   [File-based section]\n"
                    
                    zip_file.writestr(f'{unit_dir}/unit_info.txt', unit_content)                    
                    # Process each section
                    if sections:
                        for section in sections:
                            section_title = section.get('title', '')
                            section_type = section.get('section_type', 'content')
                            
                            # Create section file name (sanitized)
                            section_filename = f"{section_title.replace(' ', '_')}"                            
                            if section_type == 'file':
                                # For file-based sections, download the PDF from S3
                                file_path = section.get('file_path')
                                if file_path:
                                    try:
                                        # Extract the key from the URL if it's a full URL
                                        if file_path.startswith('http'):
                                            # Remove the bucket name and domain from the URL
                                            key = file_path.split(f'{bucket_name}.s3.amazonaws.com/')[-1]
                                        else:
                                            key = file_path
                                            
                                        response = s3.get_object(Bucket=bucket_name, Key=key)
                                        pdf_content = response['Body'].read()
                                        zip_path = f'{unit_dir}/{section_filename}.pdf'
                                        zip_file.writestr(zip_path, pdf_content)
                                    except Exception as e:
                                        logger.error(f"Error processing PDF for {section_title}")
                            else:
                                # For content-based sections, add text and docx files
                                section_content = section.get('content', '')
                                
                                # Add text file
                                txt_path = f'{unit_dir}/{section_filename}.txt'
                                zip_file.writestr(txt_path, section_content)
                                
                                # Create Word document
                                try:
                                    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
                                        markdownToWordFromString(section_content, temp_docx.name)
                                        with open(temp_docx.name, 'rb') as docx_file:
                                            docx_path = f'{unit_dir}/{section_filename}.docx'
                                            zip_file.writestr(docx_path, docx_file.read())
                                    os.unlink(temp_docx.name)
                                except Exception as e:
                                    logger.error(f"Error converting {section_title} to Word")
        
        return temp_zip.name
    except Exception as e:
        # Clean up the temporary file if something goes wrong
        if os.path.exists(temp_zip.name):
            os.unlink(temp_zip.name)
        raise e 