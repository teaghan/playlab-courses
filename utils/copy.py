import pyperclip

def to_clipboard(text_to_copy: str) -> None:
    """
    Copy text to clipboard
    Args:
        text_to_copy (str): The text to be copied to clipboard
    """
    pyperclip.copy(text_to_copy)