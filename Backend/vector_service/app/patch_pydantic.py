"""
Patch for pydantic to work around the PydanticDeprecationWarning import error
"""
import pydantic
import warnings

# Add the missing PydanticDeprecationWarning class if it doesn't exist
if not hasattr(pydantic, 'PydanticDeprecationWarning'):
    class PydanticDeprecationWarning(DeprecationWarning):
        pass
    
    pydantic.PydanticDeprecationWarning = PydanticDeprecationWarning
    
    # Monkey patch the __init__ module
    import sys
    if '__init__.cpython-' in str(pydantic.__file__):
        # If using compiled module, need to patch sys.modules
        sys.modules['pydantic'].PydanticDeprecationWarning = PydanticDeprecationWarning 