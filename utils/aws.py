import boto3
import datetime
from botocore.exceptions import ClientError
import re
from utils.logger import logger

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
            s3.delete_objects(
                Bucket=bucket_name,
                Delete={
                    'Objects': [
                        {'Key': f'{course_code}/{key}'} 
                        for key in s3.list_objects_v2(
                            Bucket=bucket_name,
                            Prefix=f'{course_code}/'
                        ).get('Contents', [])
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
    Get all information related to a course including units and lessons
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

# Lesson operations
def create_lesson(course_code, unit_id, lesson_id, title, overview, order, lesson_type="content", file_path=None, content=None):
    """
    Create a new lesson within a unit
    Args:
        course_code: The course code
        unit_id: The unit ID
        lesson_id: The lesson ID
        title: Lesson title
        overview: Lesson overview
        order: Lesson order
        lesson_type: Type of lesson ("file" or "content")
        file_path: S3 file path for file-based lessons
        content: Content for AI-generated lessons
    """
    item = {
        'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
        'SK': f'LESSON#{lesson_id}',
        'title': title,
        'overview': overview,
        'order': order,
        'lesson_type': lesson_type
    }
    
    if lesson_type == "file" and file_path:
        item['file_path'] = file_path
    elif lesson_type == "content" and content:
        item['content'] = content
        
    course_table.put_item(Item=item)
    return True

def get_unit_lessons(course_code, unit_id):
    """
    Get all lessons for a specific unit
    """
    response = course_table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
        ExpressionAttributeValues={
            ':pk': f'COURSE#{course_code}#UNIT#{unit_id}',
            ':sk_prefix': 'LESSON#'
        }
    )
    return response.get('Items', [])

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
    Delete a unit and all its associated lessons
    """
    try:
        # First, get all lessons for this unit
        lessons = get_unit_lessons(course_code, unit_id)
        
        # Delete all lessons
        for lesson in lessons:
            course_table.delete_item(
                Key={
                    'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                    'SK': f'LESSON#{lesson.get("SK").replace("LESSON#", "")}'
                }
            )
        
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

def delete_lesson(course_code, unit_id, lesson_id):
    """
    Delete a single lesson from a unit
    """
    try:
        # Get lesson details first
        response = course_table.get_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'LESSON#{lesson_id}'
            }
        )
        lesson = response.get('Item', {})
        
        # If it's a file-based lesson, delete the file from S3
        if lesson.get('lesson_type') == 'file':
            file_path = lesson.get('file_path')
            if file_path:
                # Extract filename from path
                file_name = file_path.split('/')[-1]
                delete_content_file(course_code, file_name)
        
        # Delete the lesson from DynamoDB
        course_table.delete_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'LESSON#{lesson_id}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting lesson: {e}")
        return False

def update_lesson(course_code, unit_id, lesson_id, title=None, overview=None, content=None, lesson_type=None, file_path=None):
    """
    Update a lesson's details
    Args:
        course_code: The course code
        unit_id: The unit ID
        lesson_id: The lesson ID
        title: Optional lesson title
        overview: Optional lesson overview
        content: Optional lesson content as a string (markdown)
        lesson_type: Optional lesson type ("file" or "content")
        file_path: Optional S3 file path for file-based lessons
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get current lesson details
        response = course_table.get_item(
            Key={
                'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                'SK': f'LESSON#{lesson_id}'
            }
        )
        current_lesson = response.get('Item', {})
        
        # Build update expression and values
        update_parts = []
        expr_values = {}
        
        # Add title update if provided
        if title is not None:
            update_parts.append('title = :title')
            expr_values[':title'] = title
        else:
            title = current_lesson.get('title', '')
        
        # Add overview update if provided
        if overview is not None:
            update_parts.append('overview = :overview')
            expr_values[':overview'] = overview
        else:
            overview = current_lesson.get('overview', '')
        
        # Add lesson type update if provided
        if lesson_type is not None:
            update_parts.append('lesson_type = :lesson_type')
            expr_values[':lesson_type'] = lesson_type
            
            # If changing to file type, update file path
            if lesson_type == "file" and file_path:
                update_parts.append('file_path = :file_path')
                expr_values[':file_path'] = file_path
                # Remove content if it exists
                update_parts.append('content = :empty')
                expr_values[':empty'] = None
            # If changing to content type, update content
            elif lesson_type == "content" and content:
                update_parts.append('content = :content')
                expr_values[':content'] = content
                # Remove file path if it exists
                update_parts.append('file_path = :empty')
                expr_values[':empty'] = None
        
        # Add content update if provided (only for content-type lessons)
        elif content is not None and current_lesson.get('lesson_type') == "content":
            update_parts.append('content = :content')
            expr_values[':content'] = content
        
        # Add file path update if provided (only for file-type lessons)
        elif file_path is not None and current_lesson.get('lesson_type') == "file":
            update_parts.append('file_path = :file_path')
            expr_values[':file_path'] = file_path
        
        # Only update if there are changes
        if update_parts:
            update_expr = 'SET ' + ', '.join(update_parts)
            
            # Update the lesson
            course_table.update_item(
                Key={
                    'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                    'SK': f'LESSON#{lesson_id}'
                },
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
        
        return True
    except Exception as e:
        logger.error(f"Error updating lesson: {e}")
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
    Copy all units and lessons from source course to target course
    """
    try:
        # Get all units from source course
        source_units = get_course_units(source_course_code)
        
        # For each unit, copy it and its lessons
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
            
            # Get all lessons for this unit
            lessons = get_unit_lessons(source_course_code, unit_id)
            
            # Copy each lesson
            for lesson in lessons:
                lesson_id = lesson['SK'].replace('LESSON#', '')
                create_lesson(
                    course_code=target_course_code,
                    unit_id=unit_id,
                    lesson_id=lesson_id,
                    title=lesson['title'],
                    overview=lesson.get('overview', ''),
                    order=lesson['order']
                )
        
        return True
    except Exception as e:
        logger.error(f"Error copying course contents: {e}")
        return False

def update_lesson_orders(course_code, unit_id, lesson_orders):
    """
    Update the order of multiple lessons within a unit
    Args:
        course_code: The course code
        unit_id: The unit ID
        lesson_orders: List of tuples (lesson_id, new_order)
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        for lesson_id, new_order in lesson_orders:
            course_table.update_item(
                Key={
                    'PK': f'COURSE#{course_code}#UNIT#{unit_id}',
                    'SK': f'LESSON#{lesson_id}'
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
        logger.error(f"Error updating lesson orders: {e}")
        return False 