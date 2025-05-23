from typing import Any, Dict, List, Optional, Union, Callable, get_type_hints
from functools import wraps
import re
import base64
import io
from pathlib import Path

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
    
    def __or__(self, verb: Callable) -> 'Attachment':
        result = verb(self)
        if result is None:
            result = self
        result.pipeline.append(getattr(verb, '__name__', str(verb)))
        return result
    
    def __repr__(self) -> str:
        return f"Attachment(path='{self.path}', text={len(self.text)} chars, images={len(self.images)}, pipeline={self.pipeline})"


# --- REGISTRATION SYSTEM ---

_loaders = {}
_modifiers = {}
_presenters = {}
_adapters = {}


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


def presenter(func):
    """Register a presenter function with type dispatch."""
    import inspect
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    
    if len(params) >= 2:
        type_hint = params[1].annotation
        if type_hint != inspect.Parameter.empty:
            key = func.__name__
            if key not in _presenters:
                _presenters[key] = []
            _presenters[key].append((type_hint, func))
            return func
    
    key = func.__name__
    if key not in _presenters:
        _presenters[key] = []
    _presenters[key].append((None, func))
    return func


def adapter(func):
    """Register an adapter function."""
    _adapters[func.__name__] = func
    return func


# --- VERB NAMESPACES ---

class VerbNamespace:
    def __init__(self, registry):
        self._registry = registry
    
    def __getattr__(self, name: str) -> Callable:
        if name in self._registry:
            if isinstance(self._registry[name], tuple):
                return self._make_loader_wrapper(name)
            elif isinstance(self._registry[name], list):
                return self._make_dispatch_wrapper(name)
            else:
                return self._registry[name]
        
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
            
            if match_fn(att):
                return loader_fn(att)
            else:
                raise ValueError(f"Loader {name} cannot handle: {att.path}")
        
        return wrapper
    
    def _make_dispatch_wrapper(self, name: str):
        """Create a wrapper that dispatches based on object type."""
        handlers = self._registry[name]
        
        @wraps(handlers[0][1])
        def wrapper(att: Attachment) -> Attachment:
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


def regenerate_stubs():
    """Legacy function - no longer needed."""
    print("📝 Stub generation is no longer needed!")
    print("✨ SmartVerbNamespace now provides autocomplete automatically")


# Helper functions for convenient attachment creation

