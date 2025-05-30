from typing import List, Dict, Any, Union
from .core import Attachment, AttachmentCollection, adapter

# --- ADAPTERS ---

def _handle_collection(input_obj: Union[Attachment, AttachmentCollection]) -> Attachment:
    """Convert AttachmentCollection to single Attachment for adapter processing."""
    if isinstance(input_obj, AttachmentCollection):
        return input_obj.to_attachment()
    return input_obj

@adapter
def openai_chat(input_obj: Union[Attachment, AttachmentCollection], prompt: str = "") -> List[Dict[str, Any]]:
    """Adapt for OpenAI chat completion API."""
    att = _handle_collection(input_obj)
    
    content = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    
    if att.text:
        content.append({"type": "text", "text": att.text})
    
    for img in att.images:
        if img and isinstance(img, str) and len(img) > 10:  # Basic validation
            # Check if it's already a data URL
            if img.startswith('data:image/'):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img}
                })
            elif not img.endswith('_placeholder'):
                # It's raw base64, add the data URL prefix
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}"}
                })
    
    return [{"role": "user", "content": content}]

@adapter
def openai_response(input_obj: Union[Attachment, AttachmentCollection], prompt: str = "") -> List[Dict[str, Any]]:
    """Adapt for OpenAI chat completion API."""
    att = _handle_collection(input_obj)
    
    content = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    
    if att.text:
        content.append({"type": "text", "text": att.text})
    
    for img in att.images:
        if img and isinstance(img, str) and len(img) > 10:  # Basic validation
            # Check if it's already a data URL
            if img.startswith('data:image/'):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img}
                })
            elif not img.endswith('_placeholder'):
                # It's raw base64, add the data URL prefix
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}"}
                })
    
    return [{"role": "user", "content": content}]


@adapter
def claude(input_obj: Union[Attachment, AttachmentCollection], prompt: str = "") -> List[Dict[str, Any]]:
    """Adapt for Claude API."""
    att = _handle_collection(input_obj)
    
    content = []
    
    # Check for prompt in commands (from DSL)
    dsl_prompt = att.commands.get('prompt', '')
    
    # Combine prompts: parameter prompt takes precedence, DSL prompt as fallback
    effective_prompt = prompt or dsl_prompt
    
    if effective_prompt and att.text:
        content.append({"type": "text", "text": f"{effective_prompt}\n\n{att.text}"})
    elif effective_prompt:
        content.append({"type": "text", "text": effective_prompt})
    elif att.text:
        content.append({"type": "text", "text": att.text})
    
    for img in att.images:
        if img and isinstance(img, str) and len(img) > 10:  # Basic validation
            # Extract base64 data for Claude
            base64_data = img
            if img.startswith('data:image/'):
                # Extract just the base64 part after the comma
                if ',' in img:
                    base64_data = img.split(',', 1)[1]
                else:
                    continue  # Skip malformed data URLs
            elif img.endswith('_placeholder'):
                continue  # Skip placeholder images
            
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_data
                }
            })
    
    return [{"role": "user", "content": content}]

@adapter
def openai(input_obj: Union[Attachment, AttachmentCollection], prompt: str = "") -> List[Dict[str, Any]]:
    """Alias for openai_chat - backwards compatibility with simple API."""
    return openai_chat(input_obj, prompt)

@adapter
def dspy(input_obj: Union[Attachment, AttachmentCollection]) -> 'DSPyAttachment':
    """Adapt Attachment for DSPy signatures as a BaseType-compatible object."""
    att = _handle_collection(input_obj)
    
    try:
        # Import DSPy Image class to understand the pattern
        from dspy.adapters.types.image import Image
        import pydantic
        
        class DSPyAttachment(pydantic.BaseModel):
            """DSPy-compatible wrapper for Attachment objects following Image pattern."""
            
            # Store the attachment data
            text: str = ""
            images: List[str] = []
            audio: List[str] = []
            path: str = ""
            metadata: Dict[str, Any] = {}
            
            model_config = {
                "frozen": True,
                "str_strip_whitespace": True,
                "validate_assignment": True,
                "extra": "forbid",
            }
            
            @pydantic.model_serializer()
            def serialize_model(self):
                """Serialize for DSPy compatibility - following Image pattern."""
                # Create a comprehensive representation that includes both text and images
                content_parts = []
                
                if self.text:
                    content_parts.append(f"<DSPY_TEXT_START>{self.text}<DSPY_TEXT_END>")
                
                if self.images:
                    # Process images - ensure they're properly formatted
                    valid_images = []
                    for img in self.images:
                        if img and isinstance(img, str):
                            # Check if it's already a data URL
                            if img.startswith('data:image/'):
                                valid_images.append(img)
                            elif img and not img.endswith('_placeholder'):
                                # It's raw base64, add the data URL prefix
                                valid_images.append(f"data:image/png;base64,{img}")
                    
                    if valid_images:
                        image_tags = ""
                        for img in valid_images:
                            image_tags += f"<DSPY_IMAGE_START>{img}<DSPY_IMAGE_END>"
                        content_parts.append(image_tags)
                
                if content_parts:
                    return "".join(content_parts)
                else:
                    return f"<DSPY_ATTACHMENT_START>Attachment: {self.path}<DSPY_ATTACHMENT_END>"
            
            def __str__(self):
                return self.serialize_model()
            
            def __repr__(self):
                if self.text:
                    text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
                    return f"DSPyAttachment(text='{text_preview}', images={len(self.images)})"
                elif self.images:
                    return f"DSPyAttachment(images={len(self.images)}, path='{self.path}')"
                else:
                    return f"DSPyAttachment(path='{self.path}')"
        
        # Clean up the images list - remove any invalid entries
        clean_images = []
        for img in att.images:
            if img and isinstance(img, str) and len(img) > 10:  # Basic validation
                # If it's already a data URL, keep it as is
                if img.startswith('data:image/'):
                    clean_images.append(img)
                # If it's raw base64, we'll handle it in the serializer
                elif not img.endswith('_placeholder'):
                    clean_images.append(img)
        
        # Create and return the DSPy-compatible object
        return DSPyAttachment(
            text=att.text,
            images=clean_images,
            audio=att.audio,
            path=att.path,
            metadata=att.metadata
        )
        
    except ImportError:
        # Fallback if DSPy is not available - return a simple dict
        return {
            "text": att.text,
            "images": att.images,
            "audio": att.audio,
            "path": att.path,
            "metadata": att.metadata,
            "_type": "attachment"
        }

