#!/usr/bin/env python3
"""
Simplified Attachments API Demo
==============================

Demonstrates the one-line file-to-LLM interface:
- Attachments(*paths) for automatic processing
- str(ctx) for prompt-engineered text  
- ctx.images for base64 images
- Direct API integration

Mimics the exact usage patterns from the user's examples.
"""

from attachments import Attachments, process
import tempfile
import os
from PIL import Image
import csv

def create_sample_files():
    """Create sample files for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # 1. Create a text file (simulating a report)
    report_path = os.path.join(temp_dir, "report.txt")
    with open(report_path, 'w') as f:
        f.write("""# Project Report
        
This is a comprehensive analysis of our quarterly results.

## Key Findings
- Revenue increased by 15%
- Customer satisfaction improved to 92%
- New product launch exceeded expectations

## Recommendations
- Expand marketing budget
- Hire additional support staff
- Invest in R&D for next quarter

The data supports continued growth and strategic investments.""")
    
    # 2. Create a CSV file (simulating data)
    csv_path = os.path.join(temp_dir, "data.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Month', 'Revenue', 'Customers', 'Satisfaction'])
        writer.writerow(['Jan', '125000', '450', '89'])
        writer.writerow(['Feb', '135000', '478', '91'])
        writer.writerow(['Mar', '142000', '502', '92'])
    
    # 3. Create a sample image
    img_path = os.path.join(temp_dir, "chart.png")
    img = Image.new('RGB', (400, 300), color='lightblue')
    img.save(img_path)
    
    return temp_dir, report_path, csv_path, img_path

def demo_basic_usage():
    """Demo 1: Basic one-line usage as shown in user examples."""
    print("🚀 Demo 1: Basic One-Line Usage")
    print("=" * 50)
    
    temp_dir, report_path, csv_path, img_path = create_sample_files()
    
    # The exact pattern from user's example
    print("Creating: Attachments('report.txt', 'data.csv', 'chart.png')")
    ctx = Attachments(report_path, csv_path, img_path)
    
    print(f"✅ Processed: {ctx}")
    print(f"📄 Text length: {len(str(ctx))} characters")
    print(f"🖼️ Images: {len(ctx.images)} images")
    
    # Show the actual outputs
    print("\n📖 Text output (first 200 chars):")
    print(str(ctx)[:200] + "..." if len(str(ctx)) > 200 else str(ctx))
    
    print(f"\n🖼️ Images ready for LLM: {len(ctx.images)} base64 strings")
    
    # Cleanup
    for path in [report_path, csv_path, img_path]:
        os.remove(path)
    os.rmdir(temp_dir)

def demo_dsl_commands():
    """Demo 2: DSL commands in file paths."""
    print("\n🎛️ Demo 2: DSL Commands")
    print("=" * 50)
    
    temp_dir, report_path, csv_path, img_path = create_sample_files()
    
    # Using DSL commands (simulating the user's examples)
    print("Creating: Attachments('report.txt[truncate:500]', 'chart.png[rotate:90]')")
    
    # Add DSL commands to the paths
    report_with_dsl = f"{report_path}[truncate:500]"
    img_with_dsl = f"{img_path}[rotate:90]"
    
    ctx = Attachments(report_with_dsl, img_with_dsl)
    
    print(f"✅ Processed: {ctx}")
    print(f"📄 Text (truncated): {len(str(ctx))} characters")
    print(f"🖼️ Images (rotated): {len(ctx.images)} images")
    
    # Cleanup
    for path in [report_path, csv_path, img_path]:
        os.remove(path)
    os.rmdir(temp_dir)

def demo_api_integration():
    """Demo 3: Direct API integration."""
    print("\n🤖 Demo 3: Direct API Integration")
    print("=" * 50)
    
    temp_dir, report_path, csv_path, img_path = create_sample_files()
    
    ctx = Attachments(report_path, csv_path, img_path)
    
    print("Direct API outputs:")
    
    # Claude API format
    claude_format = ctx.claude("Analyze this data and provide insights")
    print(f"📤 Claude API: {len(claude_format)} messages ready")
    print(f"   First message keys: {list(claude_format[0].keys())}")
    
    # OpenAI API format  
    openai_format = ctx.openai("Summarize the key findings")
    print(f"📤 OpenAI API: {len(openai_format)} messages ready")
    print(f"   Content types: {[c['type'] for c in openai_format[0]['content']]}")
    
    # Cleanup
    for path in [report_path, csv_path, img_path]:
        os.remove(path)
    os.rmdir(temp_dir)

def demo_convenience_function():
    """Demo 4: Even simpler process() function."""
    print("\n⚡ Demo 4: Convenience Function")
    print("=" * 50)
    
    temp_dir, report_path, csv_path, img_path = create_sample_files()
    
    # Using the process() convenience function
    print("Using: process('report.txt', 'data.csv')")
    ctx = process(report_path, csv_path)
    
    print(f"✅ Processed: {len(ctx)} files")
    print(f"📄 Combined text: {len(str(ctx))} chars")
    print(f"📊 Metadata: {ctx.metadata['file_count']} files processed")
    
    # Cleanup
    for path in [report_path, csv_path, img_path]:
        os.remove(path)
    os.rmdir(temp_dir)

def demo_error_handling():
    """Demo 5: Graceful error handling."""
    print("\n🛡️ Demo 5: Error Handling")
    print("=" * 50)
    
    # Mix of valid and invalid files
    temp_dir, report_path, csv_path, img_path = create_sample_files()
    
    ctx = Attachments(
        report_path,          # Valid
        "nonexistent.pdf",    # Invalid
        csv_path,             # Valid
        "another_missing.jpg" # Invalid
    )
    
    print(f"✅ Processed: {len(ctx)} items (including errors)")
    print(f"📄 Text includes error messages: {len(str(ctx))} chars")
    
    # Show how errors are handled
    for i, att in enumerate(ctx.attachments):
        status = "✅ Success" if "Could not process" not in att.text else "⚠️ Error"
        print(f"  File {i+1}: {status} - {att.path}")
    
    # Cleanup
    for path in [report_path, csv_path, img_path]:
        os.remove(path)
    os.rmdir(temp_dir)

def main():
    """Run all demos showing the simplified API."""
    print("🚀 Simplified Attachments API Demo")
    print("==================================")
    print("One-line file → LLM context conversion\n")
    
    try:
        demo_basic_usage()
        demo_dsl_commands()
        demo_api_integration()
        demo_convenience_function()
        demo_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("\n🎯 Key Benefits Demonstrated:")
        print("• ⚡ One-line processing: Attachments('file1', 'file2')")
        print("• 📄 str(ctx) → prompt-engineered text ready for LLMs")
        print("• 🖼️ ctx.images → base64 images ready for vision models")
        print("• 🎛️ DSL commands: 'file.pdf[pages:1-3][truncate:1000]'")
        print("• 🤖 Direct API: ctx.claude() / ctx.openai()")
        print("• 🛡️ Graceful error handling for missing/invalid files")
        print("• 🔧 Built on the full grammar system underneath")
        
        print("\n💡 Usage Summary:")
        print("pip install attachments")
        print("from attachments import Attachments")
        print("ctx = Attachments('report.pdf', 'photo.jpg[rotate:90]')")
        print("text = str(ctx)       # All extracted text")
        print("images = ctx.images   # List[str] base64 PNGs")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 