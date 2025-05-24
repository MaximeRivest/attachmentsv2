#!/usr/bin/env python3
"""
Vectorized Pipeline Demo
======================

Demonstrates vectorization and collection handling in the attachments library.
Shows how pipelines automatically vectorize over collections and aggregate results.

Key Features:
- AttachmentCollection for multiple files
- Auto-vectorization of modify/present operations  
- Reduction operations (refine.tile_images)
- Final adaptation of aggregated results
"""

from attachments import attach, load, modify, present, refine, adapt, AttachmentCollection, Attachment
import tempfile
import os
import zipfile
from PIL import Image

def create_sample_zip():
    """Create a sample ZIP file with test images."""
    # Create temp directory and images
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "sample_images.zip")
    
    # Create sample images
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]  # Red, Green, Blue, Yellow
    image_paths = []
    
    for i, color in enumerate(colors):
        img = Image.new('RGB', (200, 200), color)
        img_path = os.path.join(temp_dir, f"image_{i+1}.png")
        img.save(img_path)
        image_paths.append(img_path)
    
    # Create ZIP file
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for img_path in image_paths:
            zf.write(img_path, os.path.basename(img_path))
    
    # Cleanup individual files
    for img_path in image_paths:
        os.remove(img_path)
    
    return zip_path

def demo_basic_vectorization():
    """Demo 1: Basic vectorization of operations."""
    print("🔄 Demo 1: Basic Vectorization")
    print("=" * 50)
    
    zip_path = create_sample_zip()
    
    # Load ZIP into collection
    print(f"Loading ZIP: {zip_path}")
    collection = attach(zip_path) | load.zip_to_images
    print(f"Loaded: {collection}")
    print(f"Individual attachments: {len(collection.attachments)}")
    
    # Vectorized present operations (applied to each image)
    result = collection | present.images
    print(f"After present.images: {type(result)}")
    print(f"Each attachment has images: {[len(att.images) for att in result.attachments]}")
    
    # Cleanup
    os.remove(zip_path)
    os.rmdir(os.path.dirname(zip_path))
    
    return result

def demo_dsl_vectorization():
    """Demo 2: DSL commands with vectorization."""
    print("\n🎛️ Demo 2: DSL Commands + Vectorization")
    print("=" * 50)
    
    zip_path = create_sample_zip()
    
    # DSL commands are copied to each attachment in collection
    collection = attach(f"{zip_path}[crop:50,50,100,100][tile:2x2]") | load.zip_to_images
    print(f"DSL commands: {collection.attachments[0].commands}")
    
    # Commands flow through vectorized operations (but crop needs implementation)
    # For now, just show the flow
    result = collection | present.images
    print(f"Vectorized processing complete: {len(result.attachments)} images")
    
    # Cleanup
    os.remove(zip_path)
    os.rmdir(os.path.dirname(zip_path))
    
    return result

def demo_reduction_pipeline():
    """Demo 3: Complete pipeline with reduction."""
    print("\n🔄➡️1️⃣ Demo 3: Vectorization → Reduction")
    print("=" * 50)
    
    zip_path = create_sample_zip()
    
    # Complete pipeline: Load → Vectorized Processing → Reduction → Adaptation
    print("Pipeline: load.zip_to_images | present.images | refine.tile_images | adapt.claude")
    
    try:
        result = (attach(f"{zip_path}[tile:2x2]") 
                 | load.zip_to_images     # ZIP → AttachmentCollection
                 | present.images         # Vectorized: each image → base64
                 | refine.tile_images     # Reduction: collection → single tiled image
                 | adapt.claude("Describe this tiled image"))  # Final adaptation
        
        print(f"Final result type: {type(result)}")
        print(f"Claude API format ready: {len(result)} messages")
        
    except Exception as e:
        print(f"Pipeline error: {e}")
        # Fallback: show intermediate steps
        collection = attach(f"{zip_path}[tile:2x2]") | load.zip_to_images
        print(f"Collection loaded: {len(collection.attachments)} attachments")
        
        images_result = collection | present.images
        print(f"Images presented: {type(images_result)}")
        
    # Cleanup
    os.remove(zip_path)
    os.rmdir(os.path.dirname(zip_path))

def demo_additive_vectorization():
    """Demo 4: Additive operations with collections."""
    print("\n➕ Demo 4: Additive Vectorization")
    print("=" * 50)
    
    zip_path = create_sample_zip()
    
    # Additive operations are vectorized too
    collection = attach(zip_path) | load.zip_to_images
    
    # Each attachment gets both metadata and images
    result = collection | (present.metadata + present.images)
    print(f"Additive result: {type(result)}")
    print(f"Each attachment has both metadata and images:")
    for i, att in enumerate(result.attachments):
        print(f"  Attachment {i+1}: {len(att.images)} images, metadata keys: {list(att.metadata.keys())}")
    
    # Cleanup
    os.remove(zip_path)
    os.rmdir(os.path.dirname(zip_path))

def demo_custom_operations():
    """Demo 5: Custom operations in vectorized context."""
    print("\n🛠️ Demo 5: Custom Vectorized Operations")
    print("=" * 50)
    
    # Create manual collection for testing
    attachments = []
    for i in range(3):
        att = Attachment(f"test_{i}.txt")
        att.text = f"Document {i+1} content with some text to analyze."
        att.metadata = {'doc_id': i+1, 'length': len(att.text)}
        attachments.append(att)
    
    collection = AttachmentCollection(attachments)
    print(f"Manual collection: {collection}")
    
    # Vectorized text processing
    result = collection | refine.truncate_text | refine.add_headers
    print("After vectorized refinement:")
    for i, att in enumerate(result.attachments):
        print(f"  Doc {i+1}: {att.text[:50]}...")
    
    # Convert to single attachment for adaptation
    final = result.to_attachment()
    print(f"\nCombined text length: {len(final.text)}")

def main():
    """Run all vectorization demos."""
    print("🚀 Vectorized Operations Demo")
    print("===========================")
    print("Showcasing AttachmentCollection and vectorized pipelines\n")
    
    try:
        demo_basic_vectorization()
        demo_dsl_vectorization() 
        demo_reduction_pipeline()
        demo_additive_vectorization()
        demo_custom_operations()
        
        print("\n✅ All demos completed successfully!")
        print("\n🎯 Key Patterns Demonstrated:")
        print("• AttachmentCollection automatically vectorizes operations")
        print("• DSL commands are copied to all attachments in collection")
        print("• refine.tile_images reduces collection → single attachment")
        print("• Adapters work on final aggregated results")
        print("• Both | (sequential) and + (additive) operators vectorize")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 