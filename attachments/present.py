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
    """Convert PDF to markdown with text extraction. Handles scanned PDFs gracefully."""
    att.text += f"# PDF Document: {att.path}\n\n"
    
    try:
        # Process ALL pages by default, or only selected pages if specified
        if 'selected_pages' in att.metadata:
            pages_to_process = att.metadata['selected_pages']
        else:
            # Process ALL pages by default
            pages_to_process = range(1, len(pdf.pages) + 1)
        
        total_text_length = 0
        pages_with_text = 0
        
        for page_num in pages_to_process:
            if 1 <= page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]
                page_text = page.extract_text() or ""
                
                # Track text statistics
                if page_text.strip():
                    pages_with_text += 1
                    total_text_length += len(page_text.strip())
                
                # Only add page content if there's meaningful text
                if page_text.strip():
                    att.text += f"## Page {page_num}\n\n{page_text}\n\n"
                else:
                    # For pages with no text, add a placeholder
                    att.text += f"## Page {page_num}\n\n*[No extractable text - likely scanned image]*\n\n"
        
        # Detect if this is likely a scanned PDF
        avg_text_per_page = total_text_length / len(pages_to_process) if pages_to_process else 0
        is_likely_scanned = (
            pages_with_text == 0 or  # No pages have text
            avg_text_per_page < 50 or  # Very little text per page
            pages_with_text / len(pages_to_process) < 0.3  # Less than 30% of pages have text
        )
        
        if is_likely_scanned:
            att.text += f"\n📄 **Document Analysis**: This appears to be a scanned PDF with little to no extractable text.\n\n"
            att.text += f"- **Pages processed**: {len(pages_to_process)}\n"
            att.text += f"- **Pages with text**: {pages_with_text}\n"
            att.text += f"- **Average text per page**: {avg_text_per_page:.0f} characters\n\n"
            att.text += f"💡 **Suggestions**:\n"
            att.text += f"- Use the extracted images for vision-capable LLMs (Claude, GPT-4V)\n"
            att.text += f"- Consider OCR tools like `pytesseract` for text extraction\n"
            att.text += f"- The images are available in the `images` property for multimodal analysis\n\n"
            
            # Add metadata to help downstream processing
            att.metadata.update({
                'is_likely_scanned': True,
                'pages_with_text': pages_with_text,
                'total_pages': len(pages_to_process),
                'avg_text_per_page': avg_text_per_page,
                'text_extraction_quality': 'poor' if avg_text_per_page < 20 else 'limited'
            })
        else:
            att.text += f"*Total pages processed: {len(pages_to_process)}*\n\n"
            att.metadata.update({
                'is_likely_scanned': False,
                'pages_with_text': pages_with_text,
                'total_pages': len(pages_to_process),
                'avg_text_per_page': avg_text_per_page,
                'text_extraction_quality': 'good'
            })
            
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
    """Extract plain text from PDF. Handles scanned PDFs gracefully."""
    att.text += f"PDF Document: {att.path}\n"
    att.text += "=" * len(f"PDF Document: {att.path}") + "\n\n"
    
    try:
        # Process ALL pages by default, or only selected pages if specified
        if 'selected_pages' in att.metadata:
            pages_to_process = att.metadata['selected_pages']
        else:
            # Process ALL pages by default
            pages_to_process = range(1, len(pdf.pages) + 1)
        
        total_text_length = 0
        pages_with_text = 0
        
        for page_num in pages_to_process:
            if 1 <= page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]
                page_text = page.extract_text() or ""
                
                # Track text statistics
                if page_text.strip():
                    pages_with_text += 1
                    total_text_length += len(page_text.strip())
                
                # Only add page content if there's meaningful text
                if page_text.strip():
                    att.text += f"[Page {page_num}]\n{page_text}\n\n"
                else:
                    # For pages with no text, add a placeholder
                    att.text += f"[Page {page_num}]\n[No extractable text - likely scanned image]\n\n"
        
        # Detect if this is likely a scanned PDF (same logic as markdown presenter)
        avg_text_per_page = total_text_length / len(pages_to_process) if pages_to_process else 0
        is_likely_scanned = (
            pages_with_text == 0 or  # No pages have text
            avg_text_per_page < 50 or  # Very little text per page
            pages_with_text / len(pages_to_process) < 0.3  # Less than 30% of pages have text
        )
        
        if is_likely_scanned:
            att.text += f"\nDOCUMENT ANALYSIS: This appears to be a scanned PDF with little to no extractable text.\n\n"
            att.text += f"- Pages processed: {len(pages_to_process)}\n"
            att.text += f"- Pages with text: {pages_with_text}\n"
            att.text += f"- Average text per page: {avg_text_per_page:.0f} characters\n\n"
            att.text += f"SUGGESTIONS:\n"
            att.text += f"- Use the extracted images for vision-capable LLMs (Claude, GPT-4V)\n"
            att.text += f"- Consider OCR tools like pytesseract for text extraction\n"
            att.text += f"- The images are available in the images property for multimodal analysis\n\n"
            
            # Add metadata to help downstream processing (if not already added by markdown presenter)
            if 'is_likely_scanned' not in att.metadata:
                att.metadata.update({
                    'is_likely_scanned': True,
                    'pages_with_text': pages_with_text,
                    'total_pages': len(pages_to_process),
                    'avg_text_per_page': avg_text_per_page,
                    'text_extraction_quality': 'poor' if avg_text_per_page < 20 else 'limited'
                })
        else:
            # Add metadata for good text extraction (if not already added)
            if 'is_likely_scanned' not in att.metadata:
                att.metadata.update({
                    'is_likely_scanned': False,
                    'pages_with_text': pages_with_text,
                    'total_pages': len(pages_to_process),
                    'avg_text_per_page': avg_text_per_page,
                    'text_extraction_quality': 'good'
                })
                
    except:
        att.text += "*Error extracting PDF text*\n\n"
    
    return att


# TEXT PRESENTERS for BeautifulSoup
@presenter
def text(att: Attachment, soup: 'bs4.BeautifulSoup') -> Attachment:
    """Extract text from BeautifulSoup object."""
    att.text += soup.get_text(strip=True)
    return att


@presenter
def html(att: Attachment, soup: 'bs4.BeautifulSoup') -> Attachment:
    """Get formatted HTML from BeautifulSoup object."""
    att.text += soup.prettify()
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
def images(att: Attachment, pdf_reader: 'pdfplumber.PDF') -> Attachment:
    """
    Convert PDF pages to PNG images using pypdfium2 (MIT-compatible).
    
    Extracts resize parameter from DSL commands: file.pdf[resize:50%]
    """
    try:
        # Try to import pypdfium2
        import pypdfium2 as pdfium
    except ImportError:
        # Fallback: add error message to metadata
        att.metadata['pdf_images_error'] = "pypdfium2 not installed. Install with: pip install pypdfium2"
        return att
    
    # Get resize parameter from DSL commands
    resize = att.commands.get('resize')
    
    images = []
    
    try:
        # Get the PDF bytes for pypdfium2
        # Check if we have a temporary PDF path (with CropBox already fixed)
        if 'temp_pdf_path' in att.metadata:
            # Use the temporary PDF file that already has CropBox defined
            with open(att.metadata['temp_pdf_path'], 'rb') as f:
                pdf_bytes = f.read()
        elif hasattr(pdf_reader, 'stream') and pdf_reader.stream:
            # Save current position
            original_pos = pdf_reader.stream.tell()
            # Read the PDF bytes
            pdf_reader.stream.seek(0)
            pdf_bytes = pdf_reader.stream.read()
            # Restore position
            pdf_reader.stream.seek(original_pos)
        else:
            # Try to get bytes from the file path if available
            if hasattr(pdf_reader, 'stream') and hasattr(pdf_reader.stream, 'name'):
                with open(pdf_reader.stream.name, 'rb') as f:
                    pdf_bytes = f.read()
            elif att.path:
                # Use the attachment path directly
                with open(att.path, 'rb') as f:
                    pdf_bytes = f.read()
            else:
                raise Exception("Cannot access PDF bytes for rendering")
        
        # Open with pypdfium2 (CropBox should already be defined if temp file was used)
        pdf_doc = pdfium.PdfDocument(pdf_bytes)
        num_pages = len(pdf_doc)
        
        # Limit to reasonable number of pages (respect pages command if present)
        if 'pages' in att.commands:
            # If pages are specified, use those
            max_pages = min(num_pages, 20)  # Still cap at 20 for safety
        else:
            # Default limit
            max_pages = min(num_pages, 10)
        
        for page_idx in range(max_pages):
            page = pdf_doc[page_idx]
            
            # Render at 2x scale for better quality
            pil_image = page.render(scale=2).to_pil()
            
            # Apply resize if specified
            if resize:
                if 'x' in resize:
                    # Format: 800x600
                    w, h = map(int, resize.split('x'))
                    pil_image = pil_image.resize((w, h))
                elif resize.endswith('%'):
                    # Format: 50%
                    scale = int(resize[:-1]) / 100
                    new_width = int(pil_image.width * scale)
                    new_height = int(pil_image.height * scale)
                    pil_image = pil_image.resize((new_width, new_height))
            
            # Convert to PNG bytes
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            png_bytes = img_byte_arr.getvalue()
            
            # Encode as base64 data URL
            b64_string = base64.b64encode(png_bytes).decode('utf-8')
            images.append(f"data:image/png;base64,{b64_string}")
        
        # Clean up PDF document
        pdf_doc.close()
        
        # Add images to attachment
        att.images.extend(images)
        
        # Add metadata about image extraction
        att.metadata.update({
            'pdf_pages_rendered': len(images),
            'pdf_total_pages': num_pages,
            'pdf_resize_applied': resize if resize else None
        })
        
        return att
        
    except Exception as e:
        # Add error info to metadata instead of failing
        att.metadata['pdf_images_error'] = f"Error rendering PDF: {e}"
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
    """Add data preview to text (additive)."""
    try:
        head_text = f"\n## Data Preview\n\n"
        head_text += df.head().to_markdown(index=False)
        att.text += head_text + "\n\n"  # Additive: append to existing text
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
def head(att: Attachment) -> Attachment:
    """Fallback head presenter for non-DataFrame objects."""
    if hasattr(att._obj, 'head'):
        try:
            head_result = att._obj.head()
            att.text += f"\n## Preview\n\n{str(head_result)}\n\n"
        except:
            att.text += f"\n## Preview\n\n{str(att._obj)[:200]}\n\n"
    else:
        att.text += f"\n## Preview\n\n{str(att._obj)[:200]}\n\n"
    return att


@presenter
def metadata(att: Attachment) -> Attachment:
    """Add attachment metadata to text (user-friendly version)."""
    try:
        # Filter metadata to show only user-relevant information
        user_friendly_keys = {
            'format', 'size', 'mode', 'content_type', 'status_code', 
            'file_size', 'pdf_pages_rendered', 'pdf_total_pages',
            'collection_size', 'from_zip', 'zip_filename'
        }
        
        # Collect user-friendly metadata
        relevant_meta = {}
        for key, value in att.metadata.items():
            if key in user_friendly_keys:
                relevant_meta[key] = value
            elif key.endswith('_error'):
                # Show errors as they're important for users
                relevant_meta[key] = value
        
        if relevant_meta:
            meta_text = f"\n## File Info\n\n"
            for key, value in relevant_meta.items():
                # Format key names to be more readable
                display_key = key.replace('_', ' ').title()
                if key == 'size' and isinstance(value, tuple):
                    meta_text += f"- **{display_key}**: {value[0]} × {value[1]} pixels\n"
                elif key == 'pdf_pages_rendered':
                    meta_text += f"- **Pages Rendered**: {value}\n"
                elif key == 'pdf_total_pages':
                    meta_text += f"- **Total Pages**: {value}\n"
                else:
                    meta_text += f"- **{display_key}**: {value}\n"
            att.text += meta_text + "\n"
        # If no relevant metadata, don't add anything (cleaner output)
        
    except Exception as e:
        att.text += f"\n*Error displaying file info: {e}*\n\n"
    return att


@presenter
def summary(att: Attachment) -> Attachment:
    """Fallback summary presenter for non-DataFrame objects."""
    try:
        summary_text = f"\n## Object Summary\n\n"
        summary_text += f"- **Type**: {type(att._obj).__name__}\n"
        if hasattr(att._obj, '__len__'):
            try:
                summary_text += f"- **Length**: {len(att._obj)}\n"
            except:
                pass
        summary_text += f"- **String representation**: {str(att._obj)[:100]}...\n"
        att.text += summary_text + "\n"
    except Exception as e:
        att.text += f"\n*Error generating summary: {e}*\n\n"
    return att


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


# Note: truncate function moved to refine.py as refine.truncate
# This maintains clean separation: present extracts, refine processes

# OCR PRESENTER for scanned PDFs
@presenter
def ocr(att: Attachment, pdf_reader: 'pdfplumber.PDF') -> Attachment:
    """
    Extract text from scanned PDF using OCR (pytesseract).
    
    This presenter is useful for scanned PDFs with no extractable text.
    Requires: pip install pytesseract pillow
    Also requires tesseract binary: apt-get install tesseract-ocr (Ubuntu) or brew install tesseract (Mac)
    """
    try:
        import pytesseract
        from PIL import Image
        import pypdfium2 as pdfium
        import io
    except ImportError as e:
        att.text += f"\n## OCR Text Extraction\n\n"
        att.text += f"⚠️ **OCR not available**: Missing dependencies.\n\n"
        att.text += f"To enable OCR for scanned PDFs:\n"
        att.text += f"```bash\n"
        att.text += f"pip install pytesseract pypdfium2\n"
        att.text += f"# Ubuntu/Debian:\n"
        att.text += f"sudo apt-get install tesseract-ocr\n"
        att.text += f"# macOS:\n"
        att.text += f"brew install tesseract\n"
        att.text += f"```\n\n"
        att.text += f"Error: {e}\n\n"
        return att
    
    att.text += f"\n## OCR Text Extraction\n\n"
    
    try:
        # Get PDF bytes for pypdfium2
        if 'temp_pdf_path' in att.metadata:
            with open(att.metadata['temp_pdf_path'], 'rb') as f:
                pdf_bytes = f.read()
        elif att.path:
            with open(att.path, 'rb') as f:
                pdf_bytes = f.read()
        else:
            att.text += "⚠️ **OCR failed**: Cannot access PDF file.\n\n"
            return att
        
        # Open with pypdfium2
        pdf_doc = pdfium.PdfDocument(pdf_bytes)
        num_pages = len(pdf_doc)
        
        # Process pages (limit for performance)
        if 'selected_pages' in att.metadata:
            pages_to_process = att.metadata['selected_pages']
        else:
            # Limit OCR to first 5 pages by default (OCR is slow)
            pages_to_process = range(1, min(6, num_pages + 1))
        
        total_ocr_text = ""
        successful_pages = 0
        
        for page_num in pages_to_process:
            if 1 <= page_num <= num_pages:
                try:
                    page = pdf_doc[page_num - 1]
                    
                    # Render page as image
                    pil_image = page.render(scale=2).to_pil()  # Higher scale for better OCR
                    
                    # Perform OCR
                    page_text = pytesseract.image_to_string(pil_image, lang='eng')
                    
                    if page_text.strip():
                        att.text += f"### Page {page_num} (OCR)\n\n{page_text.strip()}\n\n"
                        total_ocr_text += page_text.strip()
                        successful_pages += 1
                    else:
                        att.text += f"### Page {page_num} (OCR)\n\n*[No text detected by OCR]*\n\n"
                        
                except Exception as e:
                    att.text += f"### Page {page_num} (OCR)\n\n*[OCR failed: {str(e)}]*\n\n"
        
        # Clean up
        pdf_doc.close()
        
        # Add OCR summary
        att.text += f"**OCR Summary**:\n"
        att.text += f"- Pages processed: {len(pages_to_process)}\n"
        att.text += f"- Pages with OCR text: {successful_pages}\n"
        att.text += f"- Total OCR text length: {len(total_ocr_text)} characters\n\n"
        
        # Update metadata
        att.metadata.update({
            'ocr_performed': True,
            'ocr_pages_processed': len(pages_to_process),
            'ocr_pages_successful': successful_pages,
            'ocr_text_length': len(total_ocr_text)
        })
        
    except Exception as e:
        att.text += f"⚠️ **OCR failed**: {str(e)}\n\n"
        att.metadata['ocr_error'] = str(e)
    
    return att
