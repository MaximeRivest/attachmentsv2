"""Loader functions that transform files into attachment objects."""

from . import matchers
from .core import Attachment, loader, AttachmentCollection
import io
import os
import fnmatch
import glob
from pathlib import Path
from typing import List, Dict, Any

# --- URL DOWNLOADER ---
@loader(match=matchers.url_match)
def url_to_bs4(att: Attachment) -> Attachment:
    """Load URL content and parse with BeautifulSoup."""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(att.path, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Store the soup object
        att._obj = soup
        # Store some metadata
        att.metadata.update({
            'content_type': response.headers.get('content-type', ''),
            'status_code': response.status_code,
        })
        
        return att
    except ImportError:
        raise ImportError("requests and beautifulsoup4 are required for URL loading. Install with: pip install requests beautifulsoup4")

@loader(match=lambda att: att.path.startswith(('http://', 'https://')) and any(att.path.lower().endswith(ext) for ext in ['.pdf', '.pptx', '.ppt', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.jpg', '.jpeg', '.png', '.gif', '.bmp']))
def url_to_file(att: Attachment) -> Attachment:
    """Download file from URL and delegate to appropriate loader based on file extension."""
    try:
        import requests
        import tempfile
        import os
        from urllib.parse import urlparse
        from pathlib import Path
        
        # Parse URL to get file extension
        parsed_url = urlparse(att.path)
        url_path = parsed_url.path
        
        # Get file extension from URL
        file_ext = Path(url_path).suffix.lower()
        
        # Download the file
        response = requests.get(att.path, timeout=30)
        response.raise_for_status()
        
        # Create temporary file with correct extension
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        # Store original URL and temp path
        original_url = att.path
        att.path = temp_path
        att.metadata.update({
            'original_url': original_url,
            'temp_file_path': temp_path,
            'downloaded_from_url': True,
            'content_length': len(response.content),
            'content_type': response.headers.get('content-type', ''),
        })
        
        # Now delegate to the appropriate loader based on file extension
        if file_ext in ('.pdf',):
            return pdf_to_pdfplumber(att)
        elif file_ext in ('.pptx', '.ppt'):
            return pptx_to_python_pptx(att)
        elif file_ext in ('.docx', '.doc'):
            return docx_to_python_docx(att)
        elif file_ext in ('.xlsx', '.xls'):
            return excel_to_openpyxl(att)
        elif file_ext in ('.csv',):
            return csv_to_pandas(att)
        elif file_ext.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic', '.heif'):
            return image_to_pil(att)
        else:
            # If we don't recognize the extension, try to guess from content-type
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type:
                return pdf_to_pdfplumber(att)
            elif 'powerpoint' in content_type or 'presentation' in content_type:
                return pptx_to_python_pptx(att)
            elif 'word' in content_type or 'document' in content_type:
                return docx_to_python_docx(att)
            elif 'excel' in content_type or 'spreadsheet' in content_type:
                return excel_to_openpyxl(att)
            else:
                # Fallback: treat as text
                att._obj = response.text
                att.text = response.text
                return att
                
    except ImportError:
        raise ImportError("requests is required for URL loading. Install with: pip install requests")
    except Exception as e:
        # Clean up temp file if it was created
        if 'temp_file_path' in att.metadata:
            try:
                os.unlink(att.metadata['temp_file_path'])
            except:
                pass
        raise ValueError(f"Could not download or process URL: {e}")

# --- LOADERS ---
@loader(match=matchers.csv_match)
def csv_to_pandas(att: Attachment) -> Attachment:
    """Load CSV into pandas DataFrame."""
    try:
        import pandas as pd
        att._obj = pd.read_csv(att.path)
    except ImportError:
        raise ImportError("pandas is required for CSV loading. Install with: pip install pandas")
    return att


@loader(match=matchers.pdf_match)
def pdf_to_pdfplumber(att: Attachment) -> Attachment:
    """Load PDF using pdfplumber."""
    try:
        import pdfplumber
        
        # Try to create a temporary PDF with CropBox defined to silence warnings
        try:
            import pypdf
            from io import BytesIO
            import tempfile
            import os
            
            # Read the original PDF
            with open(att.path, 'rb') as f:
                pdf_bytes = f.read()
            
            # Process with pypdf to add CropBox
            reader = pypdf.PdfReader(BytesIO(pdf_bytes))
            writer = pypdf.PdfWriter()
            
            for page in reader.pages:
                # Set CropBox to MediaBox if not already defined
                if '/CropBox' not in page:
                    page.cropbox = page.mediabox
                writer.add_page(page)
            
            # Create a temporary file with the modified PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                writer.write(temp_file)
                temp_path = temp_file.name
            
            # Open the temporary PDF with pdfplumber
            att._obj = pdfplumber.open(temp_path)
            
            # Store the temp path for cleanup later
            att.metadata['temp_pdf_path'] = temp_path
            
        except (ImportError, Exception):
            # If CropBox fix fails, fall back to original file
            att._obj = pdfplumber.open(att.path)
            
    except ImportError:
        raise ImportError("pdfplumber is required for PDF loading. Install with: pip install pdfplumber")
    return att


@loader(match=matchers.pptx_match)
def pptx_to_python_pptx(att: Attachment) -> Attachment:
    """Load PowerPoint using python-pptx."""
    try:
        from pptx import Presentation
        att._obj = Presentation(att.path)
    except ImportError:
        raise ImportError("python-pptx is required for PowerPoint loading. Install with: pip install python-pptx")
    return att


@loader(match=matchers.docx_match)
def docx_to_python_docx(att: Attachment) -> Attachment:
    """Load Word document using python-docx."""
    try:
        from docx import Document
        att._obj = Document(att.path)
    except ImportError:
        raise ImportError("python-docx is required for Word document loading. Install with: pip install python-docx")
    return att


@loader(match=matchers.excel_match)
def excel_to_openpyxl(att: Attachment) -> Attachment:
    """Load Excel workbook using openpyxl."""
    try:
        from openpyxl import load_workbook
        att._obj = load_workbook(att.path, read_only=True)
    except ImportError:
        raise ImportError("openpyxl is required for Excel loading. Install with: pip install openpyxl")
    return att


@loader(match=matchers.image_match)
def image_to_pil(att: Attachment) -> Attachment:
    """Load image using PIL."""
    try:
        # Try to import pillow-heif for HEIC support if needed
        if att.path.lower().endswith(('.heic', '.heif')):
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
            except ImportError:
                pass  # Fall back to PIL's built-in support if available
        
        from PIL import Image
        att._obj = Image.open(att.path)
        
        # Store metadata
        att.metadata.update({
            'format': getattr(att._obj, 'format', 'Unknown'),
            'size': getattr(att._obj, 'size', (0, 0)),
            'mode': getattr(att._obj, 'mode', 'Unknown')
        })
        
    except ImportError:
        if att.path.lower().endswith(('.heic', '.heif')):
            raise ImportError("pillow-heif is required for HEIC loading. Install with: pip install pillow-heif")
        else:
            raise ImportError("Pillow is required for image loading. Install with: pip install Pillow")
    return att


@loader(match=matchers.text_match)
def text_to_string(att: Attachment) -> Attachment:
    """Load text files as strings."""
    with open(att.path, 'r', encoding='utf-8') as f:
        content = f.read()
        att._obj = content
        att.text = content
    return att


@loader(match=lambda att: att.path.lower().endswith(('.html', '.htm')))
def html_to_bs4(att: Attachment) -> Attachment:
    """Load HTML files and parse with BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
        
        with open(att.path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Store the soup object
        att._obj = soup
        # Store some metadata
        att.metadata.update({
            'content_type': 'text/html',
            'file_size': len(content),
        })
        
        return att
    except ImportError:
        raise ImportError("beautifulsoup4 is required for HTML loading. Install with: pip install beautifulsoup4")


@loader(match=matchers.zip_match)
def zip_to_images(att: Attachment) -> 'AttachmentCollection':
    """Load ZIP file containing images into AttachmentCollection."""
    try:
        import zipfile
        from PIL import Image
        from .core import AttachmentCollection, Attachment
        
        attachments = []
        
        with zipfile.ZipFile(att.path, 'r') as zip_file:
            for file_info in zip_file.filelist:
                if file_info.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic', '.heif')):
                    # Create attachment for each image
                    img_att = Attachment(file_info.filename)
                    
                    # Copy commands from original attachment (for vectorized processing)
                    img_att.commands = att.commands.copy()
                    
                    # Load image from zip
                    with zip_file.open(file_info.filename) as img_file:
                        img_data = img_file.read()
                        img = Image.open(io.BytesIO(img_data))
                        img_att._obj = img
                        
                        # Store metadata
                        img_att.metadata.update({
                            'format': getattr(img, 'format', 'Unknown'),
                            'size': getattr(img, 'size', (0, 0)),
                            'mode': getattr(img, 'mode', 'Unknown'),
                            'from_zip': att.path,
                            'zip_filename': file_info.filename
                        })
                    
                    attachments.append(img_att)
        
        return AttachmentCollection(attachments)
        
    except ImportError:
        raise ImportError("Pillow is required for image processing. Install with: pip install Pillow")
    except Exception as e:
        raise ValueError(f"Could not load ZIP file: {e}")


# --- DIRECTORY AND REPOSITORY PROCESSING ---

@loader(match=matchers.git_repo_match)
def git_repo_to_structure(att: Attachment) -> Attachment:
    """Load Git repository structure and file list.
    
    This loader focuses on loading the repository data structure.
    Use presenters for different output formats (structure, metadata, files).
    """
    import os
    
    # Get DSL parameters
    ignore_cmd = att.commands.get('ignore', 'standard')
    max_files = int(att.commands.get('max_files', '1000'))
    glob_pattern = att.commands.get('glob', '')
    
    # Convert to absolute path for consistent handling
    repo_path = os.path.abspath(att.path)
    
    # Get ignore patterns and collect files
    ignore_patterns = _get_ignore_patterns(repo_path, ignore_cmd)
    files = _collect_files(repo_path, ignore_patterns, max_files, glob_pattern)
    
    # Create repository structure object
    repo_structure = {
        'type': 'git_repository',
        'path': repo_path,
        'files': files,
        'ignore_patterns': ignore_patterns,
        'structure': _get_directory_structure(repo_path, files),
        'metadata': _get_repo_metadata(repo_path)
    }
    
    # Store the structure as the object
    att._obj = repo_structure
    
    # Also store file paths for simple API access
    att._file_paths = files
    
    # Update attachment metadata
    att.metadata.update(repo_structure['metadata'])
    att.metadata.update({
        'file_count': len(files),
        'ignore_patterns': ignore_patterns,
        'is_git_repo': True
    })
    
    return att


@loader(match=matchers.directory_or_glob_match)
def directory_to_structure(att: Attachment) -> Attachment:
    """Load directory or glob pattern structure and file list.
    
    This loader focuses on loading the directory data structure.
    Use presenters for different output formats (structure, metadata, files).
    """
    import os
    
    # Get DSL parameters
    ignore_cmd = att.commands.get('ignore', 'minimal')  # Less aggressive for non-Git dirs
    max_files = int(att.commands.get('max_files', '1000'))
    glob_pattern = att.commands.get('glob', '')
    recursive = att.commands.get('recursive', 'true').lower() == 'true'
    
    # Handle glob patterns in the path itself
    if matchers.glob_pattern_match(att):
        # Path contains glob patterns - use glob to find files
        files = _collect_files_from_glob(att.path, max_files)
        base_path = _get_glob_base_path(att.path)
    else:
        # Regular directory
        base_path = os.path.abspath(att.path)
        ignore_patterns = _get_ignore_patterns(base_path, ignore_cmd)
        files = _collect_files(base_path, ignore_patterns, max_files, glob_pattern, recursive)
    
    # Create directory structure object
    dir_structure = {
        'type': 'directory',
        'path': base_path,
        'files': files,
        'ignore_patterns': ignore_patterns if not matchers.glob_pattern_match(att) else [],
        'structure': _get_directory_structure(base_path, files),
        'metadata': _get_directory_metadata(base_path)
    }
    
    # Store the structure as the object
    att._obj = dir_structure
    
    # Also store file paths for simple API access
    att._file_paths = files
    
    # Update attachment metadata
    att.metadata.update(dir_structure['metadata'])
    att.metadata.update({
        'file_count': len(files),
        'is_git_repo': False
    })
    
    return att


# --- HELPER FUNCTIONS ---

def _get_ignore_patterns(base_path: str, ignore_command: str) -> List[str]:
    """Get ignore patterns based on DSL command."""
    if ignore_command == 'standard':
        return [
            '.git', '.git/*', '**/.git/*',
            'node_modules', 'node_modules/*', '**/node_modules/*',
            '__pycache__', '__pycache__/*', '**/__pycache__/*',
            '.venv', '.venv/*', '**/.venv/*',
            'venv', 'venv/*', '**/venv/*',
            '.env', '.env.*',
            '*.log', '*.tmp', '*.cache',
            '.DS_Store', 'Thumbs.db',
            'dist', 'build', 'target',
            '*.pyc', '*.pyo', '*.pyd',
            '.pytest_cache', '.coverage',
            '.idea', '.vscode'
        ]
    elif ignore_command == 'minimal':
        return [
            '.git', '.git/*', '**/.git/*',
            '__pycache__', '__pycache__/*', '**/__pycache__/*',
            '*.pyc', '*.pyo', '*.pyd',
            '.DS_Store', 'Thumbs.db'
        ]
    elif ignore_command == 'gitignore':
        # Parse .gitignore file
        gitignore_path = os.path.join(base_path, '.gitignore')
        patterns = []
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception:
                pass
        return patterns
    elif ignore_command:
        # Custom comma-separated patterns
        return [pattern.strip() for pattern in ignore_command.split(',')]
    else:
        # No ignore patterns
        return []


def _should_ignore(file_path: str, base_path: str, ignore_patterns: List[str]) -> bool:
    """Check if file should be ignored based on patterns."""
    # Get relative path from base
    try:
        rel_path = os.path.relpath(file_path, base_path)
    except ValueError:
        return True  # Outside base path, ignore
    
    # Normalize path separators
    rel_path = rel_path.replace('\\', '/')
    
    for pattern in ignore_patterns:
        # Handle different pattern types
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(os.path.basename(rel_path), pattern):
            return True
        # Handle directory patterns
        if pattern.endswith('/') and rel_path.startswith(pattern):
            return True
        # Handle glob patterns
        if '**' in pattern:
            # Convert ** patterns to fnmatch
            glob_pattern = pattern.replace('**/', '*/')
            if fnmatch.fnmatch(rel_path, glob_pattern):
                return True
    
    return False


def _collect_files(base_path: str, ignore_patterns: List[str], max_files: int = 1000, 
                  glob_pattern: str = '', recursive: bool = True) -> List[str]:
    """Collect all files in directory, respecting ignore patterns and glob filters."""
    files = []
    
    if recursive:
        # Recursive directory walk
        for root, dirs, filenames in os.walk(base_path):
            # Filter directories to avoid walking into ignored ones
            dirs[:] = [d for d in dirs if not _should_ignore(os.path.join(root, d), base_path, ignore_patterns)]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                # Skip if ignored
                if _should_ignore(file_path, base_path, ignore_patterns):
                    continue
                
                # Skip binary files (basic heuristic)
                if _is_likely_binary(file_path):
                    continue
                
                # Apply glob filter if specified
                if glob_pattern and not _matches_glob_pattern(file_path, base_path, glob_pattern):
                    continue
                
                files.append(file_path)
                
                # Limit number of files to prevent overwhelming
                if len(files) >= max_files:
                    break
            
            if len(files) >= max_files:
                break
    else:
        # Non-recursive - just files in the directory
        try:
            for filename in os.listdir(base_path):
                file_path = os.path.join(base_path, filename)
                
                # Skip directories in non-recursive mode
                if os.path.isdir(file_path):
                    continue
                
                # Skip if ignored
                if _should_ignore(file_path, base_path, ignore_patterns):
                    continue
                
                # Skip binary files
                if _is_likely_binary(file_path):
                    continue
                
                # Apply glob filter if specified
                if glob_pattern and not _matches_glob_pattern(file_path, base_path, glob_pattern):
                    continue
                
                files.append(file_path)
                
                if len(files) >= max_files:
                    break
        except OSError:
            pass
    
    return sorted(files)


def _collect_files_from_glob(glob_path: str, max_files: int = 1000) -> List[str]:
    """Collect files using glob pattern."""
    files = []
    
    try:
        # Use glob to find matching files
        matches = glob.glob(glob_path, recursive=True)
        
        for file_path in matches:
            # Skip directories
            if os.path.isdir(file_path):
                continue
            
            # Skip binary files
            if _is_likely_binary(file_path):
                continue
            
            files.append(os.path.abspath(file_path))
            
            if len(files) >= max_files:
                break
                
    except Exception:
        pass
    
    return sorted(files)


def _get_glob_base_path(glob_path: str) -> str:
    """Extract base directory from glob pattern."""
    # Find the first directory part without glob characters
    parts = glob_path.split(os.sep)
    base_parts = []
    
    for part in parts:
        if any(char in part for char in ['*', '?', '[', ']']):
            break
        base_parts.append(part)
    
    if base_parts:
        return os.path.join(*base_parts) if len(base_parts) > 1 else base_parts[0]
    else:
        return os.getcwd()


def _matches_glob_pattern(file_path: str, base_path: str, glob_pattern: str) -> bool:
    """Check if file matches glob pattern."""
    rel_path = os.path.relpath(file_path, base_path)
    filename = os.path.basename(file_path)
    
    # Split multiple patterns by comma
    patterns = [p.strip() for p in glob_pattern.split(',')]
    
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(rel_path, pattern):
            return True
    
    return False


def _is_likely_binary(file_path: str) -> bool:
    """Basic heuristic to detect binary files."""
    binary_extensions = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.obj', '.o',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.pyc', '.pyo', '.pyd', '.class',
        '.woff', '.woff2', '.ttf', '.otf', '.eot'
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext in binary_extensions:
        return True
    
    # Check file size (skip very large files)
    try:
        if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
            return True
    except OSError:
        return True
    
    # Try to read first few bytes to detect binary content
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            # If chunk contains null bytes, likely binary
            if b'\x00' in chunk:
                return True
    except (OSError, UnicodeDecodeError):
        return True
    
    return False


def _get_directory_structure(base_path: str, files: List[str]) -> Dict[str, Any]:
    """Generate tree structure representation with detailed file metadata."""
    import stat
    import pwd
    import grp
    import time
    from datetime import datetime
    
    structure = {}
    
    # Also include directories in the structure
    directories = set()
    for file_path in files:
        rel_path = os.path.relpath(file_path, base_path)
        parts = rel_path.split(os.sep)
        
        # Collect all directory paths
        for i in range(len(parts) - 1):
            dir_path = os.path.join(base_path, *parts[:i+1])
            directories.add(dir_path)
    
    # Process directories first
    for dir_path in sorted(directories):
        rel_path = os.path.relpath(dir_path, base_path)
        parts = rel_path.split(os.sep)
        
        current = structure
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Add directory info
        try:
            stat_info = os.stat(dir_path)
            current[parts[-1]] = {
                'type': 'directory',
                'size': stat_info.st_size,
                'modified': stat_info.st_mtime,
                'permissions': stat.filemode(stat_info.st_mode),
                'owner': _get_owner_name(stat_info.st_uid),
                'group': _get_group_name(stat_info.st_gid),
                'mode_octal': oct(stat_info.st_mode)[-3:],
                'inode': stat_info.st_ino,
                'links': stat_info.st_nlink,
                'modified_str': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
        except OSError:
            current[parts[-1]] = {
                'type': 'directory', 
                'size': 0, 
                'modified': 0,
                'permissions': '?---------',
                'owner': 'unknown',
                'group': 'unknown',
                'mode_octal': '000',
                'inode': 0,
                'links': 0,
                'modified_str': 'unknown'
            }
    
    # Process files
    for file_path in files:
        rel_path = os.path.relpath(file_path, base_path)
        parts = rel_path.split(os.sep)
        
        current = structure
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Add file info with detailed metadata
        try:
            stat_info = os.stat(file_path)
            current[parts[-1]] = {
                'type': 'file',
                'size': stat_info.st_size,
                'modified': stat_info.st_mtime,
                'permissions': stat.filemode(stat_info.st_mode),
                'owner': _get_owner_name(stat_info.st_uid),
                'group': _get_group_name(stat_info.st_gid),
                'mode_octal': oct(stat_info.st_mode)[-3:],
                'inode': stat_info.st_ino,
                'links': stat_info.st_nlink,
                'modified_str': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
        except OSError:
            current[parts[-1]] = {
                'type': 'file', 
                'size': 0, 
                'modified': 0,
                'permissions': '?---------',
                'owner': 'unknown',
                'group': 'unknown',
                'mode_octal': '000',
                'inode': 0,
                'links': 0,
                'modified_str': 'unknown'
            }
    
    return structure


def _get_owner_name(uid: int) -> str:
    """Get username from UID."""
    try:
        import pwd
        return pwd.getpwuid(uid).pw_name
    except (KeyError, ImportError):
        return str(uid)


def _get_group_name(gid: int) -> str:
    """Get group name from GID."""
    try:
        import grp
        return grp.getgrgid(gid).gr_name
    except (KeyError, ImportError):
        return str(gid)


def _get_repo_metadata(repo_path: str) -> Dict[str, Any]:
    """Extract Git repository metadata."""
    metadata = {
        'repo_path': repo_path,
        'is_git_repo': True
    }
    
    try:
        # Try to get Git info using GitPython if available
        import git
        repo = git.Repo(repo_path)
        
        metadata.update({
            'current_branch': repo.active_branch.name,
            'commit_count': len(list(repo.iter_commits())),
            'last_commit': {
                'hash': repo.head.commit.hexsha[:8],
                'message': repo.head.commit.message.strip(),
                'author': str(repo.head.commit.author),
                'date': repo.head.commit.committed_datetime.isoformat()
            },
            'remotes': [remote.name for remote in repo.remotes],
            'is_dirty': repo.is_dirty()
        })
        
        # Get remote URL if available
        if repo.remotes:
            try:
                metadata['remote_url'] = repo.remotes.origin.url
            except:
                pass
                
    except ImportError:
        # GitPython not available, use basic Git commands
        try:
            import subprocess
            
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  cwd=repo_path, capture_output=True, text=True)
            if result.returncode == 0:
                metadata['current_branch'] = result.stdout.strip()
            
            # Get last commit info
            result = subprocess.run(['git', 'log', '-1', '--format=%H|%s|%an|%ai'], 
                                  cwd=repo_path, capture_output=True, text=True)
            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                if len(parts) >= 4:
                    metadata['last_commit'] = {
                        'hash': parts[0][:8],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    }
        except Exception:
            pass
    except Exception:
        pass
    
    return metadata


def _get_directory_metadata(dir_path: str) -> Dict[str, Any]:
    """Extract basic directory metadata."""
    metadata = {
        'directory_path': dir_path,
        'is_git_repo': False
    }
    
    try:
        # Basic directory info
        stat = os.stat(dir_path)
        metadata.update({
            'directory_name': os.path.basename(dir_path),
            'modified': stat.st_mtime,
            'absolute_path': os.path.abspath(dir_path)
        })
    except OSError:
        pass
    
    return metadata


# Formatting functions moved to present.py - removed to avoid duplication
