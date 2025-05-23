from .core import Attachment, presenter
import io
import base64

# --- PRESENTERS ---

# MARKDOWN PRESENTERS
@presenter
def markdown(att: Attachment, df: 'pandas.DataFrame') -> Attachment:
    """Convert pandas DataFrame to markdown table."""
    try:
        att.text += f"## Data from {att.path}\n\n"
        att.text += df.to_markdown(index=False)
        att.text += f"\n\n*Shape: {df.shape}*\n\n"
    except:
        att.text += f"## Data from {att.path}\n\n*Could not convert to markdown*\n\n"
    return att


@presenter
def markdown(att: Attachment, pdf: 'pdfplumber.PDF') -> Attachment:
    """Convert PDF to markdown with text extraction."""
    att.text += f"# PDF Document: {att.path}\n\n"
    
    try:
        pages_to_process = att.metadata.get('selected_pages', range(1, min(6, len(pdf.pages) + 1)))
        
        for page_num in pages_to_process:
            if 1 <= page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]
                page_text = page.extract_text() or ""
                att.text += f"## Page {page_num}\n\n{page_text}\n\n"
        
        att.text += f"*Total pages processed: {len(pages_to_process)}*\n\n"
    except Exception as e:
        att.text += f"*Error extracting PDF text: {e}*\n\n"
    
    return att


@presenter
def markdown(att: Attachment, pres: 'pptx.Presentation') -> Attachment:
    """Convert PowerPoint to markdown with slide content."""
    att.text += f"# Presentation: {att.path}\n\n"
    
    try:
        slide_indices = att.metadata.get('selected_slides', range(min(5, len(pres.slides))))
        
        for i, slide_idx in enumerate(slide_indices):
            if 0 <= slide_idx < len(pres.slides):
                slide = pres.slides[slide_idx]
                att.text += f"## Slide {slide_idx + 1}\n\n"
                
                for shape in slide.shapes:
                    if hasattr(shape, 'text') and shape.text.strip():
                        att.text += f"{shape.text}\n\n"
        
        att.text += f"*Slides processed: {len(slide_indices)}*\n\n"
    except Exception as e:
        att.text += f"*Error extracting slides: {e}*\n\n"
    
    return att


@presenter
def markdown(att: Attachment, img: 'PIL.Image.Image') -> Attachment:
    """Convert image to markdown with metadata."""
    att.text += f"# Image: {att.path}\n\n"
    try:
        att.text += f"- **Format**: {getattr(img, 'format', 'Unknown')}\n"
        att.text += f"- **Size**: {getattr(img, 'size', 'Unknown')}\n"
        att.text += f"- **Mode**: {getattr(img, 'mode', 'Unknown')}\n\n"
        att.text += "*Image converted to base64 and available in images list*\n\n"
    except:
        att.text += "*Image metadata not available*\n\n"
    return att


# TEXT PRESENTERS
@presenter
def text(att: Attachment, df: 'pandas.DataFrame') -> Attachment:
    """Convert pandas DataFrame to plain text."""
    try:
        att.text += f"Data from {att.path}\n"
        att.text += "=" * len(f"Data from {att.path}") + "\n\n"
        att.text += df.to_string(index=False)
        att.text += f"\n\nShape: {df.shape}\n\n"
    except:
        att.text += f"Data from {att.path}\n*Could not convert to text*\n\n"
    return att


@presenter
def text(att: Attachment, pdf: 'pdfplumber.PDF') -> Attachment:
    """Extract plain text from PDF."""
    att.text += f"PDF Document: {att.path}\n"
    att.text += "=" * len(f"PDF Document: {att.path}") + "\n\n"
    
    try:
        pages_to_process = att.metadata.get('selected_pages', range(1, min(6, len(pdf.pages) + 1)))
        
        for page_num in pages_to_process:
            if 1 <= page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]
                page_text = page.extract_text() or ""
                att.text += f"[Page {page_num}]\n{page_text}\n\n"
    except:
        att.text += "*Error extracting PDF text*\n\n"
    
    return att


# IMAGES PRESENTERS
@presenter
def images(att: Attachment, img: 'PIL.Image.Image') -> Attachment:
    """Convert PIL Image to base64."""
    try:
        buffer = io.BytesIO()
        # Convert to RGB if necessary
        if hasattr(img, 'mode') and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(buffer, format='PNG')
        att.images.append(base64.b64encode(buffer.getvalue()).decode())
    except Exception as e:
        print(f"Error converting image to base64: {e}")
    return att


@presenter
def images(att: Attachment, pres: 'pptx.Presentation') -> Attachment:
    """Extract images from PowerPoint slides."""
    try:
        slide_indices = att.metadata.get('selected_slides', range(min(5, len(pres.slides))))
        
        for slide_idx in slide_indices:
            if 0 <= slide_idx < len(pres.slides):
                slide = pres.slides[slide_idx]
                
                for shape in slide.shapes:
                    if hasattr(shape, 'image'):
                        try:
                            image_bytes = shape.image.blob
                            att.images.append(base64.b64encode(image_bytes).decode())
                        except:
                            continue
    except Exception as e:
        print(f"Error extracting PowerPoint images: {e}")
    
    return att


@presenter
def images(att: Attachment, pdf: 'pdfplumber.PDF') -> Attachment:
    """Extract images from PDF pages (placeholder implementation)."""
    try:
        pages_to_process = att.metadata.get('selected_pages', range(1, min(4, len(pdf.pages) + 1)))
        
        for page_num in pages_to_process:
            if 1 <= page_num <= len(pdf.pages):
                # This is a placeholder - real implementation would extract actual images
                att.images.append(f"pdf_page_{page_num}_placeholder_base64")
    except:
        pass
    
    return att


# SUMMARY PRESENTERS
@presenter
def summary(att: Attachment, df: 'pandas.DataFrame') -> Attachment:
    """Add summary statistics to text."""
    try:
        summary_text = f"\n## Summary Statistics\n\n"
        summary_text += f"- **Rows**: {len(df)}\n"
        summary_text += f"- **Columns**: {len(df.columns)}\n"
        
        # Try to get memory usage
        try:
            memory_usage = df.memory_usage(deep=True).sum()
            summary_text += f"- **Memory Usage**: {memory_usage} bytes\n"
        except:
            summary_text += f"- **Memory Usage**: Not available\n"
        
        # Get numeric columns
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            summary_text += f"- **Numeric Columns**: {numeric_cols}\n"
        except:
            summary_text += f"- **Numeric Columns**: Not available\n"
        
        att.text += summary_text + "\n"
    except Exception as e:
        att.text += f"\n*Error generating summary: {e}*\n\n"
    
    return att


@presenter
def head(att: Attachment, df: 'pandas.DataFrame') -> Attachment:
    """Add data preview to text."""
    try:
        head_text = f"\n## Data Preview\n\n"
        head_text += df.head().to_markdown(index=False)
        att.text += head_text + "\n\n"
    except Exception as e:
        att.text += f"\n*Error generating preview: {e}*\n\n"
    
    return att


@presenter
def metadata(att: Attachment, pdf: 'pdfplumber.PDF') -> Attachment:
    """Extract PDF metadata to text."""
    try:
        meta_text = f"\n## Document Metadata\n\n"
        if hasattr(pdf, 'metadata') and pdf.metadata:
            for key, value in pdf.metadata.items():
                meta_text += f"- **{key}**: {value}\n"
        else:
            meta_text += "*No metadata available*\n"
        
        att.text += meta_text + "\n"
    except Exception as e:
        att.text += f"\n*Error extracting metadata: {e}*\n\n"
    
    return att


@presenter
def thumbnails(att: Attachment, pdf: 'pdfplumber.PDF') -> Attachment:
    """Generate page thumbnails from PDF."""
    try:
        pages_to_process = att.metadata.get('selected_pages', range(1, min(4, len(pdf.pages) + 1)))
        
        for page_num in pages_to_process:
            if 1 <= page_num <= len(pdf.pages):
                # Placeholder for PDF page thumbnail
                att.images.append(f"thumbnail_page_{page_num}_base64_placeholder")
    except:
        pass
    
    return att


@presenter
def contact_sheet(att: Attachment, pres: 'pptx.Presentation') -> Attachment:
    """Create a contact sheet image from slides."""
    try:
        slide_indices = att.metadata.get('selected_slides', range(len(pres.slides)))
        if slide_indices:
            # Placeholder for contact sheet
            att.images.append("contact_sheet_base64_placeholder")
    except:
        pass
    
    return att


# CSV PRESENTER
@presenter
def csv(att: Attachment, df: 'pandas.DataFrame') -> Attachment:
    """Convert pandas DataFrame to CSV."""
    try:
        att.text += df.to_csv(index=False)
    except Exception as e:
        att.text += f"*Error converting to CSV: {e}*\n"
    return att


# XML PRESENTER  
@presenter
def xml(att: Attachment, df: 'pandas.DataFrame') -> Attachment:
    """Convert pandas DataFrame to XML."""
    try:
        att.text += df.to_xml(index=False)
    except Exception as e:
        att.text += f"*Error converting to XML: {e}*\n"
    return att


# FALLBACK PRESENTERS
@presenter
def markdown(att: Attachment) -> Attachment:
    """Fallback markdown presenter for unknown types."""
    att.text += f"# {att.path}\n\n*Object type: {type(att._obj)}*\n\n"
    att.text += f"```\n{str(att._obj)[:500]}\n```\n\n"
    return att


@presenter
def text(att: Attachment) -> Attachment:
    """Fallback text presenter for unknown types."""
    att.text += f"{att.path}: {str(att._obj)[:500]}\n\n"
    return att


@presenter
def images(att: Attachment) -> Attachment:
    """Fallback images presenter."""
    return att
