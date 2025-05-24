# Attachments Package

A Python library that defines a **grammar of file-to-LLM processing**, providing a consistent set of verbs to turn any file into model-ready context.

## 🎯 Mission

Transform any file format into structured, AI-ready content using a clean **load → modify → present → refine → adapt** pipeline with standardized verbs and intuitive operators.

## 🚀 Quick Start

```python
from attachments import attach, load, modify, present, refine, adapt

# Basic file-to-LLM pipeline
result = attach("document.pdf") | load.pdf_to_pdfplumber | present.text | adapt.claude

# With additive content extraction
result = (attach("data.csv") | load.csv_to_pandas 
         | present.markdown + present.summary + present.metadata | adapt.openai_chat)

# Complete grammar with refinement
result = (attach("image.jpg") | load.image_to_pil | present.images 
         | refine.tile_images | adapt.claude("What do you see?"))
```

## 🎯 The Grammar

The library provides **five categories of verbs** with **two composition operators** that solve the most common challenges of file-to-LLM processing:

### 🔄 **`load.*()`** - File Format Transformation
Transforms files into standardized attachments based on their format:
```python
load.pdf_to_pdfplumber    # PDF → pdfplumber object
load.csv_to_pandas        # CSV → pandas DataFrame  
load.image_to_pil         # Images → PIL Image
load.url_to_bs4           # URLs → BeautifulSoup
load.text_to_string       # Text files → string
```

### ⚙️ **`modify.*()`** - Content Operations
Transforms attachment content with common operations:
```python
modify.pages              # Extract specific pages: [pages:1-3]
modify.limit              # Limit rows/items: [limit:10]
modify.select             # Select columns/elements: [select:name,age]
modify.crop               # Crop images: [crop:100,100,400,300]
modify.rotate             # Rotate images: [rotate:90]
```

### 📋 **`present.*()`** - Content Extraction
Extracts content in different formats for LLM consumption:
```python
present.text              # Extract as plain text
present.markdown          # Format as markdown
present.images            # Convert to base64 images
present.metadata          # Extract metadata
present.summary           # Generate summaries
present.head              # Data preview
```

### ✨ **`refine.*()`** - Content Refinement
Post-processes extracted content for optimization:
```python
refine.truncate_text      # Limit text length: [truncate:500]
refine.add_headers        # Add markdown headers
refine.format_tables      # Format table content
refine.tile_images        # Tile images in grid: [tile:2x2]
refine.resize_images      # Resize images: [resize:800x600]
```

### 🤖 **`adapt.*()`** - API Formatting
Formats attachments for specific LLM APIs:
```python
adapt.claude              # Claude API format
adapt.openai_chat         # OpenAI Chat format
adapt.openai_response     # OpenAI Response format
```

## 🔗 Composition Operators

### **`|` Sequential Pipeline (Transform/Overwrite)**
Sequential processing where each step transforms or overwrites:
```python
# Sequential transformation
load.pdf_to_pdfplumber | modify.pages | present.text

# Overwriting presentation (text overwrites images)
present.images | present.text  # Only text remains

# Sequential refinement
refine.truncate_text | refine.add_headers
```

### **`+` Additive Composition (Accumulate)**
Additive processing that preserves and combines content:
```python
# Combine multiple content types
present.text + present.images + present.metadata

# Multiple text extractions
present.head + present.summary + present.metadata  # All text combined

# Build rich content
present.markdown + present.images  # Text AND images together
```

## 🎯 Complete Grammar Examples

### **Multi-Content Extraction**
```python
# Extract and combine multiple content types
result = (attach("document.pdf") | load.pdf_to_pdfplumber 
         | present.markdown + present.images + present.metadata
         | refine.truncate_text | refine.tile_images
         | adapt.claude("Analyze this document"))
```

### **Data Analysis Pipeline**
```python
# Rich data presentation with refinement
result = (attach("data.csv[limit:100]") | load.csv_to_pandas | modify.limit
         | present.head + present.summary + present.metadata
         | refine.add_headers | refine.format_tables
         | adapt.openai_chat("What patterns do you see?"))
```

### **Image Processing Workflow**
```python
# Process and refine images
result = (attach("photos.zip[extract:all]") | load.zip_to_images
         | present.images | refine.tile_images | refine.resize_images
         | adapt.claude("Describe these images"))
```

## 🎛️ DSL Commands

Embed processing commands directly in file paths using `[command:value]` syntax:

```python
# Multiple commands in sequence
attach("document.pdf[pages:1-3][truncate:500][prompt:Summarize this]")
| load.pdf_to_pdfplumber | modify.pages | present.text 
| refine.truncate_text | adapt.claude

# Image processing commands
attach("photo.heic[crop:100,100,400,300][rotate:90][tile:2x2]")
| load.heic_to_pillow | modify.crop | modify.rotate | present.images 
| refine.tile_images

# Data processing commands  
attach("data.csv[limit:100][select:name,age][truncate:500]")
| load.csv_to_pandas | modify.limit | modify.select 
| present.text | refine.truncate_text
```

## 🖼️ Complete Example: Custom HEIC Processing

```python
from attachments import attach, load, modify, present, refine, adapt, loader, modifier

# Define custom verbs following the grammar
@loader(lambda att: att.path.lower().endswith(('.heic', '.heif')))
def heic_to_pillow(att):
    """Custom loader: HEIC files → PIL Image objects"""
    from pillow_heif import register_heif_opener; register_heif_opener()
    from PIL import Image
    att._obj = Image.open(att.path)
    return att

@modifier  
def crop(att, img: 'PIL.Image.Image'):
    """Custom modifier: Apply crop commands from DSL"""
    if 'crop' in att.commands:
        att._obj = img.crop([int(x) for x in att.commands['crop'].split(',')])
    return att

# Use in complete grammar pipeline
result = (attach("IMG_2160.HEIC[crop:100,100,400,300][rotate:90][tile:2x2]")
         | load.heic_to_pillow | modify.crop | modify.rotate     # Transform
         | present.images | refine.tile_images                   # Extract + Refine
         | adapt.claude("What do you see?"))                     # Adapt

# Create reusable processor
image_processor = load.heic_to_pillow | modify.crop | present.images | refine.tile_images
result = image_processor("photo.heic[crop:50,50,200,200][tile:2x2]").claude("Describe this")
```

## 🏗️ Architecture

### The Load → Modify → Present → Refine → Adapt Flow

1. **Load**: Transform file formats into standardized objects (`file → att._obj`)
2. **Modify**: Apply content transformations and filtering (`att._obj → att._obj`)
3. **Present**: Extract content in LLM-ready formats (`att._obj → att.text/images/audio`)
4. **Refine**: Post-process extracted content (`att.text/images/audio → refined content`)
5. **Adapt**: Format for specific API requirements (`content → API format`)

### Operator Semantics

| Operator | Semantic | Use Cases |
|----------|----------|-----------|
| **`\|`** | Sequential flow | Load chains, modify chains, overwrite present, refine chains |
| **`+`** | Additive combination | Multi-content extraction, rich presentations |

### Smart Chaining
- **Loaders** skip gracefully if file doesn't match or is already loaded
- **Modifiers** check DSL commands and apply transformations sequentially
- **Presenters** extract content based on object type (overwrite with `|`, combine with `+`)
- **Refiners** process extracted content sequentially
- **Adapters** format for API consumption and handle prompts

### DSL Command System
Commands embedded in paths: `"file.ext[command1:value1][command2:value2]"`

```python
# Parser extracts commands automatically
att = attach("file.csv[limit:10][select:name][truncate:100]")
print(att.commands)  # {'limit': '10', 'select': 'name', 'truncate': '100'}

# Commands flow through the pipeline
result = (att | load.csv_to_pandas | modify.limit | modify.select 
         | present.text | refine.truncate_text)
```

## 📦 Built-in Verb Library

### File Format Loaders
- **Documents**: `pdf_to_pdfplumber`, `text_to_string`
- **Data**: `csv_to_pandas` 
- **Images**: `image_to_pil` (supports HEIC with pillow-heif)
- **Web**: `url_to_bs4`
- **Presentations**: `pptx_to_python_pptx`

### Content Modifiers
- **Data**: `limit`, `select` (rows/columns)
- **Documents**: `pages` (page selection)
- **Images**: Custom `crop`, `rotate` (via DSL)

### Content Presenters  
- **Text formats**: `text`, `markdown`, `csv`, `xml`
- **Visual**: `images` (base64 conversion)
- **Analysis**: `head`, `summary`, `metadata`

### Content Refiners
- **Text**: `truncate_text`, `add_headers`, `format_tables`
- **Images**: `tile_images`, `resize_images`

### API Adapters
- **Claude**: `claude` (Anthropic format)
- **OpenAI**: `openai_chat`, `openai_response`
- **Prompt support**: Via DSL `[prompt:text]` or direct parameters

## 🔧 Installation

```bash
# Basic installation
pip install -e .

# With optional dependencies for full format support
pip install -e ".[full]"  # pandas, pillow, beautifulsoup4, pdfplumber, etc.

# For HEIC image support
pip install pillow-heif
```

## 🎯 Design Philosophy

**"Grammar-First File Processing"**

- **Consistent verbs**: Standard vocabulary for file-to-LLM operations
- **Intuitive operators**: `|` for sequential flow, `+` for additive combination
- **Clear semantics**: Each operator has single, predictable meaning
- **Composable pipelines**: Natural `|` and `+` operator chaining
- **DSL integration**: Commands embedded in file paths
- **Type dispatch**: Automatic routing based on content types
- **AI-ready**: Direct integration with modern LLM APIs

The grammar approach makes file processing pipelines **readable, composable, and discoverable**.

## 🚀 Advanced Usage

### Multi-Format Universal Processor
```python
# Handles any file format automatically with rich content extraction
universal = (load.pdf_to_pdfplumber | load.csv_to_pandas | load.image_to_pil 
            | load.text_to_string 
            | present.text + present.images + present.metadata
            | refine.truncate_text | refine.tile_images
            | adapt.claude)

universal("document.pdf")     # PDF processing with text + images
universal("data.csv")         # CSV processing with text + metadata
universal("image.jpg")        # Image processing with refined images
```

### Custom Pipeline Functions
```python
# Domain-specific processors following the grammar
document_analyzer = (load.pdf_to_pdfplumber | modify.pages 
                    | present.markdown + present.images
                    | refine.add_headers | refine.tile_images
                    | adapt.claude("Analyze the key points"))

data_explorer = (load.csv_to_pandas | modify.limit 
                | present.head + present.summary + present.metadata
                | refine.format_tables | refine.add_headers
                | adapt.openai_chat("What patterns do you see?"))

# Compose processors
research_pipeline = document_analyzer + data_explorer  # Combine processors
```

### Grammar Patterns
```python
# Sequential transformation
file | load.* | modify.* | modify.*     # Chain modifications

# Additive extraction  
obj | present.* + present.* + present.*  # Combine content types

# Sequential refinement
content | refine.* | refine.* | refine.*  # Chain refinements

# Complete pipeline
file | load.* | modify.* | present.* + present.* | refine.* | adapt.*
```

Ready to transform any file into AI-ready context with a **consistent, intuitive grammar**! 🚀
