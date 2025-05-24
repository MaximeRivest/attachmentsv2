# Attachments Package

A modular file processing pipeline with automatic type dispatch and Jupyter autocomplete.

## 🚀 Quick Start

```python
from attachments import attach, load, present

# Process a CSV file
result = attach("data.csv") | load.csv_to_pandas | present.markdown
print(result.text)
```

## 📚 Sample Data

The package includes sample data files for tutorials and experimentation:

```python
from attachments import attach, load, present, data

# List available sample files
print(data.list_samples())  # ['test.csv', 'sample.json', 'sample.txt']

# Get path to specific sample file
csv_path = data.get_sample_path("test.csv")
json_path = data.get_sample_path("sample.json")
txt_path = data.get_sample_path("sample.txt")

# Use in pipelines
result = attach(csv_path) | load.csv_to_pandas | present.markdown
result = attach(txt_path) | load.text_to_string | present.markdown
result = attach(json_path) | load.text_to_string | present.markdown
```

The sample files include:
- **`test.csv`**: Simple CSV with user data (name, age, city)
- **`sample.json`**: JSON with structured user data and metadata
- **`sample.txt`**: Text file explaining the library features

## ✨ Autocomplete Support

This package provides **excellent autocomplete in Jupyter and IPython**:

- ✅ **Jupyter/IPython** - Full autocomplete via `__dir__` method
- ✅ **Function discovery** - All functions visible with tab completion
- ✅ **Clean namespaces** - Separate `load`, `modify`, `present`, `adapt` namespaces
- ✅ **Zero configuration** - Works immediately after `pip install -e .`

### How It Works

Simple and effective approach:

1. **Runtime introspection**: Custom `__dir__` method shows all available functions
2. **Clean namespaces**: Functions organized by purpose (load/modify/present/adapt)
3. **Dynamic dispatch**: Automatic type-based routing for flexible data processing

## 📦 Adding New Functions

1. Add your function with the appropriate decorator:
```python
@presenter
def my_new_presenter(att: Attachment, obj: 'some.Type') -> Attachment:
    """Convert some.Type to presentation format."""
    # Your implementation
    return att
```

2. Restart your Python session:
```python
# Functions available via __getattr__ and tab completion
from attachments import present
present.my_new_presenter  # ← Works in Jupyter!
```

## 🏗️ Architecture

### Core Components
- **`core.py`**: VerbNamespace with `__dir__` support for autocomplete
- **`__init__.py`**: Simple namespace creation 
- **Module files**: Separate load/modify/present/adapt implementations

### Registry System
- **Decorators**: `@loader`, `@modifier`, `@presenter`, `@adapter`
- **Auto-dispatch**: String-based type matching for optional dependencies
- **Dynamic access**: Functions accessible via `__getattr__`
- **Plugin-friendly**: Add new types without touching core

## 📋 Development Workflow

```bash
# Install in editable mode
pip install -e .

# Add new functions with decorators
# → Restart Python session
# → Functions available immediately

# Run tests
python -m pytest
```

## 🔧 Development Setup

```bash
# Install in editable mode
pip install -e .

# With optional dependencies
pip install -e ".[full]"  # pandas, pdfplumber, etc.
```

## 🎯 Design Philosophy

**"Simple, Clean, Functional"**

- **No complex IDE hacks** - Focus on what works well
- **Excellent Jupyter support** - Perfect for data science workflows
- **Clean architecture** - Easy to understand and extend
- **Zero maintenance** - Add function + restart = ready to go

The system uses Python's standard introspection mechanisms to provide a great experience where it matters most!

## 🔍 Troubleshooting

If autocomplete doesn't work:

1. **Restart Python session** - Functions discovered at import time
2. **Verify editable install**: `pip install -e .` 
3. **Check Python interpreter** - Using the right environment
4. **Try in Jupyter** - Best autocomplete experience there! 