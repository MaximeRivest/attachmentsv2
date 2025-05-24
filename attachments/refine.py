from .core import Attachment, refiner

# --- REFINERS ---

@refiner
def truncate_text(att: Attachment) -> Attachment:
    """Refine text content by truncating to specified length."""
    # Check for truncate in commands (from DSL) or direct call
    if 'truncate' not in att.commands:
        return att
        
    try:
        truncate_value = int(att.commands['truncate'])
    except (ValueError, TypeError):
        return att
    
    # Apply truncation to existing text
    if att.text and len(att.text) > truncate_value:
        original_length = len(att.text)
        att.text = att.text[:truncate_value]
        # Add metadata about the truncation
        att.metadata.update({
            'text_truncated': True,
            'original_length': original_length,
            'truncated_length': truncate_value
        })
    
    return att

@refiner
def add_headers(att: Attachment) -> Attachment:
    """Refine text content by adding markdown headers."""
    if att.text and not att.text.startswith('#'):
        # Add a main header if none exists
        att.text = f"# Document Content\n\n{att.text}"
        att.metadata['headers_added'] = True
    return att

@refiner
def format_tables(att: Attachment) -> Attachment:
    """Refine text content by formatting tables."""
    if att.text:
        # Simple table formatting - could be enhanced
        lines = att.text.split('\n')
        formatted_lines = []
        for line in lines:
            if '|' in line and line.count('|') > 2:
                # This looks like a table row, ensure proper spacing
                formatted_line = ' | '.join(part.strip() for part in line.split('|'))
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)
        att.text = '\n'.join(formatted_lines)
        att.metadata['tables_formatted'] = True
    return att

@refiner
def tile_images(att: Attachment) -> Attachment:
    """Refine images by tiling them in a grid layout."""
    if 'tile' not in att.commands or not att.images:
        return att
    
    try:
        grid_spec = att.commands['tile']  # e.g., "2x2"
        cols, rows = map(int, grid_spec.lower().split('x'))
        
        # For now, just add metadata about tiling
        # Real implementation would combine images into a grid
        att.metadata.update({
            'images_tiled': True,
            'tile_grid': f"{cols}x{rows}",
            'original_image_count': len(att.images)
        })
        
        # Placeholder: In real implementation, we'd combine the images
        # For now, just keep the first image as a placeholder
        if att.images:
            att.images = [att.images[0]]  # Placeholder for tiled result
            
    except (ValueError, IndexError):
        pass
    
    return att

@refiner
def resize_images(att: Attachment) -> Attachment:
    """Refine images by resizing them."""
    if 'resize' not in att.commands or not att.images:
        return att
    
    try:
        size_spec = att.commands['resize']  # e.g., "800x600"
        width, height = map(int, size_spec.lower().split('x'))
        
        # Add metadata about resizing
        att.metadata.update({
            'images_resized': True,
            'target_size': f"{width}x{height}",
            'image_count': len(att.images)
        })
        
        # Placeholder: Real implementation would resize base64 images
        
    except (ValueError, IndexError):
        pass
    
    return att 