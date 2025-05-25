#!/usr/bin/env python3
"""
Specialized Processors Demo
===========================

Demonstrates the key distinction between:
1. Primary processors (no name) - automatically used by Attachments()
2. Named processors (with name) - only available via processors.name

This shows how multiple contributors can create specialized processors for the same
file type without conflicting with the simple API.
"""

from attachments import Attachments, attach, processors, list_available_processors
import tempfile
import os

def create_test_files():
    """Create test PDF files for demonstration."""
    temp_dir = tempfile.mkdtemp()
    
    files = {
        'research_paper.pdf': "Academic research paper with citations and methodology sections.",
        'contract.pdf': "Legal contract with clauses, terms, and conditions.",
        'quarterly_report.pdf': "Financial report with revenue tables and profit charts.",
        'medical_record.pdf': "Medical document with patient data and clinical notes."
    }
    
    file_paths = {}
    for filename, content in files.items():
        path = os.path.join(temp_dir, filename)
        with open(path, 'w') as f:
            f.write(content)
        file_paths[filename] = path
    
    return temp_dir, file_paths

def demo_simple_api_vs_specialized():
    """Show the difference between simple API and specialized processors."""
    print("🔗 Specialized Processors Demo")
    print("=" * 60)
    
    temp_dir, files = create_test_files()
    
    print("📋 Available Processors:")
    try:
        available = list_available_processors()
        print(f"   Primary processors: {list(available['primary_processors'].keys())}")
        print(f"   Named processors: {list(available['named_processors'].keys())}")
    except Exception as e:
        print(f"   Note: {e}")
    
    print(f"\n🤖 Simple API (uses primary processor automatically):")
    print("   Attachments() will use the primary processor for each file type")
    
    # Simple API - uses primary processor automatically
    for filename, path in files.items():
        try:
            ctx = Attachments(path)
            print(f"   ✅ {filename}: {len(ctx.attachments)} attachment(s) processed")
        except Exception as e:
            print(f"   📝 {filename}: {e}")
    
    print(f"\n🎯 Specialized Processors (explicit access only):")
    print("   These are NOT used by Attachments() - must be called explicitly")
    
    # Specialized processors - explicit access only
    specialized_examples = [
        ("academic_pdf", files['research_paper.pdf'], "Academic paper processor"),
        ("legal_pdf", files['contract.pdf'], "Legal document processor"),
        ("financial_pdf", files['quarterly_report.pdf'], "Financial report processor"),
        ("medical_pdf", files['medical_record.pdf'], "Medical document processor")
    ]
    
    for processor_name, file_path, description in specialized_examples:
        try:
            # Access specialized processor explicitly
            processor_fn = getattr(processors, processor_name)
            result = processor_fn(attach(file_path))
            print(f"   ✅ processors.{processor_name}(): {description}")
        except AttributeError:
            print(f"   📝 processors.{processor_name}(): Not available (would be registered when imported)")
        except Exception as e:
            print(f"   📝 processors.{processor_name}(): {e}")
    
    print(f"\n🔑 Key Architecture Benefits:")
    print("   • Simple API: Attachments() uses best general-purpose processor")
    print("   • Specialized access: processors.name() for domain-specific needs")
    print("   • No conflicts: Multiple processors can handle same file type")
    print("   • Contributor-friendly: Add specialized processors without breaking simple API")
    
    print(f"\n📝 Usage Patterns:")
    print("```python")
    print("# Simple API - automatic processor selection")
    print("ctx = Attachments('document.pdf')  # Uses primary PDF processor")
    print("")
    print("# Specialized processors - explicit selection")
    print("academic = processors.academic_pdf(attach('paper.pdf'))")
    print("legal = processors.legal_pdf(attach('contract.pdf'))")
    print("financial = processors.financial_pdf(attach('report.pdf'))")
    print("")
    print("# Mix with verb system")
    print("result = processors.academic_pdf(attach('paper.pdf')) | refine.truncate")
    print("```")
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

def demo_contributor_workflow():
    """Show how contributors can add specialized processors."""
    print(f"\n👥 Contributor Workflow:")
    print("=" * 60)
    
    print("How to add a specialized processor:")
    print("""
1. Create processor file: pipelines/domain_processors.py

@processor(
    match=lambda att: att.path.endswith('.pdf'),
    name="academic_pdf",  # Named = explicit access only
    description="Specialized for academic papers"
)
def academic_pdf_processor(att: Attachment) -> Attachment:
    # Academic-specific pipeline
    return (att | load.pdf_to_pdfplumber 
              | present.markdown + present.metadata
              | refine.add_headers)

2. Import in __init__.py:
from .pipelines import domain_processors

3. Available immediately:
result = processors.academic_pdf(attach("paper.pdf"))
""")
    
    print("✅ Benefits:")
    print("   • No conflicts with existing processors")
    print("   • Simple API remains unchanged")
    print("   • Domain experts can optimize for their use cases")
    print("   • Power users get specialized tools")

if __name__ == "__main__":
    demo_simple_api_vs_specialized()
    demo_contributor_workflow() 