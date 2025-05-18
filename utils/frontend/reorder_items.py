import streamlit as st
from streamlit_sortables import sort_items

def create_sortable_list(items, direction="vertical", key=None):
    """
    Create a sortable list with consistent styling
    Args:
        items: List of items to be sorted
        direction: "vertical" or "horizontal"
        key: Optional key for the component
    Returns:
        list: Sorted items
    """
    # Get theme colors
    bg_color = st.get_option('theme.backgroundColor')
    sbg_color = st.get_option('theme.secondaryBackgroundColor')
    
    custom_style = f"""
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@700&family=Montserrat:wght@400;500;600;700&display=swap');
    
    .sortable-component {{
        border: 1px solid {sbg_color};
        border-radius: 5px;
        padding: 5px;
        font-family: 'Montserrat', sans-serif;
    }}
    .sortable-item {{
        background-color: {bg_color};
        border: 1px solid {sbg_color};
        border-radius: 4px;
        margin: 4px 0;
        padding: 8px 12px;
        cursor: move;
        font-family: 'Montserrat', sans-serif;
        font-weight: 400;
        color: #0F1B2A;
        -webkit-font-smoothing: antialiased;
    }}
    .sortable-item:hover {{
        background-color: {sbg_color};
    }}
    .sortable-item.dragging {{
        opacity: 0.5;
        background-color: {sbg_color};
    }}
    """
    
    return sort_items(items, direction=direction, custom_style=custom_style, key=key) 