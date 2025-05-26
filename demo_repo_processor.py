#%%
# Repository and Directory Processing Demo
# Showcases the new grammar-based architecture for repositories and directories

from attachments import Attachments, attach, load, present, refine, adapt
import os

#%% [markdown]
# # Repository and Directory Processing Demo
# 
# This demo showcases the new repository and directory processing capabilities
# following the proper grammar system architecture:
# 
# ## Grammar System:
# - **Load**: Repository/directory → structure objects
# - **Present**: Structure objects → text/metadata/file lists  
# - **Refine**: Post-process content (headers, formatting)
# - **Adapt**: Format for LLM APIs
# 
# ## Features:
# 1. **Git Repositories**: Automatic Git repo detection with metadata
# 2. **Regular Directories**: Process any folder recursively  
# 3. **Glob Patterns**: Use shell-style patterns to filter files
# 4. **Three Presentation Modes**: structure, metadata, files (default)
# 5. **Smart Ignore**: Standard patterns, .gitignore, or custom rules

#%%
# Test with current repository (attachmentsv2)
repo_path = "."  # Current directory

# Check if we're in a Git repository
if os.path.exists(".git"):
    print("✅ Found Git repository")
    is_git_repo = True
else:
    print("📁 Regular directory (not a Git repository)")
    is_git_repo = False

#%% [markdown]
# ## Grammar System Demo: Load → Present → Refine
# 
# Demonstrate the proper separation of concerns

#%%
try:
    print("🔧 Grammar System Demo: Load → Present → Refine")
    
    # Step 1: Load repository structure
    repo_structure = attach(f"{repo_path}[max_files:5]") | load.git_repo_to_structure
    print(f"✅ Loaded: {repo_structure._obj['type']} with {len(repo_structure._obj['files'])} files")
    
    # Step 2: Present in different formats
    structure_view = repo_structure | present.structure
    print(f"📊 Structure view: {len(structure_view.text)} characters")
    
    metadata_view = repo_structure | present.metadata  
    print(f"📊 Metadata view: {len(metadata_view.text)} characters")
    
    files_view = repo_structure | present.files
    print(f"📊 Files view: {len(files_view.text)} characters")
    
    # Step 3: Refine with headers
    refined = structure_view | refine.add_headers
    print(f"📊 Refined: {len(refined.text)} characters")
    
    print("\n📋 Structure Preview:")
    print(structure_view.text[:300] + "..." if len(structure_view.text) > 300 else structure_view.text)
    
except Exception as e:
    print(f"❌ Error: {e}")

#%% [markdown]
# ## Simple API: Automatic Mode Detection
# 
# The simple API automatically detects modes from DSL commands

#%%
try:
    print("🎯 Simple API with Mode Detection...")
    
    # Mode 1: Structure only (clean tree view)
    structure = Attachments(f"{repo_path}[mode:structure][max_files:10]")
    print(f"📊 Structure mode: {len(structure.text)} chars")
    print("Structure preview:")
    print(structure.text[:400] + "..." if len(structure.text) > 400 else structure.text)
    
    print("\n" + "="*50 + "\n")
    
    # Mode 2: Metadata (structure + Git info)
    if is_git_repo:
        metadata = Attachments(f"{repo_path}[mode:metadata][max_files:10]")
        print(f"📊 Metadata mode: {len(metadata.text)} chars")
        print("Metadata preview:")
        print(metadata.text[:400] + "..." if len(metadata.text) > 400 else metadata.text)
    else:
        print("📊 Metadata mode: Skipped (not a Git repo)")
    
    print("\n" + "="*50 + "\n")
    
    # Mode 3: Files (default - processes individual files)
    files = Attachments(f"{repo_path}[mode:files][max_files:3]")
    print(f"📊 Files mode: {len(files)} attachments processed")
    if len(files.attachments) > 1:
        print(f"First file preview: {files.attachments[1].text[:200]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")

#%% [markdown]
# ## Advanced Pipeline Composition
# 
# Build custom pipelines using the grammar system

#%%
try:
    print("🔧 Advanced Pipeline Composition...")
    
    # Custom repository analyzer
    repo_analyzer = (load.git_repo_to_structure 
                    | present.metadata 
                    | refine.add_headers 
                    | adapt.claude)
    
    # Apply to repository
    analysis_ready = repo_analyzer(f"{repo_path}[max_files:5]", 
                                  prompt="Analyze this codebase structure and suggest improvements")
    
    print(f"📊 Analysis ready: {len(analysis_ready)} messages")
    print(f"📝 Content preview: {analysis_ready[0]['content'][0]['text'][:200]}...")
    
    # Directory structure processor
    structure_processor = (load.directory_to_structure 
                          | present.structure 
                          | refine.add_headers)
    
    structure_result = structure_processor(f"{repo_path}[max_files:8]")
    print(f"📊 Structure processor: {len(structure_result.text)} chars")
    
except Exception as e:
    print(f"❌ Error: {e}")

#%% [markdown]
# ## Glob Pattern Support
# 
# Use glob patterns to filter specific file types

#%%
try:
    print("🎯 Testing glob pattern support...")
    
    # Test different glob patterns with the grammar system
    patterns = [
        "*.py",           # Python files only
        "*.md",           # Markdown files
        "demo_*.py",      # Demo files only
    ]
    
    for pattern in patterns:
        try:
            # Use grammar system
            result = (attach(f"{repo_path}[glob:{pattern}][max_files:5]") 
                     | load.directory_to_structure 
                     | present.files)
            
            file_count = len(result._obj.get('files', []))
            print(f"📊 Pattern '{pattern}': {file_count} files")
            
            # Show matched files
            for file_path in result._obj.get('files', [])[:3]:
                print(f"  - {os.path.basename(file_path)}")
                
        except Exception as e:
            print(f"❌ Pattern '{pattern}' failed: {e}")
        
        print()
    
except Exception as e:
    print(f"❌ Error: {e}")

#%% [markdown]
# ## Direct Glob Patterns
# 
# Use glob patterns directly in the path

#%%
try:
    print("🌟 Testing direct glob patterns...")
    
    # Direct glob patterns
    glob_patterns = [
        "*.py",           # All Python files in current dir
        "demo_*.py",      # Demo files only
    ]
    
    for pattern in glob_patterns:
        try:
            # Simple API
            result = Attachments(f"{pattern}[max_files:3]")
            print(f"📊 Glob '{pattern}': {len(result)} files")
            
            # Show matched files
            for att in result.attachments[:3]:  # Show first 3
                print(f"  - {os.path.basename(att.path)}")
                
        except Exception as e:
            print(f"❌ Glob '{pattern}' failed: {e}")
        
        print()
    
except Exception as e:
    print(f"❌ Error: {e}")

#%% [markdown]
# ## Ignore Pattern Testing
# 
# Test different ignore pattern strategies

#%%
try:
    print("🚫 Testing ignore patterns...")
    
    ignore_strategies = [
        "minimal",        # Just basic ignores
        "standard",       # Standard development ignores
    ]
    
    if os.path.exists(".gitignore"):
        ignore_strategies.append("gitignore")  # Use .gitignore patterns
    
    for strategy in ignore_strategies:
        try:
            # Use grammar system
            result = (attach(f"{repo_path}[ignore:{strategy}][max_files:20]") 
                     | load.git_repo_to_structure 
                     | present.structure)
            
            file_count = len(result._obj.get('files', []))
            print(f"📊 Ignore '{strategy}': {file_count} files found")
            
        except Exception as e:
            print(f"❌ Strategy '{strategy}' failed: {e}")
    
    # Custom ignore patterns
    try:
        custom = (attach(f"{repo_path}[ignore:*.pyc,__pycache__,.git][max_files:20]") 
                 | load.directory_to_structure 
                 | present.structure)
        
        file_count = len(custom._obj.get('files', []))
        print(f"📊 Custom ignore: {file_count} files found")
        
    except Exception as e:
        print(f"❌ Custom ignore failed: {e}")
    
except Exception as e:
    print(f"❌ Error: {e}")

#%% [markdown]
# ## LLM Integration Examples
# 
# Ready-to-use examples for LLM analysis

#%%
try:
    print("🤖 LLM Integration Examples...")
    
    # Example 1: Repository overview for Claude
    repo_overview = Attachments(f"{repo_path}[mode:metadata][max_files:10]")
    claude_msgs = repo_overview.claude("Analyze this codebase and suggest improvements")
    print(f"📊 Claude overview: {len(claude_msgs)} messages")
    
    # Example 2: Code analysis with file processing
    code_analysis = Attachments(f"{repo_path}[glob:*.py][max_files:3]")
    openai_msgs = code_analysis.openai("Review this Python code for best practices")
    print(f"📊 OpenAI analysis: {len(openai_msgs)} messages")
    
    # Example 3: Custom pipeline for documentation
    doc_pipeline = (load.git_repo_to_structure 
                   | present.files 
                   | refine.add_repo_headers 
                   | adapt.claude)
    
    doc_ready = doc_pipeline(f"{repo_path}[glob:*.md][max_files:5]", 
                            prompt="Generate comprehensive documentation")
    print(f"📊 Documentation pipeline: {len(doc_ready)} messages")
    
except Exception as e:
    print(f"❌ Error: {e}")

#%% [markdown]
# ## Performance and Best Practices
# 
# Tips for efficient repository processing

#%%
print("⚡ Performance Tips:")
print("1. Use max_files to limit processing: [max_files:100]")
print("2. Use glob patterns to filter: [glob:*.py,*.js]") 
print("3. Use ignore patterns to skip unwanted files: [ignore:standard]")
print("4. Use structure mode for quick overviews: [mode:structure]")
print("5. Use files mode only when you need full content processing")
print()
print("📊 Recommended limits:")
print("- Small repos: max_files:50")
print("- Medium repos: max_files:100") 
print("- Large repos: max_files:200 with specific glob patterns")
print()
print("🎯 Common patterns:")
print("- Code review: [glob:*.py,*.js][max_files:20]")
print("- Documentation: [glob:*.md,*.rst][max_files:10]")
print("- Configuration: [glob:*.json,*.yaml,*.toml][max_files:15]")

print("\n✅ Demo completed! Repository processing is ready for use.")

#%% [markdown]
# ## Real-World Examples
# 
# Practical examples for different use cases

#%%
print("🌟 Real-world usage examples:")
print("=" * 50)

examples = [
    # Git repository examples
    ('Git repo analysis', 'Attachments(".[ignore:standard][max_files:20]")'),
    ('Python files only', 'Attachments(".[glob:*.py][max_files:10]")'),
    ('Documentation files', 'Attachments(".[glob:*.md,*.rst,*.txt]")'),
    
    # Directory examples  
    ('Process src folder', 'Attachments("src[recursive:true][max_files:15]")'),
    ('Config files only', 'Attachments(".[glob:*.json,*.yaml,*.toml]")'),
    
    # Glob pattern examples
    ('All Python files', 'Attachments("**/*.py[max_files:10]")'),
    ('Test files only', 'Attachments("**/test_*.py")'),
    ('Demo files', 'Attachments("demo_*.py")'),
]

for description, code in examples:
    print(f"📝 {description}:")
    print(f"   {code}")
    print()

#%% [markdown]
# ## Performance and Limitations
# 
# Understanding the system's capabilities

#%%
try:
    print("⚡ Performance characteristics:")
    print("=" * 40)
    
    # Test with different file limits
    for max_files in [5, 10, 20]:
        result = Attachments(f"{repo_path}[mode:metadata][max_files:{max_files}]")
        actual_files = result.metadata.get('file_count', 0)
        print(f"📊 Limit {max_files}: Found {actual_files} files")
    
    print("\n💡 Best practices:")
    print("- Use mode:structure for quick directory overviews")
    print("- Set max_files limit to control processing time")
    print("- Use glob patterns to focus on specific file types")
    print("- Use ignore:standard for development directories")
    print("- Binary files are automatically skipped")
    print("- Large files (>10MB) are automatically skipped")
    
except Exception as e:
    print(f"❌ Error: {e}")

#%% [markdown]
# ## Summary
# 
# The new repository and directory processing provides:
# 
# ### **Git Repository Support**
# - Automatic Git detection and metadata extraction
# - Branch info, commit history, remote URLs
# - Smart ignore patterns (standard, gitignore, custom)
# 
# ### **Directory Processing** 
# - Recursive file collection from any directory
# - Glob pattern support for file filtering
# - Flexible ignore strategies
# 
# ### **Three Presentation Modes**
# - **structure**: Directory tree view only
# - **metadata**: Tree + repository/directory info
# - **files**: Full file processing (default)
# 
# ### **Integration**
# - Works seamlessly with `Attachments()` class
# - Automatic file expansion and processing
# - Compatible with all existing presenters and refiners
# - Ready for LLM analysis

print("✅ Repository and directory processing demo completed!")
print("🚀 Ready to process entire codebases and directories!")
print("🎯 Perfect for giving whole projects to LLMs!") 