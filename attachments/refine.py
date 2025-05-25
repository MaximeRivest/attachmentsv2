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
    """Resize images (in base64) based on DSL commands and return as base64.
    
    Supports:
    - Percentage scaling: [resize_images:50%]
    - Specific dimensions: [resize_images:800x600] 
    - Proportional width: [resize_images:800]
    """
    try:
        from PIL import Image
        import io
        import base64

        # Get resize specification from DSL commands
        resize_spec = att.commands.get('resize_images', '800x600')

        resized_images_b64 = []
        for img_b64 in getattr(att, "images", []):
            try:
                # Handle both data URLs and raw base64
                if img_b64.startswith('data:image/'):
                    # Extract base64 data from data URL
                    img_data_b64 = img_b64.split(',', 1)[1]
                else:
                    # Raw base64 data
                    img_data_b64 = img_b64
                
                img_data = base64.b64decode(img_data_b64)
                img = Image.open(io.BytesIO(img_data))
                img = img.convert("RGB")
                
                # Get original dimensions
                original_width, original_height = img.size
                
                # Parse resize specification (same logic as modify.resize)
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
                
                # Resize the image
                img_resized = img.resize((new_width, new_height))
                
                # Convert back to base64
                buffer = io.BytesIO()
                img_resized.save(buffer, format="PNG")
                buffer.seek(0)
                img_resized_b64 = base64.b64encode(buffer.read()).decode()
                
                # Return in the same format as input (data URL or raw base64)
                if img_b64.startswith('data:image/'):
                    resized_images_b64.append(f"data:image/png;base64,{img_resized_b64}")
                else:
                    resized_images_b64.append(img_resized_b64)
                    
            except (ValueError, ZeroDivisionError) as e:
                # If one image fails, skip it but log the error
                att.metadata.setdefault('processing_errors', []).append({
                    'operation': 'resize_images',
                    'error': f"Invalid resize specification '{resize_spec}': {str(e)}",
                    'image_index': len(resized_images_b64)
                })
                continue
            except Exception as e:
                # If one image fails for other reasons, skip it
                att.metadata.setdefault('processing_errors', []).append({
                    'operation': 'resize_images', 
                    'error': f"Failed to process image: {str(e)}",
                    'image_index': len(resized_images_b64)
                })
                continue

        att.images = resized_images_b64

        # Update metadata with detailed information
        att.metadata.setdefault('processing', []).append({
            'operation': 'resize_images',
            'resize_spec': resize_spec,
            'images_processed': len(resized_images_b64),
            'images_failed': len(getattr(att, 'images', [])) - len(resized_images_b64)
        })

        return att

    except ImportError:
        raise ImportError("Pillow is required for image resizing. Install with: pip install Pillow")
    except Exception as e:
        raise ValueError(f"Could not resize images: {e}") 