#!/usr/bin/env python3
"""
Automated Adapter Example
========================

Demonstrates how new adapters automatically become available on Attachments objects.
No manual coding required!
"""

from attachments import Attachments, adapter

# 🎯 Step 1: Create a new adapter (any framework you want!)
@adapter
def langchain(att, prompt="", temperature=0.7):
    """Custom LangChain adapter."""
    return {
        "framework": "langchain", 
        "prompt": prompt,
        "temperature": temperature,
        "content": att.text[:100] + "..." if len(att.text) > 100 else att.text,
        "ready": "for LangChain processing"
    }

@adapter  
def huggingface(att, model="gpt2", max_tokens=150):
    """Custom HuggingFace adapter."""
    return {
        "framework": "huggingface",
        "model": model,
        "max_tokens": max_tokens,
        "input_text": att.text,
        "ready": "for HuggingFace inference"
    }

@adapter
def custom_analytics(att, metrics=["sentiment", "topics"]):
    """Custom analytics adapter."""
    return {
        "framework": "custom_analytics",
        "text_length": len(att.text) if att.text else 0,
        "word_count": len(att.text.split()) if att.text else 0,
        "requested_metrics": metrics,
        "ready": "for custom analytics"
    }

def main():
    """Demonstrate automatic adapter availability."""
    print("🤖 Automated Adapter System Demo")
    print("=" * 40)
    
    # Create some content
    ctx = Attachments()
    # Add some sample text manually for the demo
    from attachments.core import Attachment
    sample = Attachment("sample.txt")
    sample.text = "This is sample text for testing our automated adapter system. It shows how any new adapter automatically becomes available on Attachments objects without manual coding."
    ctx.attachments = [sample]
    
    print("📄 Sample content loaded")
    print(f"   Text: {len(sample.text)} characters")
    
    print("\n🔧 Built-in adapters work automatically:")
    print(f"✅ ctx.claude() → {type(ctx.claude('Analyze this'))}")
    print(f"✅ ctx.openai() → {type(ctx.openai('Summarize this'))}")
    
    print("\n🎯 Custom adapters work automatically too:")
    
    # All these adapters are now automatically available!
    langchain_result = ctx.langchain("Process with LangChain", temperature=0.8)
    print(f"✅ ctx.langchain() → {langchain_result}")
    
    hf_result = ctx.huggingface("text-davinci-003", max_tokens=200)
    print(f"✅ ctx.huggingface() → {hf_result}")
    
    analytics_result = ctx.custom_analytics(["sentiment", "keywords", "summary"])
    print(f"✅ ctx.custom_analytics() → {analytics_result}")
    
    print("\n💡 Key Point:")
    print("   Just add @adapter to any function → automatically available!")
    print("   No manual method coding in Attachments class required!")
    
    print("\n🚀 Usage Pattern:")
    print("```python")
    print("@adapter")
    print("def my_framework(att, param1, param2='default'):")
    print("    return {'processed': att.text}")
    print("")
    print("# Automatically available!")  
    print("ctx = Attachments('file.txt')")
    print("result = ctx.my_framework('value', param2='custom')")
    print("```")

if __name__ == "__main__":
    main() 