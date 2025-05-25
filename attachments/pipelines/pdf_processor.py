"""
PDF to LLM Pipeline Processor
============================

Complete pipeline for processing PDF files optimized for LLM consumption.
Supports DSL commands for format and focus customization.

DSL Commands:
    [format:markdown|text] - Output format preference (default to markdown)
    [focus:text|images|both] - Content focus
    [pages:1-5,10] - Specific pages (inherits from existing modify.pages)
    [resize:50%|800x600] - Image resize specification

Usage:
    # Explicit processor access
    result = processors.pdf_to_llm(attach("doc.pdf"))
    
    # Mixing with verbs (power users)
    result = processors.pdf_to_llm(attach("doc.pdf")) | refine.custom_step

    # Like any pipeline and attachment it's ready with adapters
    claude_message_format = result.claude()
"""

from ..core import Attachment, presenter
from . import processor
import base64
import io
from typing import Optional, List

@processor(
    match=lambda att: att.path.lower().endswith('.pdf'),
    description="Primary PDF processor with format and focus options"
)
def pdf_to_llm(att: Attachment) -> Attachment:
    """
    Process PDF files for LLM consumption.
    
    Supports DSL commands:
    - format: markdown
    - focus: text, images, otherwise default to both
    - resize_images: 50%, 800x600 (for images)
    """
    
    # Import namespaces properly to get VerbFunction wrappers
    from .. import load, modify, present, refine, attach
    
    # Enhanced pipeline with both text and images
    return (att 
           | load.pdf_to_pdfplumber 
           | modify.pages  # Optional - only acts if [pages:...] present
           | present.text + present.markdown + present.images 
           | refine.tile_images | refine.resize_images )
