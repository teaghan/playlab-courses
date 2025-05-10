import streamlit as st
import streamlit.components.v1 as components
from typing import Any, Optional

# Component configuration
COMPONENT_URL = "https://js-eval.netlify.app/"

# Declare the component
streamlit_js_eval = components.declare_component(
    "streamlit_js_eval",
    url=COMPONENT_URL
)

def evaluate_js(
    js_expressions: str,
    key: Optional[str] = None,
    default: Any = None,
    height: int = 0,
    **kwargs
) -> Any:
    """
    Evaluate JavaScript expressions in the browser context.
    
    Args:
        js_expressions: JavaScript code to evaluate
        key: Unique key to identify the component instance
        default: Default value to return if evaluation fails
        height: Initial height of the iframe (in pixels)
        **kwargs: Additional arguments to pass to the component
        
    Returns:
        Result of the JavaScript evaluation or default value
    """
    try:
        result = streamlit_js_eval(
            js_expressions=js_expressions,
            key=key,
            default=default,
            height=height,
            **kwargs
        )
        
        # Handle potential errors from the component
        if isinstance(result, dict) and "error" in result:
            return default
        
        return result
    
    except Exception as e:
        return default