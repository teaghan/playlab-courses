import streamlit as st
import streamlit.components.v1 as components

def load_style():
    """Load and apply custom styling to the Streamlit app."""
    
    # Define the CSS
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@700&family=Montserrat:wght@400;500;600;700&display=swap');

     /* Base styles */
    body * {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'Lexend', sans-serif !important;
        color: #0F1B2A !important;
    }

    /* h4 specific styling */
    h4, h5, h6 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        color: #666666 !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Text formatting */
    strong {
        font-weight: 700 !important;
    }

    em {
        font-style: italic !important;
    }
    """
    # Inject CSS
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    css = """
    <style>
        /* Outer sidebar container */
        section[data-testid="stSidebar"] {
        width: 300px !important;
        }
        /* Expanded */
        section[data-testid="stSidebar"] .css-ng1t4o {
        width: 300px !important;
        }
        /* Collapsed */
        section[data-testid="stSidebar"] .css-1d391kg {
        width: 300px !important;
        }
    </style>
    """

    # Inject CSS
    st.markdown(f'<style>{css}', unsafe_allow_html=True)

def scroll_to(element_id):
    components.html(f'''
        <script>
            var element = window.parent.document.getElementById("{element_id}");
            element.scrollIntoView({{behavior: 'smooth'}});
        </script>
    '''.encode())

def button_style():
    pr_color = st.get_option('theme.primaryColor')
    if 'role' in st.session_state and st.session_state.role == 'teacher':
        bg_color = st.get_option('theme.secondaryBackgroundColor')
        sbg_color = st.get_option('theme.backgroundColor')
    else:
        bg_color = st.get_option('theme.backgroundColor')
        sbg_color = st.get_option('theme.secondaryBackgroundColor')
    
    st.markdown(
        f"""
        <style>
        .element-container:has(#button-after) + div button {{
            background-color: {sbg_color};
            border: 0px solid {pr_color};
            color: {pr_color};
            padding: 0.5em 1em;
            border-radius: 4px;
            transition: background-color 0.2s ease;
        }}
        .element-container:has(#button-after) + div button:hover {{
            background-color: {bg_color};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    def custom_button():
        st.markdown('<span id="button-after"></span>', unsafe_allow_html=True)

    return custom_button

def columns_style():
    
    def custom_columns():        
        st.markdown(
        """
        <style>
        [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            gap: 10px;  /* Space between buttons */
            padding-bottom: 10px;  /* Space for scrollbar */
            justify-content: flex-start !important;  /* Align items to start */
            max-width: 100% !important;
        }
        
        /* Lock column widths to a specific size */
        [data-testid="stHorizontalBlock"] > div {
            flex: 0 0 80px !important;  /* Fixed width for columns */
            min-width: 80px !important;
            width: 80px !important;
            margin-right: 0 !important;
        }
        
        /* Make buttons fill their container */
        [data-testid="stHorizontalBlock"] button {
            width: 100% !important;
            min-width: unset !important;
            padding: 0 8px !important;
        }
        
        /* Hide scrollbar (optional) */
        [data-testid="stHorizontalBlock"]::-webkit-scrollbar {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
        st.markdown('<span id="scrollable-columns-after"></span>', unsafe_allow_html=True)
    
    return custom_columns