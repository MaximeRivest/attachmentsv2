#%%[markdown]
# # DOCX Processor Demo
# 
# This demo showcases the comprehensive DOCX processor for the attachments library.
# The processor supports multiple text formats, image extraction, and DSL commands.

#%%[markdown]
# ## Basic DOCX Processing
# 
# The DOCX processor automatically detects Word documents and processes them with markdown formatting by default.

#%%
from attachments import Attachments

# Default processing with markdown format
ctx = Attachments('attachments/data/test_document.docx')
ctx.text

#%%[markdown]
# ## Text Format Options
# 
# The processor supports three text formats:
# - `markdown` (default): Structured markdown with heading detection
# - `plain`: Clean text extraction from all paragraphs  
# - `xml`: Raw DOCX XML content for detailed analysis

#%%
# Plain text format
ctx_plain = Attachments('attachments/data/test_document.docx[format:plain]')
ctx_plain.text

#%%
# XML format - shows raw DOCX structure
ctx_xml = Attachments('attachments/data/test_document.docx[format:xml]')
len(ctx_xml.text)

#%%
from IPython.display import HTML
HTML(f"<img src='{ctx_xml.images[0]}'>")

#%%[markdown]
# ## Format Aliases
# 
# The processor supports intuitive format aliases:
# - `text` = `plain`
# - `txt` = `plain`
# - `md` = `markdown`
# - `code` = `xml`

#%%
# Using format aliases
ctx_text = Attachments('attachments/data/test_document.docx[format:text]')
ctx_code = Attachments('attachments/data/test_document.docx[format:code]')

print(f"text alias length: {len(ctx_text.text)}")
print(f"code alias length: {len(ctx_code.text)}")

#%%[markdown]
# ## Image Extraction
# 
# The processor converts DOCX pages to PNG images by first converting to PDF using LibreOffice,
# then rendering with pypdfium2. This provides actual page screenshots including formatting.

#%%
# Default includes images
ctx_with_images = Attachments('attachments/data/test_document.docx')
len(ctx_with_images.images)

#%%
# Disable images
ctx_no_images = Attachments('attachments/data/test_document.docx[images:false]')
len(ctx_no_images.images)

#%%[markdown]
# ## Image Tiling
# 
# Multiple pages can be tiled into grid layouts for compact visualization.

#%%
# Tile pages in a 2x2 grid (if document has multiple pages)
ctx_tiled = Attachments('attachments/data/test_document.docx[tile:2x2]')
len(ctx_tiled.images)

#%%[markdown]
# ## Combined DSL Commands
# 
# Multiple DSL commands can be combined for precise control.

#%%
# Plain text format with images disabled
ctx_combined = Attachments('attachments/data/test_document.docx[format:plain][images:false]')
print(f"Text format: plain")
print(f"Images: {len(ctx_combined.images)}")
print(f"Text length: {len(ctx_combined.text)}")

#%%[markdown]
# ## Processor Registration
# 
# The DOCX processor is automatically registered and available through the processors namespace.

#%%
from attachments import processors

# Check available processors
available_processors = [name for name in dir(processors) if not name.startswith('_')]
print("Available processors:", available_processors)

#%%
# Direct processor access
result = processors.docx_to_llm(Attachments('attachments/data/test_document.docx').attachments[0])
print(f"Direct processor result: {len(result.text)} chars")

#%%[markdown]
# ## Architecture Integration
# 
# The DOCX processor follows the same architecture as other processors:
# - Uses `@processor` decorator with `docx_match`
# - Supports the standard pipeline: `load → modify → present → refine`
# - Integrates with existing DSL command system
# - Compatible with image tiling and resizing refiners

#%%[markdown]
# ## Summary
# 
# The DOCX processor provides:
# 
# ✅ **Multiple text formats**: markdown, plain, xml  
# ✅ **Format aliases**: text, txt, md, code  
# ✅ **Image extraction**: Real page screenshots via LibreOffice → PDF → PNG  
# ✅ **DSL commands**: format, images, pages, tile, resize_images  
# ✅ **Architecture consistency**: Same patterns as PDF/PPTX processors  
# ✅ **Simple API**: Auto-detection with `Attachments("file.docx")` 