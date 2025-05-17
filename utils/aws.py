import boto3
import datetime
from botocore.exceptions import ClientError
import re
from utils.logger import logger
import io
from utils.config import open_config
import uuid

# Initialize clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
course_table = dynamodb.Table('playlab-courses')
bucket_name = 'playlab-courses-content'

def validate_course_code(code: str) -> bool:
    """
    Validate the course code format.
    Only allows lowercase letters, numbers, and hyphens.
    Must start with a letter and be between 3-20 characters.
    Must not already be in use.
    """
    if not code:
        return False
    pattern = r'^[a-z][a-z0-9-]{2,19}$'
    valid_format = bool(re.match(pattern, code))
    if not valid_format:
        return 'Invalid'
    # Check if course code is already in use
    elif course_code_exists(code):
        return 'In Use'
    else:
        return 'Good to Go'

# User operations
def get_user_courses(email):
    """
    Retrieve all courses for a specific user
    """
    response = course_table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
        ExpressionAttributeValues={
            ':pk': f'USER#{email}',
            ':sk_prefix': 'COURSE#'
        }
    )
    return response.get('Items', [])

# Course operations
def create_course(email, course_code, name, description, grade):
    """
    Create a new course for a user
    Stores both the user-course relationship and the course metadata
    """
    
    # Create course entry under user
    user_course_item = {
        'PK': f'USER#{email}',
        'SK': f'COURSE#{course_code}',
        'name': name,
        'description': description,
        'grade_level': grade,
        'created_at': str(datetime.datetime.now()),
        'GSI1PK': 'ALLCOURSES',
        'GSI1SK': f'COURSE#{course_code}'
    }
    course_table.put_item(Item=user_course_item)
    
    # Create course metadata
    metadata_item = {
        'PK': f'COURSE#{course_code}',
        'SK': 'METADATA',
        'name': name,
        'description': description,
        'created_by': email,
        'grade_level': grade,
        'created_at': str(datetime.datetime.now())
    }
    course_table.put_item(Item=metadata_item)
    
    return True

def delete_course(email, course_code):
    """
    Delete a course and all its associated data
    """
    try:
        # Get all items related to the course
        course_items = get_course_details(course_code)
        
        # Delete all course-related items
        for item in course_items:
            course_table.delete_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                }
            )
        
        # Delete the user-course relationship
        course_table.delete_item(
            Key={
                'PK': f'USER#{email}',
                'SK': f'COURSE#{course_code}'
            }
        )
        
        # Delete any associated S3 content
        try:
            # List all objects with the course prefix
            objects = s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=f'{course_code}/'
            ).get('Contents', [])
            
            # Only attempt deletion if there are objects
            if objects:
                s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={
                        'Objects': [
                            {'Key': obj['Key']} for obj in objects
                        ]
                    }
                )
        except ClientError as e:
            logger.error(f"Error deleting S3 objects: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error deleting course: {e}")
        return False

def get_course_details(course_code):
    """
    Get all information related to a course including units and sections
    """
    response = course_table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={
            ':pk': f'COURSE#{course_code}'
        }
    )
    items = response.get('Items', [])
    return items

def get_all_courses():
    """
    Get all courses across all users (for admin purposes)
    """
    response = course_table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :pk',
        ExpressionAttributeValues={
            ':pk': 'ALLCOURSES'
        }
    )
    return response.get('Items', [])

def course_code_exists(course_code):
    """
    Check if a course code exists for any user
    Returns True if the course code exists, False otherwise
    """
    response = course_table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :pk AND GSI1SK = :sk',
        ExpressionAttributeValues={
            ':pk': 'ALLCOURSES',
            ':sk': f'COURSE#{course_code}'
        }
    )
    return len(response.get('Items', [])) > 0

# Unit operations
def create_unit(course_code, unit_id, title, description, order):
    """
    Create a new unit for a course
    """
    course_table.put_item(
        Item={
            'PK': f'COURSE#{course_code}',
            'SK': f'UNIT#{unit_id}',
            'title': title,
            'description': description,
            'order': order
        }
    )
    return True

def get_course_units(course_code):
    """
    Get all units for a specific course
    """
    response = course_table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
        ExpressionAttributeValues={
            ':pk': f'COURSE#{course_code}',
            ':sk_prefix': 'UNIT#'
        }
    )
    return response.get('Items', [])

def update_unit(course_code, unit_id, title, description):
    """
    Update an existing unit's details
    """
    try:
        course_table.update_item(
            Key={
                'PK': f'COURSE#{course_code}',
                'SK': f'UNIT#{unit_id}'
            },
            UpdateExpression='SET title = :title, description = :desc',
            ExpressionAttributeValues={
                ':title': title,
                ':desc': description
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error updating unit: {e}")
        return False

# Section operations
def create_section(course_code, unit_id, section_id, title, overview, order, section_type="content", file_path=None, content=None):
    """
    Create a new section within a unit
    Args:
        course_code: The course code
        unit_id: The unit ID
        section_id: The section ID
        title: Section title
        overview: Section overview
        order: Section order
        section_type: Type of section ("file" or "content")
        file_path: S3 file path for file-based sections
        content: Content for AI-generated sections
    """
    item = {
        'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
        'SK': f'SECTION#{section_id}',
        'title': title,
        'overview': overview,
        'order': order,
        'section_type': section_type
    }
    
    if section_type == "file" and file_path:
        item['file_path'] = file_path
    elif section_type == "content" and content:
        item['content'] = content
        
    course_table.put_item(Item=item)
    return True

def get_unit_sections(course_code, unit_id):
    """
    Get all sections for a specific unit
    """
    response = course_table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
        ExpressionAttributeValues={
            ':pk': f'COURSE#{course_code}#UNIT#{unit_id}',
            ':sk_prefix': 'SECTION#'
        }
    )
    return response.get('Items', [])

def delete_section(course_code, unit_id, section_id):
    """
    Delete a section from a unit
    """
    try:
        # Get the section to check if it's a file-based section
        response = course_table.get_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'SECTION#{section_id}'
            }
        )
        section = response.get('Item')
        
        if section and section.get('section_type') == 'file' and section.get('file_path'):
            # Delete the file from S3
            try:
                s3.delete_object(
                    Bucket=bucket_name,
                    Key=section['file_path']
                )
            except ClientError as e:
                logger.error(f"Error deleting S3 file: {e}")
        
        # Delete the section from DynamoDB
        course_table.delete_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'SECTION#{section_id}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting section: {e}")
        return False

def update_section(course_code, unit_id, section_id, title=None, overview=None, content=None, section_type=None, file_path=None):
    """
    Update an existing section's details
    """
    try:
        # Build update expression and attribute values
        update_expr_parts = []
        expr_attr_values = {}
        
        if title is not None:
            update_expr_parts.append('title = :title')
            expr_attr_values[':title'] = title
            
        if overview is not None:
            update_expr_parts.append('overview = :overview')
            expr_attr_values[':overview'] = overview
            
        if content is not None:
            update_expr_parts.append('content = :content')
            expr_attr_values[':content'] = content
            
        if section_type is not None:
            update_expr_parts.append('section_type = :section_type')
            expr_attr_values[':section_type'] = section_type
            
        if file_path is not None:
            update_expr_parts.append('file_path = :file_path')
            expr_attr_values[':file_path'] = file_path
        
        if not update_expr_parts:
            return True  # Nothing to update
            
        update_expression = 'SET ' + ', '.join(update_expr_parts)
        
        course_table.update_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'SECTION#{section_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_attr_values
        )
        return True
    except Exception as e:
        logger.error(f"Error updating section: {e}")
        return False

def update_section_orders(course_code, unit_id, section_orders):
    """
    Update the order of multiple sections within a unit
    Args:
        course_code: The course code
        unit_id: The unit ID
        section_orders: List of (section_id, new_order) tuples
    """
    try:
        with course_table.batch_writer() as batch:
            for section_id, new_order in section_orders:
                batch.put_item(
                    Item={
                        'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                        'SK': f'SECTION#{section_id}',
                        'order': new_order
                    }
                )
        return True
    except Exception as e:
        logger.error(f"Error updating section orders: {e}")
        return False

# S3 operations
def upload_content_file(file_data, course_code, file_name):
    """
    Upload a file to S3 bucket and return the URL
    """
    key = f'{course_code}/{file_name}'
    try:
        s3.upload_fileobj(file_data, bucket_name, key)
        return f'https://{bucket_name}.s3.amazonaws.com/{key}'
    except ClientError as e:
        logger.error(f"Error uploading file: {e}")
        return None

def delete_content_file(course_code, file_name):
    """
    Delete a file from S3 bucket
    """
    key = f'{course_code}/{file_name}'
    try:
        s3.delete_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError as e:
        logger.error(f"Error deleting file: {e}")
        return False

def update_course(email, course_code, name, description, grade):
    """
    Update an existing course's details
    """
    try:
        # Update course entry under user
        course_table.update_item(
            Key={
                'PK': f'USER#{email}',
                'SK': f'COURSE#{course_code}'
            },
            UpdateExpression='SET #name = :name, #desc = :desc, grade_level = :grade',
            ExpressionAttributeNames={
                '#name': 'name',
                '#desc': 'description'
            },
            ExpressionAttributeValues={
                ':name': name,
                ':desc': description,
                ':grade': grade
            }
        )
        
        # Update course metadata
        course_table.update_item(
            Key={
                'PK': f'COURSE#{course_code}',
                'SK': 'METADATA'
            },
            UpdateExpression='SET #name = :name, #desc = :desc, grade_level = :grade',
            ExpressionAttributeNames={
                '#name': 'name',
                '#desc': 'description'
            },
            ExpressionAttributeValues={
                ':name': name,
                ':desc': description,
                ':grade': grade
            }
        )
        
        return True
    except Exception as e:
        logger.error(f"Error updating course: {e}")
        return False

def delete_unit(course_code, unit_id):
    """
    Delete a unit and all its associated sections
    """
    try:
        # First, get all sections for this unit
        sections = get_unit_sections(course_code, unit_id)
        
        # Delete all sections
        for section in sections:
            delete_section(course_code, unit_id, section['SK'].replace('SECTION#', ''))
        
        # Delete the unit itself
        course_table.delete_item(
            Key={
                'PK': f'COURSE#{course_code}',
                'SK': f'UNIT#{unit_id}'
            }
        )
        
        return True
    except Exception as e:
        logger.error(f"Error deleting unit: {e}")
        return False

def delete_section(course_code, unit_id, section_id):
    """
    Delete a single section from a unit
    """
    try:
        # Get section details first
        response = course_table.get_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'SECTION#{section_id}'
            }
        )
        section = response.get('Item', {})
        
        # If it's a file-based section, delete the file from S3
        if section.get('section_type') == 'file':
            file_path = section.get('file_path')
            if file_path:
                # Extract filename from path
                file_name = file_path.split('/')[-1]
                delete_content_file(course_code, file_name)
        
        # Delete the section from DynamoDB
        course_table.delete_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'SECTION#{section_id}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting section: {e}")
        return False

def update_section(course_code, unit_id, section_id, title=None, overview=None, content=None, section_type=None, file_path=None):
    """
    Update a section's details
    Args:
        course_code: The course code
        unit_id: The unit ID
        section_id: The section ID
        title: Optional section title
        overview: Optional section overview
        content: Optional section content as a string (markdown)
        section_type: Optional section type ("file" or "content")
        file_path: Optional S3 file path for file-based sections
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get current section details
        response = course_table.get_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'SECTION#{section_id}'
            }
        )
        current_section = response.get('Item', {})
        
        # Build update expression and values
        update_parts = []
        expr_values = {}
        
        # Add title update if provided
        if title is not None:
            update_parts.append('title = :title')
            expr_values[':title'] = title
        else:
            title = current_section.get('title', '')
        
        # Add overview update if provided
        if overview is not None:
            update_parts.append('overview = :overview')
            expr_values[':overview'] = overview
        else:
            overview = current_section.get('overview', '')
        
        # Add section type update if provided
        if section_type is not None:
            update_parts.append('section_type = :section_type')
            expr_values[':section_type'] = section_type
            
            # If changing to file type, update file path
            if section_type == "file" and file_path:
                update_parts.append('file_path = :file_path')
                expr_values[':file_path'] = file_path
                # Remove content if it exists
                update_parts.append('content = :empty')
                expr_values[':empty'] = None
            # If changing to content type, update content
            elif section_type == "content" and content:
                update_parts.append('content = :content')
                expr_values[':content'] = content
                # Remove file path if it exists
                update_parts.append('file_path = :empty')
                expr_values[':empty'] = None
        
        # Add content update if provided (only for content-type sections)
        elif content is not None and current_section.get('section_type') == "content":
            update_parts.append('content = :content')
            expr_values[':content'] = content
        
        # Add file path update if provided (only for file-type sections)
        elif file_path is not None and current_section.get('section_type') == "file":
            update_parts.append('file_path = :file_path')
            expr_values[':file_path'] = file_path
        
        # Only update if there are changes
        if update_parts:
            update_expr = 'SET ' + ', '.join(update_parts)
            
            # Update the section
            course_table.update_item(
                Key={
                    'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                    'SK': f'SECTION#{section_id}'
                },
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
        
        return True
    except Exception as e:
        logger.error(f"Error updating section: {e}")
        return False

def update_unit_orders(course_code, unit_orders):
    """
    Update the order of multiple units
    Args:
        course_code: The course code
        unit_orders: List of tuples (unit_id, new_order)
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        for unit_id, new_order in unit_orders:
            course_table.update_item(
                Key={
                    'PK': f'COURSE#{course_code}',
                    'SK': f'UNIT#{unit_id}'
                },
                UpdateExpression='SET #order = :order',
                ExpressionAttributeNames={
                    '#order': 'order'
                },
                ExpressionAttributeValues={
                    ':order': new_order
                }
            )
        return True
    except Exception as e:
        logger.error(f"Error updating unit orders: {e}")
        return False

def copy_course_contents(source_course_code, target_course_code):
    """
    Copy all units and sections from source course to target course, including content and files
    """
    try:
        # Get all units from source course
        source_units = get_course_units(source_course_code)
        
        # For each unit, copy it and its sections
        for unit in source_units:
            unit_id = unit['SK'].replace('UNIT#', '')
            
            # Create the unit in target course
            create_unit(
                course_code=target_course_code,
                unit_id=unit_id,
                title=unit['title'],
                description=unit.get('description', ''),
                order=unit['order']
            )
            
            # Get all sections for this unit
            sections = get_unit_sections(source_course_code, unit_id)
            
            # Copy each section
            for section in sections:
                section_id = section['SK'].replace('SECTION#', '')
                section_type = section.get('section_type', 'content')
                
                if section_type == 'file':
                    # For file-based sections, copy the file to the new course
                    file_path = section.get('file_path')
                    if file_path:
                        try:
                            # Get file content using the helper function
                            file_data = get_file_content(file_path)
                            if file_data is None:
                                raise Exception("Could not retrieve file content")
                            
                            # Extract filename from the file path
                            file_name = file_path.split('/')[-1]
                            
                            # Create a file-like object from the bytes
                            file_obj = io.BytesIO(file_data)
                            
                            # Upload to target course with same filename
                            target_key = f'{target_course_code}/{file_name}'
                            s3.upload_fileobj(
                                file_obj,
                                bucket_name,
                                target_key
                            )
                            
                            # Create section with new file path
                            create_section(
                                course_code=target_course_code,
                                unit_id=unit_id,
                                section_id=section_id,
                                title=section['title'],
                                overview=section.get('overview', ''),
                                order=section['order'],
                                section_type='file',
                                file_path=target_key
                            )
                        except Exception as e:
                            logger.error(f"Error copying file for section {section_id}: {e}")
                            # Create section without file if copy fails
                            create_section(
                                course_code=target_course_code,
                                unit_id=unit_id,
                                section_id=section_id,
                                title=section['title'],
                                overview=section.get('overview', ''),
                                order=section['order'],
                                section_type='content',
                                content=f"Error: Could not copy original file content. {str(e)}"
                            )
                else:
                    # For content-based sections, copy the content
                    create_section(
                        course_code=target_course_code,
                        unit_id=unit_id,
                        section_id=section_id,
                        title=section['title'],
                        overview=section.get('overview', ''),
                        order=section['order'],
                        section_type='content',
                        content=section.get('content', '')
                    )
        
        return True
    except Exception as e:
        logger.error(f"Error copying course contents: {e}")
        return False

def update_section_orders(course_code, unit_id, section_orders):
    """
    Update the order of multiple sections within a unit
    Args:
        course_code: The course code
        unit_id: The unit ID
        section_orders: List of tuples (section_id, new_order)
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        for section_id, new_order in section_orders:
            course_table.update_item(
                Key={
                    'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                    'SK': f'SECTION#{section_id}'
                },
                UpdateExpression='SET #order = :order',
                ExpressionAttributeNames={
                    '#order': 'order'
                },
                ExpressionAttributeValues={
                    ':order': new_order
                }
            )
        return True
    except Exception as e:
        logger.error(f"Error updating section orders: {e}")
        return False

def get_file_content(file_path):
    """
    Retrieve file content from S3
    Args:
        file_path: The S3 file path (can be full URL or just the key)
    Returns:
        The file content as bytes, or None if the file doesn't exist
    """
    try:
        # Extract the key from the URL if it's a full URL
        if file_path.startswith('http'):
            # Remove the bucket name and domain from the URL
            key = file_path.split(f'{bucket_name}.s3.amazonaws.com/')[-1]
        else:
            key = file_path

        response = s3.get_object(
            Bucket=bucket_name,
            Key=key
        )
        return response['Body'].read()
    except ClientError as e:
        logger.error(f"Error retrieving file content: {e}")
        return None

def create_custom_assistant(course_code, name, instructions):
    """
    Create a new custom AI assistant for a course
    """
    try:
        # Generate a unique identifier for the assistant
        assistant_id = str(uuid.uuid4())
        course_table.put_item(
            Item={
                'PK': f'COURSE#{course_code}',
                'SK': f'ASSISTANT#{assistant_id}',
                'assistant_id': assistant_id,
                'name': name,
                'instructions': instructions,
                'created_at': str(datetime.datetime.now())
            }
        )
        return assistant_id
    except Exception as e:
        logger.error(f"Error creating custom assistant: {e}")
        return None

def get_custom_assistants(course_code):
    """
    Get all custom AI assistants for a course
    """
    try:
        response = course_table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'COURSE#{course_code}',
                ':sk_prefix': 'ASSISTANT#'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting custom assistants: {e}")
        return []

def delete_custom_assistant(course_code, assistant_id):
    """
    Delete a custom AI assistant from a course
    """
    try:
        course_table.delete_item(
            Key={
                'PK': f'COURSE#{course_code}',
                'SK': f'ASSISTANT#{assistant_id}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting custom assistant: {e}")
        return False

def update_section_assistant(course_code, unit_id, section_id, assistant_id):
    """
    Update the AI assistant for a section
    """
    try:
        # Get the instructions based on the assistant ID
        if assistant_id == "None":
            instructions = None
        elif assistant_id == "Default":
            instructions = open_config()['playlab']['student_assistant_default_system_prompt']
        else:
            # Get instructions from custom assistant
            custom_assistants = get_custom_assistants(course_code)
            for assistant in custom_assistants:
                if assistant['assistant_id'] == assistant_id:
                    instructions = assistant['instructions']
                    break
            else:
                # If custom assistant not found, fall back to default
                instructions = open_config()['playlab']['student_assistant_default_system_prompt']

        course_table.update_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'SECTION#{section_id}'
            },
            UpdateExpression='SET assistant_id = :assistant_id',
            ExpressionAttributeValues={
                ':assistant_id': assistant_id
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error updating section assistant: {e}")
        return False 