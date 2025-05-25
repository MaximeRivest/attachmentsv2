from .core import Attachment, modifier

# Use string literals for type annotations to avoid import issues
# The actual imports are handled by the loader functions


# --- MODIFIERS ---

@modifier
def pages(att: Attachment) -> Attachment:
    """Fallback pages modifier - stores page commands for later processing."""
    # This fallback handles the case when object isn't loaded yet
    # The actual page selection will happen in the type-specific modifiers
    return att

@modifier
def pages(att: Attachment, pdf: 'pdfplumber.PDF') -> Attachment:
    """Extract specific pages from PDF."""
    if 'pages' not in att.commands:
        return att
    
    pages_spec = att.commands['pages']
    selected_pages = []
    
    # Parse page specification
    for part in pages_spec.split(','):
        part = part.strip()
        if '-' in part and not part.startswith('-'):
            start, end = map(int, part.split('-'))
            selected_pages.extend(range(start, end + 1))
        elif part == '-1':
            try:
                total_pages = len(pdf.pages)
                selected_pages.append(total_pages)
            except:
                selected_pages.append(1)
        else:
            selected_pages.append(int(part))
    
    att.metadata['selected_pages'] = selected_pages
    return att


@modifier
def pages(att: Attachment, pres: 'pptx.Presentation') -> Attachment:
    """Extract specific slides from PowerPoint."""
    if 'pages' not in att.commands:
        return att
    
    pages_spec = att.commands['pages']
    selected_slides = []
    
    for part in pages_spec.split(','):
        part = part.strip()
        if '-' in part and not part.startswith('-'):
            start, end = map(int, part.split('-'))
            selected_slides.extend(range(start - 1, end))
        elif part == '-1':
            try:
                selected_slides.append(len(pres.slides) - 1)
            except:
                selected_slides.append(0)
        else:
            selected_slides.append(int(part) - 1)
    
    att.metadata['selected_slides'] = selected_slides
    return att


@modifier
def limit(att: Attachment, df: 'pandas.DataFrame') -> Attachment:
    """Limit pandas DataFrame rows."""
    if 'limit' in att.commands:
        try:
            limit_val = int(att.commands['limit'])
            att._obj = df.head(limit_val)
        except:
            pass
    return att


@modifier
def select(att: Attachment, df: 'pandas.DataFrame') -> Attachment:
    """Select columns from pandas DataFrame."""
    if 'select' in att.commands:
        try:
            columns = [c.strip() for c in att.commands['select'].split(',')]
            att._obj = df[columns]
        except:
            pass
    return att


@modifier
def select(att: Attachment, soup: 'bs4.BeautifulSoup') -> Attachment:
    """
    Generic select modifier that works with different object types.
    Can be used with both command syntax and direct arguments.
    """
    # Check if we have a select command from attachy syntax or direct argument
    if 'select' not in att.commands:
        return att
    
    selector = att.commands['select']
    
    # If we have a BeautifulSoup object, handle CSS selection
    if att._obj and hasattr(att._obj, 'select'):
        # Use CSS selector to find matching elements
        selected_elements = att._obj.select(selector)
        
        if not selected_elements:
            # If no elements found, create empty soup
            from bs4 import BeautifulSoup
            new_soup = BeautifulSoup("", 'html.parser')
        elif len(selected_elements) == 1:
            # If single element, use it directly
            from bs4 import BeautifulSoup
            new_soup = BeautifulSoup(str(selected_elements[0]), 'html.parser')
        else:
            # If multiple elements, wrap them in a container
            from bs4 import BeautifulSoup
            container_html = ''.join(str(elem) for elem in selected_elements)
            new_soup = BeautifulSoup(f"<div>{container_html}</div>", 'html.parser')
        
        # Update the attachment with selected content
        att._obj = new_soup
        
        # Update metadata to track the selection
        att.metadata.update({
            'selector': selector,
            'selected_count': len(selected_elements),
            'selection_applied': True
        })
    
    return att

@modifier  
def crop(att: Attachment, img: 'PIL.Image.Image') -> Attachment:
    """Crop: [crop:x1,y1,x2,y2] (box: left, upper, right, lower)"""
    if 'crop' not in att.commands:
        return att
    box = att.commands['crop']
    # Accept string "x1,y1,x2,y2" or tuple/list
    if isinstance(box, str):
        try:
            box = [int(x) for x in box.split(',')]
        except Exception:
            raise ValueError(f"Invalid crop box format: {att.commands['crop']!r}")
    if not (isinstance(box, (list, tuple)) and len(box) == 4):
        raise ValueError(f"Crop box must be 4 values (x1,y1,x2,y2), got: {box!r}")
    x1, y1, x2, y2 = box
    # Use the box as provided, do not reorder coordinates
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid crop box: right <= left or lower <= upper ({x1},{y1},{x2},{y2})")
    att._obj = img.crop((x1, y1, x2, y2))
    return att

@modifier
def rotate(att: Attachment, img: 'PIL.Image.Image') -> Attachment:
    """Rotate: [rotate:degrees] (positive = clockwise)"""
    if 'rotate' in att.commands:
        att._obj = img.rotate(-float(att.commands['rotate']), expand=True)
    return att

@modifier
def resize(att: Attachment, img: 'PIL.Image.Image') -> Attachment:
    """Resize: [resize:50%] or [resize:800x600] or [resize:800]"""
    if 'resize' not in att.commands:
        return att
    
    resize_spec = att.commands['resize']
    original_width, original_height = img.size
    
    try:
        if resize_spec.endswith('%'):
            # Percentage scaling: "50%" -> scale to 50% of original size
            percentage = float(resize_spec[:-1]) / 100.0
            new_width = int(original_width * percentage)
            new_height = int(original_height * percentage)
        elif 'x' in resize_spec:
            # Dimension specification: "800x600" -> specific width and height
            width_str, height_str = resize_spec.split('x', 1)
            new_width = int(width_str)
            new_height = int(height_str)
        else:
            # Single dimension: "800" -> scale proportionally to this width
            new_width = int(resize_spec)
            aspect_ratio = original_height / original_width
            new_height = int(new_width * aspect_ratio)
        
        # Ensure minimum size of 1x1
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        
        att._obj = img.resize((new_width, new_height))
        att.metadata.update({
            'resize_applied': True,
            'original_size': (original_width, original_height),
            'new_size': (new_width, new_height),
            'resize_spec': resize_spec
        })
        
    except (ValueError, ZeroDivisionError) as e:
        # If resize fails, keep original image and log the error
        att.metadata.update({
            'resize_error': f"Invalid resize specification '{resize_spec}': {str(e)}"
        })
    
    return att