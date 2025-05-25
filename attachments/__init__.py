from .core import Attachment, AttachmentCollection, attach, A, Pipeline, SmartVerbNamespace, _loaders, _modifiers, _presenters, _adapters, _refiners, loader, modifier, presenter, adapter, refiner
from .simple import Attachments, process


# Import the individual modules to ensure functions are registered
from . import load as _load_module
from . import modify as _modify_module
from . import present as _present_module
from . import adapt as _adapt_module
from . import refine as _refine_module
from . import split as _split_module
from . import matchers as _matchers_module

# Import processor system and register processors
from .pipelines import processor, processors, find_primary_processor, find_named_processor, list_available_processors

# Import processors to register them automatically
from .pipelines import pdf_processor as _pdf_processor_module
from .pipelines import image_processor as _image_processor_module
from .pipelines import pptx_processor as _pptx_processor_module
#from .pipelines import example_processors as _example_processors_module

# Import data module for sample data access
from . import data

# Create the namespace instances after functions are registered
load = SmartVerbNamespace(_loaders)
modify = SmartVerbNamespace(_modifiers)
present = SmartVerbNamespace(_presenters)
adapt = SmartVerbNamespace(_adapters)
refine = SmartVerbNamespace(_refiners)
split = SmartVerbNamespace(_modifiers)  # Split functions are also modifiers

__all__ = ["Attachment", "AttachmentCollection", "attach", "A", "Pipeline",
           "load", "modify", "present", "adapt", "refine", "split", "data",
           "loader", "modifier", "presenter", "adapter", "refiner",
           "processor", "processors", "Attachments", "process"]
