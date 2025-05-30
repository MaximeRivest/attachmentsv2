from typing import Any, Dict, List, Optional, Union, Callable, get_type_hints
from functools import wraps, partial
import re
import base64
import io
from pathlib import Path

class Pipeline:
    """A callable pipeline that can be applied to attachments."""
    
    def __init__(self, steps: List[Callable] = None, fallback_pipelines: List['Pipeline'] = None):
        self.steps = steps or []
        self.fallback_pipelines = fallback_pipelines or []
    
    def __or__(self, other: Union[Callable, 'Pipeline']) -> 'Pipeline':
        """Chain this pipeline with another step or pipeline."""
        if isinstance(other, Pipeline):
            # If both are pipelines, create a new pipeline with fallback logic
            if self.steps and other.steps:
                # This is chaining two complete pipelines - treat as fallback
                return Pipeline(self.steps, [other] + other.fallback_pipelines)
            elif not self.steps:
                # If self is empty, just return other
                return other
            else:
                # Concatenate steps
                return Pipeline(self.steps + other.steps, other.fallback_pipelines)
        else:
            # Adding a single step to the pipeline
            return Pipeline(self.steps + [other], self.fallback_pipelines)
    
    def __call__(self, input_: Union[str, 'Attachment']) -> Any:
        """Apply the pipeline to an input."""
        if isinstance(input_, str):
            result = Attachment(input_)
        else:
            result = input_
        
        # Try the main pipeline first
        try:
            return self._execute_steps(result, self.steps)
        except Exception as e:
            # If the main pipeline fails, try fallback pipelines
            for fallback in self.fallback_pipelines:
                try:
                    return fallback(input_)
                except:
                    continue
            # If all pipelines fail, raise the original exception
            raise e
    
    def _execute_steps(self, result: 'Attachment', steps: List[Callable]) -> Any:
        """Execute a list of steps on an attachment."""
        for step in steps:
            result = step(result)
            if result is None:
                # If step returns None, keep the previous result
                continue
            if not isinstance(result, (Attachment, AttachmentCollection)):
                # If step returns something else (like an adapter result), return it directly
                # This allows adapters to "exit" the pipeline and return their result
                return result
        
        return result
    
    def __getattr__(self, name: str):
        """Allow calling adapters as methods on pipelines."""
        if name in _adapters:
            def adapter_method(input_: Union[str, 'Attachment'], *args, **kwargs):
                # Apply pipeline first, then adapter
                result = self(input_)
                adapter_fn = _adapters[name]
                return adapter_fn(result, *args, **kwargs)
            return adapter_method
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __repr__(self) -> str:
        step_names = [getattr(step, '__name__', str(step)) for step in self.steps]
        main_pipeline = f"Pipeline({' | '.join(step_names)})"
        if self.fallback_pipelines:
            fallback_names = [repr(fp) for fp in self.fallback_pipelines]
            return f"{main_pipeline} with fallbacks: [{', '.join(fallback_names)}]"
        return main_pipeline

class AdditivePipeline:
    """A pipeline that applies presenters additively, preserving existing content."""
    
    def __init__(self, steps: List[Callable] = None):
        self.steps = steps or []
    
    def __call__(self, input_: Union[str, 'Attachment']) -> 'Attachment':
        """Apply additive pipeline - each step adds to existing content."""
        if isinstance(input_, str):
            result = Attachment(input_)
        else:
            result = input_
        
        for step in self.steps:
            # Apply each step to the original attachment
            # Each presenter should preserve existing content and add new content
            result = step(result)
            if result is None:
                continue
        
        return result
    
    def __add__(self, other: Union[Callable, 'AdditivePipeline']) -> 'AdditivePipeline':
        """Chain additive pipelines."""
        if isinstance(other, AdditivePipeline):
            return AdditivePipeline(self.steps + other.steps)
        else:
            return AdditivePipeline(self.steps + [other])
    
    def __or__(self, other: Union[Callable, Pipeline]) -> Pipeline:
        """Convert to regular pipeline when using | operator."""
        return Pipeline([self]) | other
    
    def __repr__(self) -> str:
        step_names = [getattr(step, '__name__', str(step)) for step in self.steps]
        return f"AdditivePipeline({' + '.join(step_names)})"

class AttachmentCollection:
    """A collection of attachments that supports vectorized operations."""
    
    def __init__(self, attachments: List['Attachment']):
        self.attachments = attachments or []
    
    def __or__(self, operation: Union[Callable, Pipeline]) -> Union['AttachmentCollection', 'Attachment']:
        """Apply operation - vectorize or reduce based on operation type."""
        
        # Check if this is a reducing operation (operates on collections)
        if self._is_reducer(operation):
            # Apply to the collection as a whole (reduction)
            return operation(self)
        else:
            # Apply to each attachment (vectorization)
            results = []
            for att in self.attachments:
                result = operation(att)
                if result is not None:
                    results.append(result)
            return AttachmentCollection(results)
    
    def __add__(self, other: Union[Callable, Pipeline]) -> 'AttachmentCollection':
        """Apply additive operation to each attachment."""
        results = []
        for att in self.attachments:
            result = att + other
            if result is not None:
                results.append(result)
        return AttachmentCollection(results)
    
    def _is_reducer(self, operation) -> bool:
        """Check if an operation is a reducer (combines multiple attachments)."""
        # Check if it's a refiner that works on collections
        if hasattr(operation, 'name'):
            reducing_operations = {
                'tile_images', 'combine_images', 'merge_text', 
                'claude', 'openai_chat', 'openai_response'  # Adapters are always reducers
            }
            return operation.name in reducing_operations
        return False
    
    def to_attachment(self) -> 'Attachment':
        """Convert collection to single attachment by combining content."""
        if not self.attachments:
            return Attachment("")
        
        # Create a new attachment that combines all content
        combined = Attachment("")
        combined.text = "\n\n".join(att.text for att in self.attachments if att.text)
        combined.images = [img for att in self.attachments for img in att.images]
        combined.audio = [audio for att in self.attachments for audio in att.audio]
        
        # Combine metadata
        combined.metadata = {
            'collection_size': len(self.attachments),
            'combined_from': [att.path for att in self.attachments]
        }
        
        return combined
    
    def __len__(self) -> int:
        return len(self.attachments)
    
    def __getitem__(self, index: int) -> 'Attachment':
        return self.attachments[index]
    
    def __repr__(self) -> str:
        return f"AttachmentCollection({len(self.attachments)} attachments)"

class Attachment:
    """Simple container for file processing."""
    
    def __init__(self, attachy: str = ""):
        self.attachy = attachy
        self.path, self.commands = self._parse_attachy()
        
        self._obj: Optional[Any] = None
        self.text: str = ""
        self.images: List[str] = []
        self.audio: List[str] = []
        self.metadata: Dict[str, Any] = {}
        
        self.pipeline: List[str] = []
    
    def _parse_attachy(self) -> tuple[str, Dict[str, str]]:
        if not self.attachy:
            return "", {}
        
        commands = {}
        def extract_command(match):
            key, value = match.group(1), match.group(2)
            commands[key.strip()] = value.strip()
            return ""
        
        path = re.sub(r'\[([^:]+):([^\]]+)\]', extract_command, self.attachy).strip()
        return path, commands
    
    def __or__(self, verb: Union[Callable, Pipeline]) -> Union['Attachment', 'AttachmentCollection', Pipeline]:
        """Support both immediate application and pipeline creation."""
        if isinstance(verb, Pipeline):
            # Apply pipeline to this attachment
            return verb(self)
        else:
            # Apply single verb
            result = verb(self)
            if result is None:
                result = self
            if isinstance(result, Attachment):
                result.pipeline.append(getattr(verb, '__name__', str(verb)))
            elif isinstance(result, AttachmentCollection):
                # For collections, add the pipeline step to each attachment
                for att in result.attachments:
                    att.pipeline.append(getattr(verb, '__name__', str(verb)))
            return result
    
    def __getattr__(self, name: str):
        """Allow calling adapters as methods on attachments."""
        if name in _adapters:
            def adapter_method(*args, **kwargs):
                adapter_fn = _adapters[name]
                return adapter_fn(self, *args, **kwargs)
            return adapter_method
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __add__(self, other: Union[Callable, 'Pipeline']) -> 'Attachment':
        """Support additive composition for presenters: present.text + present.images"""
        if isinstance(other, (VerbFunction, Pipeline)):
            # Apply the presenter additively (should preserve existing content)
            result = other(self)
            return result if result is not None else self
        else:
            raise TypeError(f"Cannot add {type(other)} to Attachment")
    
    def __repr__(self) -> str:
        # Show shortened base64 for images
        img_info = ""
        if self.images:
            img_count = len([img for img in self.images if img and not img.endswith('_placeholder')])
            if img_count > 0:
                first_img = next((img for img in self.images if img and not img.endswith('_placeholder')), "")
                if first_img:
                    if first_img.startswith('data:image/'):
                        img_preview = f"{first_img[:30]}...{first_img[-10:]}"
                    else:
                        img_preview = f"{first_img[:20]}...{first_img[-10:]}"
                    img_info = f", images=[{img_count} imgs: {img_preview}]"
                else:
                    img_info = f", images={img_count}"
        
        return f"Attachment(path='{self.path}', text={len(self.text)} chars{img_info}, pipeline={self.pipeline})"
    
    def __str__(self) -> str:
        """Return the text content for f-string formatting."""
        return self.text if self.text else f"[No text content from {self.path}]"
    
    def cleanup(self):
        """Clean up any temporary resources associated with this attachment."""
        # Clean up temporary PDF files
        if 'temp_pdf_path' in self.metadata:
            try:
                import os
                temp_path = self.metadata['temp_pdf_path']
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                del self.metadata['temp_pdf_path']
            except Exception:
                # If cleanup fails, just continue
                pass
        
        # Clean up temporary files downloaded from URLs
        if 'temp_file_path' in self.metadata:
            try:
                import os
                temp_path = self.metadata['temp_file_path']
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                del self.metadata['temp_file_path']
            except Exception:
                # If cleanup fails, just continue
                pass
        
        # Close any open file objects
        if hasattr(self._obj, 'close'):
            try:
                self._obj.close()
            except Exception:
                pass
    
    def __del__(self):
        """Destructor to ensure cleanup when attachment is garbage collected."""
        try:
            self.cleanup()
        except Exception:
            # Ignore errors during cleanup in destructor
            pass


# --- REGISTRATION SYSTEM ---

_loaders = {}
_modifiers = {}
_presenters = {}
_adapters = {}
_refiners = {}


def loader(match: Callable[[Attachment], bool]):
    """Register a loader function with a match predicate."""
    def decorator(func):
        _loaders[func.__name__] = (match, func)
        return func
    return decorator


def modifier(func):
    """Register a modifier function with type dispatch."""
    import inspect
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    
    if len(params) >= 2:
        type_hint = params[1].annotation
        if type_hint != inspect.Parameter.empty:
            key = func.__name__
            if key not in _modifiers:
                _modifiers[key] = []
            _modifiers[key].append((type_hint, func))
            return func
    
    key = func.__name__
    if key not in _modifiers:
        _modifiers[key] = []
    _modifiers[key].append((None, func))
    return func


def presenter(func=None, *, category=None):
    """Register a presenter function with type dispatch and smart DSL filtering.
    
    Args:
        func: The presenter function to register
        category: Optional explicit category ('text', 'image', or None for auto-detection)
        
    Examples:
        @presenter
        def auto_detected(att, data): ...  # Auto-detects based on what it modifies
        
        @presenter(category='text')
        def explicit_text(att, data): ...  # Explicitly categorized as text
        
        @presenter(category='image') 
        def explicit_image(att, data): ...  # Explicitly categorized as image
    """
    def decorator(func):
        import inspect
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        
        # Create a smart wrapper that handles DSL command filtering
        @wraps(func)
        def smart_presenter_wrapper(att: Attachment, *args, **kwargs):
            """Smart presenter wrapper that filters based on DSL commands."""
            
            # Get presenter name and category
            presenter_name = func.__name__
            presenter_category = category
            
            # Auto-detect category if not explicitly provided
            if presenter_category is None:
                presenter_category = _detect_presenter_category(func, presenter_name)
            
            # Get DSL commands with cleaner approach
            include_images = att.commands.get('images', 'true').lower() != 'false'  # Images on by default
            text_format = att.commands.get('format', 'markdown')  # How to format text: plain|markdown|code
            
            # Apply image filtering (images can be turned off)
            if not include_images and presenter_category == 'image':
                # Skip image presenters if images are disabled
                return att
            
            # Apply text format filtering - only for text presenters
            if presenter_category == 'text':
                # Normalize format aliases and map to presenter names
                if text_format in ('plain', 'text', 'txt'):
                    preferred_presenter = 'text'
                elif text_format in ('markdown', 'md'):
                    preferred_presenter = 'markdown'
                elif text_format in ('code', 'structured', 'html', 'xml', 'json'):
                    # For code formats, prefer structured presenters, fallback to markdown
                    if presenter_name in ('html', 'xml', 'csv'):
                        # Let structured presenters run for code format
                        preferred_presenter = presenter_name
                    else:
                        preferred_presenter = 'markdown'  # Fallback for code format
                else:
                    preferred_presenter = 'markdown'  # Default
                
                # Check if the preferred presenter exists for this object type
                # If not, allow any text presenter to run (fallback behavior)
                if presenter_name in ('text', 'markdown'):
                    if att._obj is not None:
                        # Check if preferred presenter exists for this object type
                        obj_type = type(att._obj)
                        preferred_exists = False
                        
                        if preferred_presenter in _presenters:
                            for expected_type, handler_fn in _presenters[preferred_presenter]:
                                # Skip fallback handlers (None type) - they don't count as type-specific
                                if expected_type is None:
                                    continue
                                try:
                                    if isinstance(expected_type, str):
                                        expected_class_name = expected_type.split('.')[-1]
                                        if expected_class_name in obj_type.__name__ or obj_type.__name__ == expected_class_name:
                                            preferred_exists = True
                                            break
                                    elif isinstance(att._obj, expected_type):
                                        preferred_exists = True
                                        break
                                except (TypeError, AttributeError):
                                    continue
                        
                        # Only skip if preferred presenter exists AND this isn't the preferred one
                        if preferred_exists and presenter_name != preferred_presenter:
                            return att
                    else:
                        # No object loaded yet, use original filtering logic
                        if presenter_name != preferred_presenter:
                            return att
            
            # If we get here, the presenter should run
            return func(att, *args, **kwargs)
        
        # Register the smart wrapper instead of the original function
        if len(params) >= 2:
            type_hint = params[1].annotation
            if type_hint != inspect.Parameter.empty:
                key = func.__name__
                if key not in _presenters:
                    _presenters[key] = []
                _presenters[key].append((type_hint, smart_presenter_wrapper))
                return smart_presenter_wrapper
        
        key = func.__name__
        if key not in _presenters:
            _presenters[key] = []
        _presenters[key].append((None, smart_presenter_wrapper))
        return smart_presenter_wrapper
    
    # Handle both @presenter and @presenter(category='text') syntax
    if func is None:
        # Called with parameters: @presenter(category='text')
        return decorator
    else:
        # Called without parameters: @presenter
        return decorator(func)


def _detect_presenter_category(func: Callable, presenter_name: str) -> str:
    """Automatically detect presenter category based on function behavior and name.
    
    Returns:
        'text': Presenter that primarily works with text content
        'image': Presenter that primarily works with images  
    """
    
    # Auto-detect based on function name patterns
    text_patterns = ['text', 'markdown', 'csv', 'xml', 'html', 'json', 'yaml', 'summary', 'head', 'metadata']
    image_patterns = ['image', 'thumbnail', 'chart', 'graph', 'plot', 'visual', 'photo', 'picture']
    
    name_lower = presenter_name.lower()
    
    # Check for image patterns first (more specific)
    if any(pattern in name_lower for pattern in image_patterns):
        return 'image'
    
    # Check for text patterns
    if any(pattern in name_lower for pattern in text_patterns):
        return 'text'
    
    # Try to analyze the function source code for hints (best effort)
    try:
        import inspect
        source = inspect.getsource(func)
        
        # Count references to text vs image operations
        text_indicators = source.count('att.text') + source.count('.text ') + source.count('text =')
        image_indicators = source.count('att.images') + source.count('.images') + source.count('images.append')
        
        if image_indicators > text_indicators:
            return 'image'
        elif text_indicators > 0:
            return 'text'
    except:
        # If source analysis fails, fall back to safe default
        pass
    
    # Default to 'text' for unknown presenters (safe default - always runs)
    return 'text'


def adapter(func):
    """Register an adapter function."""
    _adapters[func.__name__] = func
    return func


def refiner(func):
    """Register a refiner function that operates on presented content."""
    _refiners[func.__name__] = func
    return func


# --- VERB NAMESPACES ---

class VerbFunction:
    """A wrapper for verb functions that supports both direct calls and pipeline creation."""
    
    def __init__(self, func: Callable, name: str, args=None, kwargs=None, is_loader=False):
        self.func = func
        self.name = name
        self.__name__ = name
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.is_loader = is_loader
    
    def __call__(self, *args, **kwargs) -> Union[Attachment, 'VerbFunction']:
        """Support both att | verb() and verb(args) | other_verb patterns."""
        if len(args) == 1 and isinstance(args[0], Attachment) and not kwargs and not self.args and not self.kwargs:
            # Direct application: verb(attachment)
            return self.func(args[0])
        elif len(args) == 1 and isinstance(args[0], Attachment) and (kwargs or self.args or self.kwargs):
            # Apply with stored or provided arguments
            return self._apply_with_args(args[0], *(self.args + args[1:]), **{**self.kwargs, **kwargs})
        elif len(args) == 1 and isinstance(args[0], str) and self.is_loader and not kwargs and not self.args and not self.kwargs:
            # Special case: loader called with string path - create attachment and apply
            att = Attachment(args[0])
            return self.func(att)
        elif args or kwargs:
            # Partial application: verb(arg1, arg2) returns a new VerbFunction with stored args
            return VerbFunction(self.func, self.name, self.args + args, {**self.kwargs, **kwargs}, self.is_loader)
        else:
            # No args, return self for pipeline creation
            return self
    
    def _apply_with_args(self, att: Attachment, *args, **kwargs):
        """Apply the function with additional arguments."""
        
        # Check if the function can accept additional arguments
        import inspect
        sig = inspect.signature(self.func)
        params = list(sig.parameters.values())
        
        # Check if this is an adapter (has *args, **kwargs) vs modifier/presenter (fixed params)
        has_var_args = any(p.kind == p.VAR_POSITIONAL for p in params)
        has_var_kwargs = any(p.kind == p.VAR_KEYWORD for p in params)
        
        if has_var_args and has_var_kwargs:
            # This is an adapter - pass arguments directly
            return self.func(att, *args, **kwargs)
        else:
            # This is a modifier/presenter - set commands and call with minimal args
            if args and hasattr(att, 'commands'):
                # Assume first argument is the command value for this verb
                att.commands[self.name] = str(args[0])
            
            # If function only takes 1 parameter (just att) or 2 parameters (att + obj type),
            # don't pass additional args - the commands are already set
            if len(params) <= 2:
                return self.func(att)
            else:
                # Function can take additional arguments
                return self.func(att, *args, **kwargs)
    
    def __or__(self, other: Union[Callable, Pipeline]) -> Pipeline:
        """Create a pipeline when using | operator."""
        return Pipeline([self]) | other
    
    def __add__(self, other: Union[Callable, 'VerbFunction', Pipeline]) -> 'AdditivePipeline':
        """Create an additive pipeline when using + operator."""
        return AdditivePipeline([self, other])
    
    def __repr__(self) -> str:
        args_str = ""
        if self.args or self.kwargs:
            args_str = f"({', '.join(map(str, self.args))}{', ' if self.args and self.kwargs else ''}{', '.join(f'{k}={v}' for k, v in self.kwargs.items())})"
        return f"VerbFunction({self.name}{args_str})"

class VerbNamespace:
    def __init__(self, registry):
        self._registry = registry
    
    def __getattr__(self, name: str) -> VerbFunction:
        if name in self._registry:
            if isinstance(self._registry[name], tuple):
                wrapper = self._make_loader_wrapper(name)
                return VerbFunction(wrapper, name, is_loader=True)
            elif isinstance(self._registry[name], list):
                wrapper = self._make_dispatch_wrapper(name)
                return VerbFunction(wrapper, name)
            else:
                wrapper = self._make_adapter_wrapper(name)
                return VerbFunction(wrapper, name)
        
        raise AttributeError(f"No verb '{name}' registered")
    
    def _make_loader_wrapper(self, name: str):
        """Create a wrapper that converts strings to Attachments."""
        match_fn, loader_fn = self._registry[name]
        
        @wraps(loader_fn)
        def wrapper(input_: Union[str, Attachment]) -> Attachment:
            if isinstance(input_, str):
                att = Attachment(input_)
            else:
                att = input_
            
            # Skip loading if already loaded (default behavior for all loaders)
            if att._obj is not None:
                return att
            
            if match_fn(att):
                return loader_fn(att)
            else:
                # Skip gracefully if this loader doesn't match - enables chaining
                return att
        
        return wrapper
    
    def _make_dispatch_wrapper(self, name: str):
        """Create a wrapper that dispatches based on object type."""
        handlers = self._registry[name]
        
        @wraps(handlers[0][1])
        def wrapper(att: Attachment) -> Union[Attachment, AttachmentCollection]:
            if att._obj is None:
                # Use fallback handler
                for expected_type, handler_fn in handlers:
                    if expected_type is None:
                        return handler_fn(att)
                return att
            
            obj_type_name = type(att._obj).__name__
            
            # Try to find a matching handler based on type annotations
            for expected_type, handler_fn in handlers:
                if expected_type is None:
                    continue
                    
                try:
                    # Handle string type annotations
                    if isinstance(expected_type, str):
                        # Generic type name matching - extract the class name from module.ClassName
                        expected_class_name = expected_type.split('.')[-1]
                        if expected_class_name in obj_type_name or obj_type_name == expected_class_name:
                            return handler_fn(att, att._obj)
                    elif isinstance(att._obj, expected_type):
                        return handler_fn(att, att._obj)
                except (TypeError, AttributeError):
                    continue
            
            # Fallback to first handler with no type requirement
            for expected_type, handler_fn in handlers:
                if expected_type is None:
                    return handler_fn(att)
            
            return att
        
        return wrapper
    
    def _make_adapter_wrapper(self, name: str):
        """Create a wrapper for adapter functions."""
        adapter_fn = self._registry[name]
        
        # Don't use @wraps here because it copies the original function's signature,
        # but we need to preserve the *args, **kwargs signature for VerbFunction detection
        def wrapper(att: Attachment, *args, **kwargs):
            # Call the adapter and return result directly (exit the attachment pipeline)
            result = adapter_fn(att, *args, **kwargs)
            return result
        
        # Manually copy some attributes without affecting the signature
        wrapper.__name__ = getattr(adapter_fn, '__name__', name)
        wrapper.__doc__ = getattr(adapter_fn, '__doc__', None)
        
        return wrapper


class SmartVerbNamespace(VerbNamespace):
    """VerbNamespace with __dir__ support for runtime autocomplete."""
    
    def __init__(self, registry):
        super().__init__(registry)

    def __dir__(self):
        """Return list of attributes for IDE autocomplete."""
        # Get the default attributes
        attrs = set(object.__dir__(self))
        
        # Add all registered function names
        attrs.update(self._registry.keys())
        
        return sorted(attrs)

    @property
    def __all__(self):
        """Provide __all__ for static analysis tools."""
        return list(self._registry.keys())

    def register_new_function(self, name):
        """Call this when dynamically adding new functions."""
        # Functions will be accessible via __getattr__
        pass


# Helper functions for convenient attachment creation
def attach(path: str) -> Attachment:
    """Create an Attachment from a file path."""
    return Attachment(path)

def A(path: str) -> Attachment:
    """Short alias for attach()."""
    return Attachment(path)


