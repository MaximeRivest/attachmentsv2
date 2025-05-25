from .core import Attachment, refiner

# --- REFINERS ---

@refiner
def truncate(att: Attachment, limit: int = None) -> Attachment:
    """Truncate text content to specified character limit."""
    # Get limit from DSL commands or parameter
    if limit is None:
        limit = int(att.commands.get('truncate', 1000))
    
    if att.text and len(att.text) > limit:
        att.text = att.text[:limit] + "..."
        # Add metadata about truncation
        att.metadata.setdefault('processing', []).append({
            'operation': 'truncate',
            'original_length': len(att.text) + len("...") - 3,
            'truncated_length': len(att.text)
        })
    
    return att

@refiner
def add_headers(att: Attachment) -> Attachment:
    """Add markdown headers to text content."""
    if att.text:
        # Simple header addition - could be enhanced with DSL commands
        lines = att.text.split('\n')
        if lines and not lines[0].startswith('#'):
            filename = getattr(att, 'path', 'Document')
            att.text = f"# {filename}\n\n{att.text}"
    return att

@refiner
def format_tables(att: Attachment) -> Attachment:
    """Format table content for better readability."""
    if att.text:
        # Simple table formatting - could be enhanced
        att.text = att.text.replace('\t', ' | ')
    return att

@refiner
def tile_images(collection: 'AttachmentCollection') -> Attachment:
    """Combine multiple images from a collection into a tiled grid."""
    try:
        from PIL import Image
        from .core import Attachment, AttachmentCollection
        
        # Handle both AttachmentCollection and single Attachment
        if isinstance(collection, AttachmentCollection):
            images = []
            for att in collection.attachments:
                if hasattr(att, '_obj') and isinstance(att._obj, Image.Image):
                    images.append(att._obj)
                elif att.images:
                    # Handle base64 images - would need to decode
                    pass
            
            if not images:
                return Attachment("")
                
            # Get tile configuration from first attachment's commands
            first_att = collection.attachments[0]
            tile_config = first_att.commands.get('tile', '2x2')
            
        else:
            # Single attachment case - just return it with images
            return collection
        
        # Parse tile configuration (e.g., "2x2", "3x1")
        if 'x' in tile_config:
            cols, rows = map(int, tile_config.split('x'))
        else:
            # Square grid
            size = int(tile_config)
            cols = rows = size
        
        # Calculate grid size
        img_count = len(images)
        if img_count == 0:
            return Attachment("")
            
        # Resize images to same size (use the smallest dimensions)
        if images:
            min_width = min(img.size[0] for img in images)
            min_height = min(img.size[1] for img in images)
            resized_images = [img.resize((min_width, min_height)) for img in images]
            
            # Create tiled image
            tile_width = min_width * cols
            tile_height = min_height * rows
            tiled_img = Image.new('RGB', (tile_width, tile_height), 'white')
            
            for i, img in enumerate(resized_images[:cols*rows]):
                row = i // cols
                col = i % cols
                x = col * min_width
                y = row * min_height
                tiled_img.paste(img, (x, y))
            
            # Create result attachment
            result = Attachment("")
            result._obj = tiled_img
            
            # Convert to base64 for images list
            import io
            import base64
            
            buffer = io.BytesIO()
            tiled_img.save(buffer, format='PNG')
            buffer.seek(0)
            img_data = base64.b64encode(buffer.read()).decode()
            result.images = [img_data]
            
            # Add metadata
            result.metadata = {
                'operation': 'tile_images',
                'grid_size': f"{cols}x{rows}",
                'original_count': img_count,
                'tiled_dimensions': (tile_width, tile_height)
            }
            
            return result
            
    except ImportError:
        raise ImportError("Pillow is required for image tiling. Install with: pip install Pillow")
    except Exception as e:
        raise ValueError(f"Could not tile images: {e}")

@refiner
def resize_images(att: Attachment) -> Attachment:
    """Resize images based on DSL commands."""
    try:
        from PIL import Image
        
        if hasattr(att, '_obj') and isinstance(att._obj, Image.Image):
            resize_config = att.commands.get('resize', '800x600')
            if 'x' in resize_config:
                width, height = map(int, resize_config.split('x'))
                att._obj = att._obj.resize((width, height))
                
                # Update metadata
                att.metadata.setdefault('processing', []).append({
                    'operation': 'resize',
                    'new_size': (width, height)
                })
        
        return att
        
    except ImportError:
        raise ImportError("Pillow is required for image resizing. Install with: pip install Pillow")
    except Exception as e:
        raise ValueError(f"Could not resize image: {e}") 