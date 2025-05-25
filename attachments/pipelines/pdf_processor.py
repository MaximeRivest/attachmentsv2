"""
PDF to LLM Pipeline Processor
============================

Complete pipeline for processing PDF files optimized for LLM consumption.
Supports DSL commands for format and focus customization.

DSL Commands:
    [format:markdown|text|structured] - Output format preference
    [focus:text|images|both] - Content focus
    [pages:1-5,10] - Specific pages (inherits from existing modify.pages)
    [resize:50%|800x600] - Image resize specification

Usage:
    # Simple usage (auto-detected by Attachments)
    ctx = Attachments("document.pdf")
    
    # With DSL commands
    ctx = Attachments("report.pdf[format:markdown][focus:both][resize:50%]")
    
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
    - format: markdown, text, structured
    - focus: text, images, both  
    - resize: 50%, 800x600 (for images)
    """
    
    # Import namespaces properly to get VerbFunction wrappers
    from .. import load, modify, present, refine, attach
    
    # Enhanced pipeline with both text and images
    return (att 
           | load.pdf_to_pdfplumber 
           | modify.pages  # Optional - only acts if [pages:...] present
           | present.text + present.markdown + present.images + present.metadata
           | refine.add_headers)


# Example of a specialized processor for the same file type
@processor(
    match=lambda att: att.path.lower().endswith('.pdf'),
    name="programmer_pdf",
    description="Specialized PDF processor for programming documentation and code-heavy PDFs"
)
def programmer_pdf_to_llm(att: Attachment) -> Attachment:
    """
    Specialized processor for PDFs containing code, API docs, programming tutorials.
    Optimized for preserving code formatting and technical structure.
    """
    
    # Import namespaces properly to get VerbFunction wrappers
    from .. import load, modify, present, refine, attach
    
    # Elegant pipeline for code-heavy PDFs - prefer text preservation
    return (att 
           | load.pdf_to_pdfplumber 
           | modify.pages  # Optional - only acts if [pages:...] present
           | present.text + present.metadata  # Focus on text for code preservation
           | refine.add_headers)


@processor(
    match=lambda att: att.path.lower().endswith('.pdf'),
    name="visual_pdf",
    description="PDF processor optimized for visual content - diagrams, charts, images"
)
def visual_pdf_to_llm(att: Attachment) -> Attachment:
    """
    Specialized processor for PDFs with heavy visual content.
    Prioritizes image extraction over text.
    """
    
    # Import namespaces properly to get VerbFunction wrappers
    from .. import load, modify, present, refine, attach
    
    # Visual-focused pipeline
    return (att 
           | load.pdf_to_pdfplumber 
           | modify.pages  # Optional - only acts if [pages:...] present
           | present.pdf_images + present.text + present.metadata  # Images first
           | refine.add_headers)


# Built-in testing
def test_pdf_processor():
    """Test the PDF processor with various configurations."""
    print("🧪 Testing Enhanced PDF Processor")
    
    # Use actual sample PDF from data directory
    from ..data import get_sample_path
    from .. import attach
    
    sample_pdf_path = get_sample_path("sample.pdf")
    print(f"📄 Using sample PDF: {sample_pdf_path}")
    
    # Test basic processing
    result = pdf_to_llm(attach(sample_pdf_path))
    print("✅ Default processing works")
    print(f"📝 Text length: {len(result.text)} characters")
    print(f"🖼️ Images: {len(result.images)} images")
    
    # Test with DSL commands for images
    dsl_att = attach(f"{sample_pdf_path}[format:text][focus:both][resize:50%]")
    result_dsl = pdf_to_llm(dsl_att)
    print("✅ DSL command processing with images works")
    print(f"📝 Text length: {len(result_dsl.text)} characters")
    print(f"🖼️ Images with resize: {len(result_dsl.images)} images")
    
    # Test specialized processors
    prog_result = programmer_pdf_to_llm(attach(sample_pdf_path))
    print("✅ Programmer PDF processor works")
    print(f"📝 Programmer result length: {len(prog_result.text)} characters")
    
    visual_result = visual_pdf_to_llm(attach(sample_pdf_path))
    print("✅ Visual PDF processor works")
    print(f"📝 Visual result text: {len(visual_result.text)} characters")
    print(f"🖼️ Visual result images: {len(visual_result.images)} images")
    
    print("✅ All enhanced PDF processor tests passed!")
    print(f"📊 Sample text preview: {result.text[:100]}...")
    if result.images:
        print(f"🖼️ First image preview: {result.images[0][:50]}...")


if __name__ == "__main__":
    test_pdf_processor() 