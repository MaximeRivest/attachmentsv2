#%%[markdown]
# # Excel Processor Demo
# 
# This demo showcases the comprehensive Excel processor for the attachments library.
# The processor supports sheet summaries, table previews, and screenshot capabilities.

#%%[markdown]
# ## Basic Excel Processing
# 
# The Excel processor automatically detects Excel files and processes them with markdown formatting by default,
# providing sheet summaries and table previews.

#%%
from attachments import Attachments

# Default processing with markdown format
ctx = Attachments('attachments/data/test_workbook.xlsx')
print(ctx.text)

#%%[markdown]
# ## Text Format Options
# 
# The processor supports two text formats:
# - `markdown` (default): Structured markdown with sheet headers and table previews
# - `plain`: Clean text summary with sheet dimensions and data preview

#%%
# Plain text format
ctx_plain = Attachments('attachments/data/test_workbook.xlsx[format:plain]')
ctx_plain.text

#%%[markdown]
# ## Format Aliases
# 
# The processor supports intuitive format aliases:
# - `text` = `plain`
# - `txt` = `plain`
# - `md` = `markdown`

#%%
# Using format aliases
ctx_text = Attachments('attachments/data/test_workbook.xlsx[format:text]')
print(f"text alias length: {len(ctx_text.text)}")
print("Content preview:")
print(ctx_text.text[:200])

#%%[markdown]
# ## Sheet Screenshots
# 
# The processor converts Excel sheets to PNG images by first converting to PDF using LibreOffice,
# then rendering with pypdfium2. This provides actual sheet screenshots including formatting and charts.

#%%
# Default includes sheet screenshots
ctx_with_images = Attachments('attachments/data/test_workbook.xlsx')
len(ctx_with_images.images)

#%%
from IPython.display import HTML
HTML(f"<img src='{ctx_with_images.images[0]}'>")

#%%
# Disable images
ctx_no_images = Attachments('attachments/data/test_workbook.xlsx[images:false]')
len(ctx_no_images.images)

#%%[markdown]
# ## Sheet Selection
# 
# Specific sheets can be selected using the pages DSL command (treating pages as sheets).

#%%
# Select only the first sheet
ctx_first_sheet = Attachments('attachments/data/test_workbook.xlsx[pages:1]')
print(f"Selected sheet 1 only:")
print(f"Images: {len(ctx_first_sheet.images)}")
print("Text preview:")
print(ctx_first_sheet.text[:300])

#%%[markdown]
# ## Image Tiling
# 
# Multiple sheets can be tiled into grid layouts for compact visualization.

#%%
# Tile sheets in a 2x1 grid
ctx_tiled = Attachments('attachments/data/test_workbook.xlsx[tile:2x1]')
len(ctx_tiled.images)

#%%
from IPython.display import HTML
HTML(f"<img src='{ctx_tiled.images[0]}'>")

#%%[markdown]
# ## Combined DSL Commands
# 
# Multiple DSL commands can be combined for precise control.

#%%
# Plain text format with images disabled
ctx_combined = Attachments('attachments/data/test_workbook.xlsx[format:plain][images:false]')
print(f"Text format: plain")
print(f"Images: {len(ctx_combined.images)}")
print(f"Text length: {len(ctx_combined.text)}")

#%%[markdown]
# ## Processor Registration
# 
# The Excel processor is automatically registered and available through the processors namespace.

#%%
from attachments import processors

# Check available processors
available_processors = [name for name in dir(processors) if not name.startswith('_')]
print("Available processors:", available_processors)

#%%
# Direct processor access
result = processors.excel_to_llm(Attachments('attachments/data/test_workbook.xlsx').attachments[0])
print(f"Direct processor result: {len(result.text)} chars")

#%%[markdown]
# ## Architecture Integration
# 
# The Excel processor follows the same architecture as other processors:
# - Uses `@processor` decorator with `excel_match`
# - Supports the standard pipeline: `load → modify → present → refine`
# - Integrates with existing DSL command system
# - Compatible with image tiling and resizing refiners
# - Treats "pages" as "sheets" for sheet selection

#%%[markdown]
# ## Future Improvements
# 
# The Excel processor includes notes for future enhancements:
# 
# 🔮 **Planned improvements**:
# - Direct Excel-to-image conversion using xlwings or similar
# - Better handling of large sheets with automatic scaling
# - Support for chart extraction and analysis
# - Custom sheet selection and formatting options
# - CSV export functionality for individual sheets

#%%[markdown]
# ## Summary
# 
# The Excel processor provides:
# 
# ✅ **Sheet summaries**: Dimensions and data previews for each sheet  
# ✅ **Table previews**: Markdown tables showing first 5 rows/columns  
# ✅ **Format options**: markdown (default), plain text  
# ✅ **Format aliases**: text, txt, md  
# ✅ **Sheet screenshots**: Real sheet images via LibreOffice → PDF → PNG  
# ✅ **DSL commands**: format, images, pages (as sheets), tile, resize_images  
# ✅ **Architecture consistency**: Same patterns as PDF/PPTX/DOCX processors  
# ✅ **Simple API**: Auto-detection with `Attachments("file.xlsx")`  
# ✅ **Future-ready**: Documented improvement roadmap 