from .core import Attachment, attach, A, Pipeline, SmartVerbNamespace, _loaders, _modifiers, _presenters, _adapters, _refiners, loader, modifier, presenter, adapter, refiner


# Import the individual modules to ensure functions are registered
from . import load as _load_module
from . import modify as _modify_module
from . import present as _present_module
from . import adapt as _adapt_module
from . import refine as _refine_module
from . import matchers as _matchers_module

# Import data module for sample data access
from . import data

# Create the namespace instances after functions are registered
load = SmartVerbNamespace(_loaders)
modify = SmartVerbNamespace(_modifiers)
present = SmartVerbNamespace(_presenters)
adapt = SmartVerbNamespace(_adapters)
refine = SmartVerbNamespace(_refiners)

__all__ = ["Attachment", "attach", "A", "Pipeline",
           "load", "modify", "present", "adapt", "refine", "data",
           "loader", "modifier", "presenter", "adapter", "refiner"]
