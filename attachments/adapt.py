from typing import List, Dict, Any
from .core import Attachment, adapter

# --- ADAPTERS ---

@adapter
def openai_chat(att: Attachment, prompt: str = "") -> List[Dict[str, Any]]:
    """Adapt for OpenAI chat completion API."""
    content = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    
    if att.text:
        content.append({"type": "text", "text": att.text})
    
    for img in att.images:
        if not img.startswith('data:'):  # Only add real base64 images
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img}"}
            })
    
    return [{"role": "user", "content": content}]

@adapter
def openai_response(att: Attachment, prompt: str = "") -> List[Dict[str, Any]]:
    """Adapt for OpenAI chat completion API."""
    content = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    
    if att.text:
        content.append({"type": "text", "text": att.text})
    
    for img in att.images:
        if not img.startswith('data:'):  # Only add real base64 images
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img}"}
            })
    
    return [{"role": "user", "content": content}]


@adapter
def claude(att: Attachment, prompt: str = "") -> List[Dict[str, Any]]:
    """Adapt for Claude API."""
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
        if not img.endswith('_placeholder'):  # Only add real base64 images
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img
                }
            })
    
    return [{"role": "user", "content": content}]

