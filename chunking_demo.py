#!/usr/bin/env python3
"""
Chunking/Splitting Demo for Attachments Library
===============================================

Demonstrates the new split namespace for chunking documents, data, and web content.
Perfect for handling large documents that need to be processed in smaller pieces for LLMs.

Key Features:
- Text splitting: paragraphs, sentences, characters, tokens, lines
- Document splitting: PDF pages, PowerPoint slides  
- Data splitting: DataFrame rows/columns
- Web content splitting: HTML sections
- Custom splitting with separators
- Vectorized processing of chunks
- LLM-ready chunking for context limits
"""

from attachments import attach, load, split, present, adapt, Attachments, data
import tempfile
import os
import pandas as pd
from pathlib import Path

def create_sample_data():
    """Create sample files for chunking demos."""
    temp_dir = tempfile.mkdtemp()
    
    # 1. Create a long text document (simulating a website or large document)
    long_text_path = os.path.join(temp_dir, "long_document.txt")
    with open(long_text_path, 'w') as f:
        f.write("""# The Future of Artificial Intelligence

Artificial intelligence represents one of the most significant technological advances of our time. The field has evolved rapidly over the past decade, with breakthrough developments in machine learning, natural language processing, and computer vision.

## Current Applications

Today's AI systems are already transforming industries across the board. In healthcare, AI assists with medical diagnosis and drug discovery. In finance, algorithmic trading and fraud detection systems protect billions of dollars in transactions daily.

The automotive industry has embraced AI for autonomous vehicle development. Companies like Tesla, Waymo, and others are racing to perfect self-driving technology that could revolutionize transportation.

## Machine Learning Advances

Deep learning, a subset of machine learning, has been particularly transformative. Neural networks with millions or billions of parameters can now understand and generate human-like text, create realistic images, and even write code.

Large language models like GPT-4, Claude, and others have demonstrated remarkable capabilities in understanding context, following instructions, and engaging in sophisticated conversations.

## Challenges and Limitations

Despite these advances, significant challenges remain. AI systems can exhibit bias, hallucinate false information, and struggle with reasoning about novel situations. Ensuring AI safety and alignment with human values is an ongoing research priority.

The computational requirements for training large models are enormous, raising concerns about energy consumption and environmental impact.

## Future Prospects

Looking ahead, AI is expected to become even more capable and ubiquitous. Advances in areas like robotics, scientific discovery, and creative applications will likely accelerate in the coming years.

However, the path forward requires careful consideration of ethical implications, regulatory frameworks, and the potential impact on employment and society as a whole.

The future of AI holds tremendous promise, but realizing its benefits while mitigating risks will require thoughtful development and deployment of these powerful technologies.""")
    
    # 2. Create a large CSV dataset
    large_csv_path = os.path.join(temp_dir, "sales_data.csv")
    data_rows = []
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    products = ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']
    regions = ['North', 'South', 'East', 'West', 'Central']
    
    for month in months:
        for product in products:
            for region in regions:
                revenue = 10000 + (hash(f"{month}{product}{region}") % 50000)
                units = 100 + (hash(f"{product}{region}{month}") % 500)
                data_rows.append([month, product, region, revenue, units])
    
    df = pd.DataFrame(data_rows, columns=['Month', 'Product', 'Region', 'Revenue', 'Units'])
    df.to_csv(large_csv_path, index=False)
    
    # 3. Create an HTML-like document
    html_doc_path = os.path.join(temp_dir, "article.html")
    with open(html_doc_path, 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head><title>AI Research Article</title></head>
<body>
<h1>Recent Advances in Neural Networks</h1>
<p>This article discusses the latest developments in neural network architectures.</p>

<h2>Transformer Architecture</h2>
<p>The transformer architecture has revolutionized natural language processing. Introduced in "Attention Is All You Need", it relies entirely on attention mechanisms.</p>
<p>Key components include multi-head attention, position encoding, and feed-forward layers.</p>

<h2>Vision Transformers</h2>
<p>Vision Transformers (ViTs) adapt the transformer architecture for computer vision tasks.</p>
<p>They split images into patches and treat them as sequences, achieving excellent results on image classification.</p>

<h2>Large Language Models</h2>
<p>Modern LLMs use transformer architectures with billions of parameters.</p>
<p>They demonstrate emergent capabilities like few-shot learning and reasoning.</p>

<h2>Future Directions</h2>
<p>Research continues into more efficient architectures, better training methods, and improved alignment techniques.</p>
</body>
</html>""")
    
    return temp_dir, long_text_path, large_csv_path, html_doc_path

def demo_text_chunking():
    """Demo 1: Text-based chunking strategies."""
    print("📝 Demo 1: Text Chunking Strategies")
    print("=" * 50)
    
    temp_dir, long_text_path, _, _ = create_sample_data()
    
    print("Original document length:")
    with open(long_text_path, 'r') as f:
        original_text = f.read()
    print(f"  {len(original_text)} characters, {len(original_text.split())} words")
    
    # Load and split into paragraphs
    print("\n1. Paragraph chunking:")
    chunks = attach(long_text_path) | load.text_to_string | split.paragraphs
    print(f"  Split into {len(chunks)} paragraphs")
    for i, chunk in enumerate(chunks.attachments[:3]):  # Show first 3
        print(f"  Paragraph {i+1}: {len(chunk.text)} chars - '{chunk.text[:50]}...'")
    
    # Split by token limits (for LLM contexts)
    print("\n2. Token-based chunking (LLM-friendly):")
    token_chunks = attach(f"{long_text_path}[tokens:200]") | load.text_to_string | split.tokens
    print(f"  Split into {len(token_chunks)} token-limited chunks")
    for i, chunk in enumerate(token_chunks.attachments[:2]):
        estimated_tokens = chunk.metadata.get('estimated_tokens', 0)
        print(f"  Chunk {i+1}: ~{estimated_tokens} tokens - '{chunk.text[:40]}...'")
    
    # Character-based chunking
    print("\n3. Character-based chunking:")
    char_chunks = attach(f"{long_text_path}[characters:500]") | load.text_to_string | split.characters
    print(f"  Split into {len(char_chunks)} character-limited chunks")
    
    # Cleanup
    cleanup_temp_files(temp_dir)

def demo_data_chunking():
    """Demo 2: DataFrame chunking for large datasets."""
    print("\n📊 Demo 2: Data Chunking Strategies")
    print("=" * 50)
    
    temp_dir, _, large_csv_path, _ = create_sample_data()
    
    # Load the CSV to see original size
    original_df = pd.read_csv(large_csv_path)
    print(f"Original dataset: {original_df.shape[0]} rows, {original_df.shape[1]} columns")
    
    # Row-based chunking
    print("\n1. Row-based chunking:")
    row_chunks = attach(f"{large_csv_path}[rows:50]") | load.csv_to_pandas | split.rows
    print(f"  Split into {len(row_chunks)} row chunks")
    for i, chunk in enumerate(row_chunks.attachments[:3]):
        shape = chunk.metadata.get('chunk_shape', (0, 0))
        print(f"  Chunk {i+1}: {shape[0]} rows x {shape[1]} columns")
    
    # Column-based chunking  
    print("\n2. Column-based chunking:")
    col_chunks = attach(f"{large_csv_path}[columns:2]") | load.csv_to_pandas | split.columns
    print(f"  Split into {len(col_chunks)} column chunks")
    for i, chunk in enumerate(col_chunks.attachments):
        cols = chunk.metadata.get('chunk_columns', [])
        print(f"  Chunk {i+1}: columns {cols}")
    
    cleanup_temp_files(temp_dir)

def demo_web_content_chunking():
    """Demo 3: HTML/web content chunking."""
    print("\n🌐 Demo 3: Web Content Chunking")
    print("=" * 50)
    
    temp_dir, _, _, html_doc_path = create_sample_data()
    
    # Load HTML and split by sections
    print("1. Section-based chunking (by headings):")
    try:
        import bs4
        sections = attach(html_doc_path) | load.html_to_bs4 | split.sections
        print(f"  Split into {len(sections)} sections")
        for i, section in enumerate(sections.attachments):
            heading = section.metadata.get('section_heading', 'Unknown')
            level = section.metadata.get('heading_level', 'h?')
            print(f"  Section {i+1} ({level}): '{heading[:40]}...'")
    except ImportError:
        print("  (Skipped - BeautifulSoup4 not available)")
    
    cleanup_temp_files(temp_dir)

def demo_vectorized_processing():
    """Demo 4: Vectorized processing of chunks."""
    print("\n🔄 Demo 4: Vectorized Chunk Processing")
    print("=" * 50)
    
    temp_dir, long_text_path, _, _ = create_sample_data()
    
    # Split into paragraphs and process each one
    print("Processing each paragraph through present.markdown:")
    chunks = (attach(long_text_path) 
             | load.text_to_string 
             | split.paragraphs 
             | present.markdown)  # This gets vectorized automatically
    
    print(f"Processed {len(chunks)} paragraph chunks")
    
    # Show how each chunk now has formatted markdown text
    for i, chunk in enumerate(chunks.attachments[:2]):
        print(f"\nChunk {i+1} markdown preview:")
        print(chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text)
    
    cleanup_temp_files(temp_dir)

def demo_llm_ready_chunking():
    """Demo 5: LLM-ready chunking with Claude/OpenAI."""
    print("\n🤖 Demo 5: LLM-Ready Chunking")
    print("=" * 50)
    
    temp_dir, long_text_path, _, _ = create_sample_data()
    
    # Create chunks optimized for LLM context windows
    print("Creating LLM-optimized chunks:")
    chunks = (attach(f"{long_text_path}[tokens:300]") 
             | load.text_to_string 
             | split.tokens 
             | present.markdown)
    
    print(f"Split document into {len(chunks)} LLM-friendly chunks")
    
    # Process each chunk with LLM (simulate with format preparation)
    print("\nPreparing chunks for LLM analysis:")
    results = []
    for i, chunk in enumerate(chunks.attachments[:3]):  # Process first 3 chunks
        # This would call an actual LLM in real usage
        claude_format = chunk.claude(f"Summarize this section (part {i+1})")
        results.append(claude_format)
        print(f"  Chunk {i+1}: Ready for Claude API ({len(claude_format)} messages)")
    
    print(f"\n💡 Usage pattern for large documents:")
    print("```python")
    print("# Split large document into LLM-friendly chunks")
    print("chunks = (attach('large_doc.txt[tokens:500]')")
    print("         | load.text_to_string | split.tokens | present.markdown)")
    print("")
    print("# Process each chunk with LLM")
    print("summaries = []")
    print("for chunk in chunks:")
    print("    summary = chunk.claude('Summarize this section')")
    print("    summaries.append(summary)")
    print("```")
    
    cleanup_temp_files(temp_dir)

def demo_custom_splitting():
    """Demo 6: Custom splitting patterns."""
    print("\n🛠️ Demo 6: Custom Splitting Patterns")
    print("=" * 50)
    
    # Create a document with custom separators
    temp_dir = tempfile.mkdtemp()
    custom_doc_path = os.path.join(temp_dir, "custom_format.txt")
    with open(custom_doc_path, 'w') as f:
        f.write("""Section Alpha
This is the first section with some content.
It has multiple lines and discusses topic A.

---BREAK---

Section Beta  
This is the second section covering topic B.
It has different information and analysis.

---BREAK---

Section Gamma
The final section covers advanced topics.
It includes conclusions and recommendations.""")
    
    # Split using custom separator
    print("Custom separator splitting (---BREAK---):")
    custom_chunks = (attach(f"{custom_doc_path}[custom:---BREAK---]") 
                    | load.text_to_string 
                    | split.custom)
    
    print(f"Split into {len(custom_chunks)} custom sections")
    for i, chunk in enumerate(custom_chunks.attachments):
        preview = chunk.text.split('\n')[0]  # First line as preview
        print(f"  Section {i+1}: '{preview}'")
    
    cleanup_temp_files(temp_dir)

def demo_advanced_patterns():
    """Demo 7: Advanced chunking patterns and workflows."""
    print("\n🎯 Demo 7: Advanced Chunking Patterns")
    print("=" * 50)
    
    temp_dir, long_text_path, large_csv_path, _ = create_sample_data()
    
    # Pattern 1: Multi-level chunking
    print("1. Multi-level chunking (paragraphs → sentences):")
    
    # First split into paragraphs, then split each paragraph into sentences
    para_chunks = attach(long_text_path) | load.text_to_string | split.paragraphs
    
    all_sentences = []
    for para_chunk in para_chunks.attachments[:2]:  # First 2 paragraphs
        # Split this paragraph into sentences
        sentences = para_chunk | split.sentences
        # Handle both AttachmentCollection and Attachment returns
        if hasattr(sentences, 'attachments'):
            all_sentences.extend(sentences.attachments)
        else:
            all_sentences.append(sentences)
    
    print(f"  From {len(para_chunks)} paragraphs → {len(all_sentences)} sentences")
    
    # Pattern 2: Filtered chunking
    print("\n2. Filtered chunking (only long paragraphs):")
    long_paragraphs = []
    for chunk in para_chunks.attachments:
        if len(chunk.text) > 200:  # Only keep long paragraphs
            long_paragraphs.append(chunk)
    
    print(f"  Filtered to {len(long_paragraphs)} paragraphs over 200 characters")
    
    # Pattern 3: Chunk metadata analysis
    print("\n3. Chunk metadata analysis:")
    token_chunks = attach(f"{long_text_path}[tokens:150]") | load.text_to_string | split.tokens
    
    total_estimated_tokens = sum(
        chunk.metadata.get('estimated_tokens', 0) 
        for chunk in token_chunks.attachments
    )
    print(f"  {len(token_chunks)} chunks with ~{total_estimated_tokens} total estimated tokens")
    
    # Pattern 4: Mixed content chunking
    print("\n4. Mixed content type processing:")
    print("  Text chunks → summarize, Data chunks → analyze")
    
    # This would typically involve multiple file types
    text_summary = "Text chunks would be summarized with LLM"
    data_analysis = "Data chunks would be analyzed statistically" 
    print(f"  {text_summary}")
    print(f"  {data_analysis}")
    
    cleanup_temp_files(temp_dir)

def cleanup_temp_files(temp_dir):
    """Clean up temporary files."""
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

def main():
    """Run all chunking demos."""
    print("🧩 Attachments Library: Chunking/Splitting Demo")
    print("=" * 60)
    print("Perfect for handling large documents with LLM context limits!\n")
    
    try:
        demo_text_chunking()
        demo_data_chunking()
        demo_web_content_chunking()
        demo_vectorized_processing()
        demo_llm_ready_chunking()
        demo_custom_splitting()
        demo_advanced_patterns()
        
        print("\n" + "=" * 60)
        print("✅ All chunking demos completed successfully!")
        
        print("\n🎯 Key Chunking Strategies Demonstrated:")
        print("• 📝 Text: paragraphs, sentences, characters, tokens, lines")
        print("• 📄 Documents: PDF pages, PowerPoint slides")
        print("• 📊 Data: DataFrame rows/columns")
        print("• 🌐 Web: HTML sections by headings")
        print("• 🛠️ Custom: any separator pattern")
        
        print("\n💡 LLM Integration Patterns:")
        print("• split.tokens(500) - Respect LLM context limits")
        print("• Vectorized processing - Each chunk gets processed")
        print("• chunk.claude() / chunk.openai() - Direct API integration")
        print("• Metadata tracking - Monitor chunk sizes and positions")
        
        print("\n🚀 Usage Examples:")
        print("```python")
        print("# Basic chunking")
        print("chunks = attach('doc.txt') | load.text_to_string | split.paragraphs")
        print("")
        print("# LLM-ready chunking with DSL")
        print("chunks = attach('doc.txt[tokens:500]') | load.text_to_string | split.tokens")
        print("")
        print("# Process each chunk")
        print("for chunk in chunks:")
        print("    result = chunk.claude('Analyze this section')")
        print("```")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 