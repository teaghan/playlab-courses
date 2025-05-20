import base64

def get_image_base64(image_path):
    # Get file extension from path
    file_extension = image_path.lower().split('.')[-1]
    
    # Map common image extensions to MIME types
    mime_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp'
    }
    
    # Get the appropriate MIME type or default to octet-stream if unknown
    mime_type = mime_types.get(file_extension, 'application/octet-stream')
    
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()
    return f"data:{mime_type};base64,{img_base64}"