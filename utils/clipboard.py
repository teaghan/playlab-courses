import streamlit as st
from st_copy_to_clipboard import st_copy_to_clipboard

@st.dialog("Copy Course URL")
def to_clipboard(text_to_copy: str) -> None:
    """
    Copy text to clipboard
    Args:
        text_to_copy (str): The text to be copied to clipboard
    """
    st.markdown("Here is the URL to share with your students:")
    col1, col2 = st.columns((3, 1))
    with col1:
        st.markdown(text_to_copy)
    with col2:
        st_copy_to_clipboard(text_to_copy, 
                                before_copy_label="Copy", 
                                after_copy_label="Copied!")
    if st.button("Close", use_container_width=True, type="primary"):
        st.rerun()