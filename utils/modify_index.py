import os
import streamlit as st
from utils.config import domain_url
from utils.logger import logger

def modify_index():
    app_title = "Playlab Courses"
    app_url = domain_url()
    app_description = "Teachers building AI-powered course materials."
    app_image = "https://raw.githubusercontent.com/teaghan/playlab-courses/main/images/Playlab_Icon.png"

    # Locate the streamlit package's static folder and index.html
    st_dir = os.path.dirname(st.__file__)
    index_path = os.path.join(st_dir, 'static', 'index.html')
    
    if not os.path.exists(index_path):
        logger.error(f"index.html not found at: {index_path}")
        return

    # Read the current index.html content
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if our custom meta tags are already present
    if '<!-- Custom Meta Tags for social preview -->' in content:
        logger.info("Custom meta tags already present. No changes made.")
        return

    # Define the custom meta tags (adjust the content as needed)
    custom_meta = f"""
    <!-- Custom Meta Tags for social preview -->
    <meta name="title" content="{app_title}">
    <meta name="description" content="{app_description}">
    
    <!-- Open Graph / Facebook / LinkedIn -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{app_url}">
    <meta property="og:title" content="{app_title}">
    <meta property="og:description" content="{app_description}">
    <meta property="og:image" content="{app_image}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{app_url}">
    <meta name="twitter:title" content="{app_title}">
    <meta name="twitter:description" content="{app_description}">
    <meta name="twitter:image" content="{app_image}">
    <!-- End Custom Meta Tags -->
    """

    # Insert the custom meta tags before the closing </head> tag
    if '</head>' in content:
        content = content.replace('</head>', custom_meta + '\n</head>')
    else:
        logger.error("No closing </head> tag found. Meta tags not inserted.")
        return

    # Write the modified content back to index.html
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info("Custom meta tags successfully inserted into index.html")

if __name__ == "__main__":
    modify_index()
