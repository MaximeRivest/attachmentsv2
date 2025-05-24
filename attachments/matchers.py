from .core import Attachment
# --- MATCHERS ---

def csv_match(att: 'Attachment') -> bool:
    return att.path.endswith('.csv')

def pdf_match(att: 'Attachment') -> bool:
    return att.path.endswith('.pdf')

def pptx_match(att: 'Attachment') -> bool:
    return att.path.endswith(('.pptx', '.ppt'))

def image_match(att: 'Attachment') -> bool:
    return att.path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))

def text_match(att: 'Attachment') -> bool:
    return att.path.endswith(('.txt', '.md', '.log', '.json', '.py'))

