from .core import Attachment
import re

# --- MATCHERS ---

def url_match(att: 'Attachment') -> bool:
    """Check if the attachment path looks like a URL."""
    url_pattern = r'^https?://'
    return bool(re.match(url_pattern, att.path))

def csv_match(att: 'Attachment') -> bool:
    return att.path.endswith('.csv')

def pdf_match(att: 'Attachment') -> bool:
    return att.path.endswith('.pdf')

def pptx_match(att: 'Attachment') -> bool:
    return att.path.endswith(('.pptx', '.ppt'))

def image_match(att: 'Attachment') -> bool:
    return att.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic', '.heif'))

def text_match(att: 'Attachment') -> bool:
    return att.path.endswith(('.txt', '.md', '.log', '.json', '.py'))

def zip_match(att: 'Attachment') -> bool:
    """Check if the attachment path is a ZIP file."""
    return att.path.lower().endswith('.zip')

