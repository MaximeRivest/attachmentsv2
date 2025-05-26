#%%[markdown]
# # Webpage Processor Demo
# 
# This demo showcases the comprehensive webpage processor for the attachments library.
# The processor combines text extraction with screenshot capabilities using Playwright.
# ## Basic Webpage Processing
# 
# The webpage processor automatically detects web URLs and processes them with both text extraction
# and screenshot capabilities. It uses BeautifulSoup for text and Playwright for screenshots.

#%%

# Default processing with markdown format and screenshots
# Note: This will try to capture a screenshot, which requires Playwright
ctx = Attachments('https://httpbin.org/html')

#%%
from attachments import Attachments
from IPython.display import HTML
from openai import OpenAI

client = OpenAI()
att = Attachments('https://maximerivest.github.io/attachments/[select:h1]')
#%%
att.text
#%%
HTML(f"<img src='{att.images[0]}' width=1000>")
#%%
res=OpenAI().chat.completions.create(
    model="gpt-4o-mini",
    messages=att.openai_chat("What do you see? be brief and concise.")
)
print(res.choices[0].message.content)
#%%
print(att.text)

#%%[markdown]
# ## Text Format Options
# 
# The processor supports two text formats:
# - `markdown` (default): Structured markdown preserving some formatting
# - `plain`: Clean text extraction from page content

#%%
# Plain text format
ctx_plain = Attachments('https://httpbin.org/html[format:plain]')
print("Plain text format:")
print(ctx_plain.text[:200])

#%%[markdown]
# ## Screenshot Control
# 
# Screenshots can be enabled or disabled, and various screenshot parameters can be controlled
# through DSL commands.

#%%
# Disable screenshots (text only)
ctx_no_images = Attachments('https://httpbin.org/html[images:false]')
print(f"Text only - Images: {len(ctx_no_images.images)}")
print(f"Text length: {len(ctx_no_images.text)} chars")

#%%[markdown]
# ## Screenshot Configuration
# 
# When screenshots are enabled, various parameters can be controlled:
# - `viewport`: Browser viewport size (default: 1280x720)
# - `fullpage`: Full page vs viewport only (default: true)
# - `wait`: Wait time for page to settle in milliseconds (default: 200)

#%%
# Custom viewport and wait time
# Note: This requires Playwright to be installed
ctx_custom = Attachments('https://httpbin.org/html[viewport:1920x1080][wait:1000][fullpage:false]')
print(f"Custom screenshot config:")
print(f"Images: {len(ctx_custom.images)}")
if 'screenshot_viewport' in ctx_custom.attachments[0].metadata:
    print(f"Viewport: {ctx_custom.attachments[0].metadata['screenshot_viewport']}")
    print(f"Full page: {ctx_custom.attachments[0].metadata['screenshot_fullpage']}")

#%%[markdown]
# ## Error Handling
# 
# The processor gracefully handles cases where Playwright is not installed,
# falling back to text-only processing.

#%%
# Check for screenshot errors
ctx_test = Attachments('https://httpbin.org/html')
if ctx_test.attachments:
    metadata = ctx_test.attachments[0].metadata
    if 'screenshot_error' in metadata:
        print(f"Screenshot error: {metadata['screenshot_error']}")
    elif 'screenshot_captured' in metadata:
        print("Screenshot captured successfully!")
    else:
        print("No screenshot attempted")

#%%[markdown]
# ## Format Aliases
# 
# The processor supports intuitive format aliases:
# - `text` = `plain`
# - `txt` = `plain`
# - `md` = `markdown`

#%%
# Using format aliases
ctx_text = Attachments('https://httpbin.org/html[format:text]')
print(f"text alias length: {len(ctx_text.text)}")

#%%[markdown]
# ## CSS Selector Support
# 
# The webpage processor now supports CSS selectors to extract specific elements from web pages.
# This allows you to target exactly the content you need instead of processing the entire page.

#%%
# Extract only the main heading
ctx_title = Attachments('https://httpbin.org/html[select:h1][format:plain]')
print("H1 heading only:")
print(ctx_title.text.strip())

#%%
# Extract only paragraphs
ctx_paragraphs = Attachments('https://httpbin.org/html[select:p][format:plain]')
print("Paragraphs only:")
print(ctx_paragraphs.text.strip()[:200] + "...")

#%%
# CSS selector with images disabled for faster processing
ctx_fast = Attachments('https://httpbin.org/html[select:h1][format:plain][images:false]')
print(f"Fast extraction (no images): {len(ctx_fast.images)} images")
print(f"Content: {ctx_fast.text.strip()}")

#%%[markdown]
# ### CSS Selector Examples
# 
# The processor supports any valid CSS selector:
# - `[select:title]` - Extract page title
# - `[select:h1]` - Extract all h1 headings
# - `[select:.content]` - Extract elements with class "content"
# - `[select:#main]` - Extract element with id "main"
# - `[select:p]` - Extract all paragraphs
# - `[select:article h2]` - Extract h2 elements inside article tags
# - `[select:.post-content, .article-body]` - Multiple selectors

#%%
# Test with Wikipedia for more realistic example
ctx_wiki = Attachments('https://en.wikipedia.org/wiki/Llama[select:h1][format:plain][images:false]')
print("Wikipedia title extraction:")
print(ctx_wiki.text.strip())

#%%
# Extract first few paragraphs from Wikipedia
ctx_wiki_content = Attachments('https://en.wikipedia.org/wiki/Llama[select:p][format:plain][images:false]')
print("Wikipedia content (first 300 chars):")
print(ctx_wiki_content.text.strip()[:300] + "...")

#%%[markdown]
# ### CSS Selector Metadata
# 
# The processor tracks CSS selector usage in metadata for debugging and optimization.

#%%
# Check CSS selector metadata
ctx_meta = Attachments('https://httpbin.org/html[select:h1]')
if ctx_meta.attachments:
    metadata = ctx_meta.attachments[0].metadata
    print("CSS Selector Metadata:")
    print(f"  Selector used: {metadata.get('selector', 'None')}")
    print(f"  Elements found: {metadata.get('selected_count', 'Unknown')}")
    print(f"  Selection applied: {metadata.get('selection_applied', 'Unknown')}")

#%%[markdown]
# ## Combined DSL Commands
# 
# Multiple DSL commands can be combined for precise control.

#%%
# Plain text format with custom screenshot settings
ctx_combined = Attachments('https://httpbin.org/html[format:plain][viewport:800x600][wait:500]')
print(f"Combined commands:")
print(f"Text format: plain")
print(f"Images: {len(ctx_combined.images)}")
print(f"Text length: {len(ctx_combined.text)}")

#%%[markdown]
# ## Processor Registration
# 
# The webpage processor is automatically registered and available through the processors namespace.

#%%
from attachments import processors

# Check available processors
available_processors = [name for name in dir(processors) if not name.startswith('_')]
print("Available processors:", available_processors)

#%%
# Direct processor access
from attachments import attach
result = processors.webpage_to_llm(attach('https://httpbin.org/html'))
print(f"Direct processor result: {len(result.text)} chars")

#%%[markdown]
# ## Architecture Integration
# 
# The webpage processor follows the same architecture as other processors:
# - Uses `@processor` decorator with `webpage_match`
# - Supports the standard pipeline: `load → present → refine`
# - Integrates with existing DSL command system
# - Combines text extraction (BeautifulSoup) with screenshots (Playwright)

#%%[markdown]
# ## URL vs File Distinction
# 
# The system intelligently distinguishes between:
# - **Webpage URLs**: `https://example.com` → webpage processor (text + screenshot)
# - **File URLs**: `https://example.com/document.pdf` → file download + appropriate processor

#%%
# This would go to webpage processor
webpage_url = "https://httpbin.org/html"
print(f"Webpage URL: {webpage_url}")

#%%
# This would go to PDF processor (if the URL existed)
file_url = "https://example.com/document.pdf"
att = Attachments(file_url)
att.text


#%%[markdown]
# ## Future Improvements
# 
# The webpage processor includes notes for future enhancements:
# 
# 🔮 **Planned improvements**:
# - Element-specific screenshots using CSS selectors
# - Mobile viewport simulation
# - Multiple screenshot formats (PNG, JPEG, WebP)
# - Performance metrics capture
# - Network request interception
# - PDF generation from web pages

#%%[markdown]
# ## Summary
# 
# The webpage processor provides:
# 
# ✅ **Text extraction**: Clean text from web pages using BeautifulSoup  
# ✅ **Screenshot capture**: Full-page screenshots with JavaScript rendering  
# ✅ **CSS selectors**: Extract specific elements using any valid CSS selector  
# ✅ **Format options**: markdown (default), plain text  
# ✅ **Format aliases**: text, txt, md  
# ✅ **Screenshot control**: viewport size, full page vs viewport, wait times  
# ✅ **DSL commands**: format, select, images, viewport, fullpage, wait  
# ✅ **Error handling**: Graceful fallback when Playwright unavailable  
# ✅ **Architecture consistency**: Same patterns as other processors  
# ✅ **Smart URL routing**: Webpages vs downloadable files  
# ✅ **Future-ready**: Documented improvement roadmap 

#%%[markdown]
# ### Element Highlighting in Screenshots
# 
# When using CSS selectors, the screenshot automatically highlights the selected elements
# with a blue outline and label, similar to browser dev tools. This makes it easy to
# visually verify which elements were selected.

#%%
# Screenshot with highlighted H1 element
ctx_highlighted = Attachments('https://httpbin.org/html[select:h1]')
print("Screenshot with highlighted H1:")
print(f"  Images captured: {len(ctx_highlighted.images)}")
if ctx_highlighted.attachments:
    metadata = ctx_highlighted.attachments[0].metadata
    print(f"  Highlighted selector: {metadata.get('highlighted_selector', 'None')}")
    print(f"  Elements highlighted: {metadata.get('highlighted_elements', 'None')}")
    print(f"  Screenshot shows blue outline around selected element!")

#%%
# Test with multiple elements (if available)
ctx_multi = Attachments('https://en.wikipedia.org/wiki/Llama[select:h2][wait:1000]')
print("Wikipedia with highlighted H2 elements:")
print(f"  Images captured: {len(ctx_multi.images)}")
if ctx_multi.attachments:
    metadata = ctx_multi.attachments[0].metadata
    print(f"  Highlighted selector: {metadata.get('highlighted_selector', 'None')}")
    print(f"  Elements highlighted: {metadata.get('highlighted_elements', 'None')}")
    if metadata.get('highlighted_elements', 0) > 1:
        print(f"  Multiple elements highlighted with counters (1/n, 2/n, etc.)")

#%%
# show the selected images
HTML(f"<img src='{ctx_multi.images[0]}'")

#%%[markdown]
# ### Highlighting Features
# 
# The element highlighting provides:
# 
# 🎯 **Visual feedback**: Blue outline around selected elements  
# 📍 **Element labels**: "📍 Selected" badge on each highlighted element  
# 🔢 **Element counting**: Shows "📍 Selected (1/3)" for multiple selections  
# 🎨 **Dev tools style**: Familiar blue outline similar to browser inspector  
# 📊 **Metadata tracking**: Records selector and element count in metadata  
# ⚡ **Automatic**: Works with any CSS selector, no extra configuration needed  
# 
# This makes it easy to:
# - **Debug selectors**: Visually verify which elements match your CSS selector
# - **Document extraction**: Show stakeholders exactly what content is being extracted
# - **Quality assurance**: Ensure selectors are working as expected
# - **Training**: Help users understand CSS selector behavior 