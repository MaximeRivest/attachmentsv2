#!/usr/bin/env python3
"""
Simple API for Attachments - One-line file to LLM context
=========================================================

High-level interface that abstracts the grammar complexity:
- Attachments(*paths) - automatic processing of any file types
- str(ctx) - combined, prompt-engineered text
- ctx.images - all base64 images ready for LLMs
"""

from typing import List, Union
from .core import Attachment, AttachmentCollection, attach
import os

# Import the namespace objects, not the raw modules
# We can't use relative imports for the namespaces since they're created in __init__.py
def _get_namespaces():
    """Get the namespace objects after they're created."""
    from attachments import load, present, refine
    return load, present, refine

# Cache the namespaces
_namespaces = None

def _get_cached_namespaces():
    """Get cached namespaces."""
    global _namespaces
    if _namespaces is None:
        _namespaces = _get_namespaces()
    return _namespaces

class Attachments:
    """
    High-level interface for converting files to LLM-ready context.
    
    Usage:
        ctx = Attachments("report.pdf", "photo.jpg[rotate:90]", "data.csv")
        text = str(ctx)          # All extracted text, prompt-engineered
        images = ctx.images      # List of base64 PNG strings
    """
    
    def __init__(self, *paths: str):
        """Initialize with one or more file paths (with optional DSL commands)."""
        self.attachments: List[Attachment] = []
        self._process_files(paths)
    
    def _process_files(self, paths: tuple) -> None:
        """Process all input files through universal pipeline."""
        for path in paths:
            try:
                # Create attachment and apply universal auto-pipeline
                result = self._auto_process(attach(path))
                
                # Handle collections (like ZIP files)
                if isinstance(result, AttachmentCollection):
                    self.attachments.extend(result.attachments)
                elif isinstance(result, Attachment):
                    self.attachments.append(result)
                    
            except Exception as e:
                # Create a fallback attachment with error info
                error_att = Attachment(path)
                error_att.text = f"⚠️ Could not process {path}: {str(e)}"
                error_att.metadata = {'error': str(e), 'path': path}
                self.attachments.append(error_att)
    
    def _auto_process(self, att: Attachment) -> Union[Attachment, AttachmentCollection]:
        """Universal pipeline that handles any file type automatically."""
        
        # Get the proper namespaces
        load, present, refine = _get_cached_namespaces()
        
        # Smart loader chain - order matters for proper fallback
        # Put more specific loaders first, more general ones last
        try:
            loaded = (att 
                     | load.pdf_to_pdfplumber  # PDF → pdfplumber object
                     | load.csv_to_pandas      # CSV → pandas DataFrame  
                     | load.image_to_pil       # Images → PIL Image
                     | load.url_to_bs4         # URLs → BeautifulSoup
                     | load.text_to_string     # Text → string
                     | load.zip_to_images)     # ZIP → AttachmentCollection (last)
        except Exception as e:
            # If loading fails, create a basic attachment with the file content
            loaded = att
            try:
                # Try basic text loading as last resort
                if os.path.exists(att.path):
                    with open(att.path, 'r', encoding='utf-8', errors='ignore') as f:
                        loaded.text = f.read()
                        loaded._obj = loaded.text
            except:
                loaded.text = f"Could not read file: {att.path}"
        
        # Handle collections differently
        if isinstance(loaded, AttachmentCollection):
            # Vectorized processing for collections
            processed = (loaded 
                        | (present.images + present.metadata)
                        | refine.add_headers)
            return processed
        else:
            # Single file processing
            processed = (loaded
                        | (present.text + present.images + present.metadata)
                        | refine.add_headers)
            
            # Apply truncation only if text is very long (>5000 chars)
            if hasattr(processed, 'text') and processed.text and len(processed.text) > 5000:
                processed = processed | refine.truncate_text(3000)
            
            return processed
    
    def __str__(self) -> str:
        """Return all extracted text in a prompt-engineered format."""
        if not self.attachments:
            return ""
        
        text_sections = []
        
        for i, att in enumerate(self.attachments):
            if att.text:
                # Add file header if multiple files
                if len(self.attachments) > 1:
                    filename = att.path or f"File {i+1}"
                    section = f"## {filename}\n\n{att.text}"
                else:
                    section = att.text
                
                text_sections.append(section)
        
        combined_text = "\n\n---\n\n".join(text_sections)
        
        # Add metadata summary if useful
        if len(self.attachments) > 1:
            file_count = len(self.attachments)
            image_count = len(self.images)
            summary = f"📄 Processing Summary: {file_count} files processed"
            if image_count > 0:
                summary += f", {image_count} images extracted"
            combined_text = f"{summary}\n\n{combined_text}"
        
        return combined_text
    
    @property
    def images(self) -> List[str]:
        """Return all base64-encoded images ready for LLM APIs."""
        all_images = []
        for att in self.attachments:
            # Filter out placeholder images
            real_images = [img for img in att.images 
                          if img and not img.endswith('_placeholder')]
            all_images.extend(real_images)
        return all_images
    
    @property 
    def metadata(self) -> dict:
        """Return combined metadata from all processed files."""
        combined_meta = {
            'file_count': len(self.attachments),
            'image_count': len(self.images),
            'files': []
        }
        
        for att in self.attachments:
            file_meta = {
                'path': att.path,
                'text_length': len(att.text) if att.text else 0,
                'image_count': len([img for img in att.images 
                                  if not img.endswith('_placeholder')]),
                'metadata': att.metadata
            }
            combined_meta['files'].append(file_meta)
        
        return combined_meta
    
    def __len__(self) -> int:
        """Return number of processed files/attachments."""
        return len(self.attachments)
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        file_types = []
        for att in self.attachments:
            if att.path:
                ext = att.path.split('.')[-1].lower() if '.' in att.path else 'unknown'
                file_types.append(ext)
        
        type_summary = ', '.join(set(file_types)) if file_types else 'mixed'
        return f"Attachments({len(self.attachments)} files: {type_summary}, {len(self.images)} images)"
    
    # LLM API convenience methods
    
    def claude(self, prompt: str = "") -> List[dict]:
        """Get Claude API format directly."""
        from .adapt import claude
        combined_att = self._to_single_attachment()
        return claude(combined_att, prompt)
    
    def openai(self, prompt: str = "") -> List[dict]:
        """Get OpenAI Chat API format directly.""" 
        from .adapt import openai_chat
        combined_att = self._to_single_attachment()
        return openai_chat(combined_att, prompt)
    
    def _to_single_attachment(self) -> Attachment:
        """Convert to single attachment for API adapters."""
        if not self.attachments:
            return Attachment("")
        
        combined = Attachment("")
        combined.text = str(self)  # Use our formatted text
        combined.images = self.images
        combined.metadata = self.metadata
        
        return combined


# Convenience function for even simpler usage
def process(*paths: str) -> Attachments:
    """
    Process files and return Attachments object.
    
    Usage:
        ctx = process("report.pdf", "image.jpg")
        text = str(ctx)
        images = ctx.images
    """
    return Attachments(*paths) 