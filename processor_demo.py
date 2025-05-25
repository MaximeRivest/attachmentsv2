#!/usr/bin/env python3
"""
Processor System Demo
====================

Demonstrates the new pipeline processor system that allows contributors to create
complete file-to-LLM processors with automatic registration and DSL support.

Key Features:
- Primary processors auto-registered for simple API
- Named specialized processors for niche use cases  
- DSL commands: [format:markdown|text|structured], [focus:text|images|both]
- Mixing processors with verbs for power users
- Automatic fallback to universal pipeline
"""

from attachments import Attachments, attach, processors, processor, refine
from attachments.core import Attachment
import tempfile
import os

def create_sample_files():
    """Create sample files for testing processors."""
    temp_dir = tempfile.mkdtemp()
    
    # Create a sample PDF-like content (simulate since we don't have real PDFs)
    pdf_path = os.path.join(temp_dir, "sample.pdf")
    with open(pdf_path, 'w') as f:
        f.write("This is simulated PDF content for testing the processor system.")
    
    # Create a non-PDF file to show fallback
    text_path = os.path.join(temp_dir, "sample.txt")
    with open(text_path, 'w') as f:
        f.write("This is a regular text file that will use the universal pipeline fallback.")
    
    return temp_dir, pdf_path, text_path

def demo_simple_api_with_processors():
    """Demo 1: Simple API automatically uses processors."""
    print("🤖 Demo 1: Simple API with Automatic Processors")
    print("=" * 60)
    
    temp_dir, pdf_path, text_path = create_sample_files()
    
    print("1. PDF files automatically use PDF processor:")
    ctx_pdf = Attachments(pdf_path)
    print(f"   ✅ Processed: {len(ctx_pdf.attachments)} attachments")
    print(f"   📄 Has text: {bool(ctx_pdf.attachments[0].text)}")
    
    print("\n2. PDF with DSL commands:")
    pdf_with_dsl = f"{pdf_path}[format:markdown][focus:text]"
    ctx_dsl = Attachments(pdf_with_dsl)
    print(f"   ✅ Processed with DSL: {len(ctx_dsl.attachments)} attachments")
    print(f"   🎛️ Commands parsed: {ctx_dsl.attachments[0].commands}")
    
    print("\n3. Non-PDF files use universal fallback:")
    ctx_text = Attachments(text_path)
    print(f"   ✅ Fallback processing: {len(ctx_text.attachments)} attachments")
    
    # Cleanup
    cleanup_files(temp_dir)

def demo_explicit_processor_access():
    """Demo 2: Explicit processor access for power users."""
    print("\n🔧 Demo 2: Explicit Processor Access")
    print("=" * 60)
    
    temp_dir, pdf_path, text_path = create_sample_files()
    
    print("1. Access primary PDF processor directly:")
    result = processors.pdf_to_llm(attach(pdf_path))
    print(f"   ✅ Direct access: {type(result)}")
    print(f"   📄 Has text: {bool(result.text)}")
    
    print("\n2. Access specialized processor:")
    try:
        result_specialized = processors.programmer_pdf(attach(pdf_path))
        print(f"   ✅ Specialized processor: {type(result_specialized)}")
        print(f"   📄 Has text: {bool(result_specialized.text)}")
    except AttributeError as e:
        print(f"   📝 Note: {e}")
        print("   (This is expected - processors namespace shows available processors)")
    
    print("\n3. List available processors:")
    try:
        from attachments import list_available_processors
        available = list_available_processors()
        print(f"   📋 Primary processors: {list(available['primary_processors'].keys())}")
        print(f"   📋 Named processors: {list(available['named_processors'].keys())}")
    except Exception as e:
        print(f"   📝 Processor listing: {e}")
    
    # Cleanup
    cleanup_files(temp_dir)

def demo_mixing_with_verbs():
    """Demo 3: Mixing processors with verbs."""
    print("\n🔗 Demo 3: Mixing Processors with Verbs")
    print("=" * 60)
    
    temp_dir, pdf_path, text_path = create_sample_files()
    
    print("1. Processor + refiner:")
    result = processors.pdf_to_llm(attach(pdf_path)) | refine.add_headers
    print(f"   ✅ Mixed pipeline: {type(result)}")
    print(f"   📄 Has text: {bool(result.text)}")
    
    print("\n2. Complex mixing pattern:")
    # This shows the power of the verb system combined with processors
    try:
        complex_result = (processors.pdf_to_llm(attach(pdf_path))
                         | refine.add_headers 
                         | refine.truncate)
        print(f"   ✅ Complex mixing: {type(complex_result)}")
        print(f"   📄 Final text length: {len(complex_result.text) if complex_result.text else 0}")
    except Exception as e:
        print(f"   📝 Complex mixing note: {e}")
    
    # Cleanup
    cleanup_files(temp_dir)

def demo_dsl_commands():
    """Demo 4: DSL command variations."""
    print("\n🎛️ Demo 4: DSL Command Variations")
    print("=" * 60)
    
    temp_dir, pdf_path, text_path = create_sample_files()
    
    dsl_examples = [
        f"{pdf_path}[format:markdown]",
        f"{pdf_path}[format:text][focus:images]", 
        f"{pdf_path}[format:structured][focus:both]",
        f"{pdf_path}[pages:1-3][format:markdown]",
        f"{pdf_path}[focus:text][format:text]",
        f"{pdf_path}[format:structured][focus:both][pages:1-2]"
    ]
    
    for i, dsl_path in enumerate(dsl_examples, 1):
        print(f"{i}. Testing: {os.path.basename(dsl_path)}")
        try:
            ctx = Attachments(dsl_path)
            commands = ctx.attachments[0].commands if ctx.attachments else {}
            print(f"   ✅ Commands: {commands}")
        except Exception as e:
            print(f"   📝 Note: {e}")
    
    # Cleanup
    cleanup_files(temp_dir)

def demo_contributor_pattern():
    """Demo 5: How contributors can add processors."""
    print("\n👥 Demo 5: Contributor Pattern")
    print("=" * 60)
    
    print("Example of how contributors can add processors:")
    print("""
# Step 1: Create a new processor file (e.g., pipelines/docx_processor.py)
@processor(match=lambda att: att.path.endswith('.docx'))
def docx_to_llm(att: Attachment) -> Attachment:
    '''Primary DOCX processor with format and focus options.'''
    
    format_type = att.commands.get('format', 'markdown')
    focus_type = att.commands.get('focus', 'both')
    
    # Load → Process → Present → Refine
    return (att 
           | load.docx_to_python_docx
           | present.text + present.images
           | refine.add_headers)

@processor(match=lambda att: att.path.endswith('.docx'), name="legal_docx")  
def legal_docx_to_llm(att: Attachment) -> Attachment:
    '''Specialized for legal documents.'''
    # Legal-specific processing...
    return process_legal_document(att)

# Step 2: Import in __init__.py (automatic registration)
from .pipelines import docx_processor

# Step 3: Automatically available!
ctx = Attachments("contract.docx")  # Uses docx_to_llm
result = processors.legal_docx(attach("contract.docx"))  # Explicit access
""")
    
    print("✅ This pattern makes it easy for contributors to:")
    print("   • Create complete file-to-LLM pipelines")
    print("   • Support DSL commands for customization")
    print("   • Add specialized processors for niche use cases")
    print("   • Maintain compatibility with existing verb system")

def cleanup_files(temp_dir):
    """Clean up temporary files."""
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

def main():
    """Run all processor demos."""
    print("🔗 Attachments Library: Processor System Demo")
    print("=" * 70)
    print("Demonstrating complete file-to-LLM pipeline processors\n")
    
    try:
        demo_simple_api_with_processors()
        demo_explicit_processor_access()
        demo_mixing_with_verbs()
        demo_dsl_commands()
        demo_contributor_pattern()
        
        print("\n" + "=" * 70)
        print("✅ All processor demos completed!")
        
        print("\n🎯 Key Architecture Benefits:")
        print("• 🤖 Simple API: Automatically uses best processor for each file type")
        print("• 🔧 Power Users: Direct access to specialized processors")
        print("• 🔗 Composability: Mix processors with existing verb system")
        print("• 🎛️ DSL Commands: [format:markdown|text|structured], [focus:text|images|both]")
        print("• 👥 Contributor-Friendly: One file per processor with auto-registration")
        
        print("\n🚀 Usage Patterns:")
        print("```python")
        print("# Simple API (auto-detects processor)")
        print("ctx = Attachments('document.pdf[format:markdown][focus:both]')")
        print("")
        print("# Explicit processor access")
        print("result = processors.pdf_to_llm(attach('doc.pdf'))")
        print("")
        print("# Mix with verb system")
        print("result = processors.pdf_to_llm(attach('doc.pdf')) | refine.custom_step")
        print("")
        print("# Specialized processors")
        print("result = processors.programmer_pdf(attach('paper.pdf'))")
        print("```")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 