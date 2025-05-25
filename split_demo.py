#!/usr/bin/env python3
"""
Simple Split/Chunking Demo
==========================

Quick examples of the new split functionality for chunking large documents.
Perfect for LLM context limits and processing large files.

Usage:
    python split_demo.py
"""

from attachments import attach, load, split, present, Attachments, data
import tempfile
import os

def create_sample_text():
    """Create a sample text file for demonstration."""
    temp_dir = tempfile.mkdtemp()
    sample_path = os.path.join(temp_dir, "sample_document.txt")
    
    with open(sample_path, 'w') as f:
        f.write("""# Artificial Intelligence Overview

Artificial intelligence (AI) is transforming every industry. From healthcare to finance, AI systems are becoming essential tools for modern businesses.

## Machine Learning Basics

Machine learning is a subset of AI that enables computers to learn without explicit programming. It uses algorithms to identify patterns in data and make predictions.

Deep learning, using neural networks, has been particularly successful in areas like image recognition and natural language processing.

## Current Applications

Today's AI applications include:
- Autonomous vehicles
- Medical diagnosis systems  
- Financial fraud detection
- Virtual assistants
- Recommendation systems

## Future Prospects

The future of AI looks promising with advances in:
- Quantum computing integration
- Enhanced natural language understanding
- Improved robotics capabilities
- Better human-AI collaboration

These developments will likely accelerate AI adoption across industries and create new possibilities for innovation.""")
    
    return temp_dir, sample_path

def demo_basic_chunking():
    """Demonstrate basic chunking patterns."""
    print("🧩 Basic Chunking Patterns")
    print("=" * 40)
    
    temp_dir, sample_path = create_sample_text()
    
    # 1. Paragraph chunking
    print("\n1. Split by paragraphs:")
    chunks = attach(sample_path) | load.text_to_string | split.paragraphs
    print(f"   → {len(chunks)} paragraphs")
    for i, chunk in enumerate(chunks.attachments[:3]):
        preview = chunk.text.split('\n')[0][:50]
        print(f"   Paragraph {i+1}: {preview}...")
    
    # 2. Token-based chunking (LLM-friendly)
    print("\n2. Split by tokens (LLM-friendly):")
    token_chunks = attach(f"{sample_path}[tokens:200]") | load.text_to_string | split.tokens
    print(f"   → {len(token_chunks)} token-limited chunks")
    for i, chunk in enumerate(token_chunks.attachments):
        estimated_tokens = chunk.metadata.get('estimated_tokens', 0)
        print(f"   Chunk {i+1}: ~{estimated_tokens} tokens")
    
    # 3. Custom splitting
    print("\n3. Custom splitting:")
    # Add some custom separators to the text
    with open(sample_path, 'a') as f:
        f.write("\n\n---SECTION---\n\nBonus Section\nThis is additional content added for custom splitting demonstration.")
    
    custom_chunks = attach(f"{sample_path}[custom:---SECTION---]") | load.text_to_string | split.custom
    print(f"   → {len(custom_chunks)} custom sections")
    
    # Cleanup
    os.remove(sample_path)
    os.rmdir(temp_dir)

def demo_llm_ready():
    """Demonstrate LLM-ready chunking workflow."""
    print("\n\n🤖 LLM-Ready Chunking Workflow")
    print("=" * 40)
    
    temp_dir, sample_path = create_sample_text()
    
    # Create LLM-optimized chunks
    print("\n1. Creating LLM-optimized chunks:")
    chunks = (attach(f"{sample_path}[tokens:150]") 
             | load.text_to_string 
             | split.tokens 
             | present.markdown)
    
    print(f"   → Split into {len(chunks)} chunks")
    
    # Simulate LLM processing
    print("\n2. Processing each chunk (simulated):")
    for i, chunk in enumerate(chunks.attachments[:2]):  # Show first 2
        # In real usage, you'd do: chunk.claude("Summarize this section")
        estimated_tokens = chunk.metadata.get('estimated_tokens', 0)
        print(f"   Chunk {i+1}: ~{estimated_tokens} tokens → Ready for LLM")
        print(f"   Preview: {chunk.text[:60]}...")
    
    print(f"\n💡 Real usage pattern:")
    print("```python")
    print("for chunk in chunks:")
    print('    summary = chunk.claude("Summarize this section")')
    print("    print(f'Summary: {summary}')")
    print("```")
    
    # Cleanup
    os.remove(sample_path)
    os.rmdir(temp_dir)

def demo_dsl_commands():
    """Demonstrate DSL command patterns."""
    print("\n\n🎛️ DSL Command Patterns")
    print("=" * 40)
    
    temp_dir, sample_path = create_sample_text()
    
    print("\nDSL commands embed chunking parameters in file paths:")
    
    examples = [
        ("Basic tokens", f"{sample_path}[tokens:100]"),
        ("Character limit", f"{sample_path}[characters:500]"),
        ("Line chunks", f"{sample_path}[lines:10]"),
        ("Custom separator", f"{sample_path}[custom:##]")
    ]
    
    for name, path_with_dsl in examples:
        print(f"\n{name}: {os.path.basename(path_with_dsl)}")
        print(f"   → DSL commands parsed from path automatically")
    
    # Cleanup
    os.remove(sample_path)
    os.rmdir(temp_dir)

def demo_simple_api():
    """Demonstrate how chunking works with the simple Attachments API."""
    print("\n\n⚡ Simple API Integration")
    print("=" * 40)
    
    print("\nChunking also works with the simple Attachments() API:")
    print("\nExample workflow:")
    print("```python")
    print("# Option 1: Use grammar system for chunking")
    print("chunks = attach('large_doc.txt[tokens:500]') | load.text_to_string | split.tokens")
    print("")
    print("# Option 2: Use simple API for individual files")
    print("for chunk in chunks:")
    print("    ctx = Attachments() # Can process individual chunks")
    print("    ctx.attachments = [chunk]")
    print("    result = ctx.claude('Analyze this section')")
    print("```")

def main():
    """Run all chunking demonstrations."""
    print("🔗 Attachments Library: Split/Chunking Demo")
    print("=" * 50)
    print("Demonstrating document chunking for LLM processing\n")
    
    try:
        demo_basic_chunking()
        demo_llm_ready()
        demo_dsl_commands()
        demo_simple_api()
        
        print("\n" + "=" * 50)
        print("✅ All demos completed!")
        
        print("\n🎯 Key Takeaways:")
        print("• split.paragraphs, split.tokens, split.characters - text chunking")
        print("• split.pages (PDF), split.slides (PowerPoint) - document chunking") 
        print("• split.rows, split.columns (DataFrames) - data chunking")
        print("• DSL commands: [tokens:500], [characters:1000], [custom:---]")
        print("• Vectorized processing: operations apply to each chunk")
        print("• LLM integration: chunk.claude(), chunk.openai()")
        
        print("\n🚀 Next Steps:")
        print("• Try: python chunking_demo.py (comprehensive demo)")
        print("• Explore: attachments/split.py (implementation)")
        print("• Integrate: Use chunking in your LLM projects!")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 