"""
PDF to LLM Pipeline Processor
============================

Complete pipeline for processing PDF files optimized for LLM consumption.
Supports clean DSL commands for the Attachments() simple API.

DSL Commands:
    [images:true|false] - Include images (default: true)
    [format:plain|markdown|code] - Text formatting (default: markdown)
        Aliases: text=plain, txt=plain, md=markdown
    [pages:1-5,10] - Specific pages (inherits from existing modify.pages)
    [resize:50%|800x600] - Image resize specification

Usage:
    # Explicit processor access
    result = processors.pdf_to_llm(attach("doc.pdf"))
    
    # With DSL commands
    result = processors.pdf_to_llm(attach("doc.pdf[format:plain][images:false]"))
    result = processors.pdf_to_llm(attach("doc.pdf[format:md]"))  # markdown alias
    result = processors.pdf_to_llm(attach("doc.pdf[images:false]"))  # text only
    
    # Mixing with verbs (power users)
    result = processors.pdf_to_llm(attach("doc.pdf")) | refine.custom_step

    # Like any pipeline and attachment it's ready with adapters
    claude_message_format = result.claude()
"""

from ..core import Attachment
from ..matchers import pdf_match
from . import processor

@processor(
    match=pdf_match,
    description="Primary PDF processor with clean DSL commands"
)
def pdf_to_llm(att: Attachment) -> Attachment:
    """
    Process PDF files for LLM consumption.
    
    Supports DSL commands (for Attachments() simple API):
    - images: true, false (default: true)
    - format: plain, markdown, code (default: markdown)
      Aliases: text=plain, txt=plain, md=markdown
    - resize_images: 50%, 800x600 (for images)
    """
    
    # Import namespaces properly to get VerbFunction wrappers
    from .. import load, modify, present, refine, attach
    
    # Enhanced pipeline with both text and images
    # Smart filtering will choose based on DSL commands
    return (att 
           | load.pdf_to_pdfplumber 
           | modify.pages  # Optional - only acts if [pages:...] present
           | present.text + present.markdown + present.images 
           | refine.tile_images | refine.resize_images )
