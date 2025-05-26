import os

def load_prompt_template(style: str, context_type: str) -> str:
    """
    Load a prompt template based on therapy style and context type.
    
    Args:
        style: The therapy style ('cbt' for CBT-informed approach)
        context_type: The context approach ('with_context' or 'without_context')
    
    Returns:
        str: The prompt template content
    
    Raises:
        ValueError: If the style or context_type is invalid or file not found
    """
    valid_styles = ['cbt']
    valid_context_types = ['with_context', 'without_context']
    
    if style not in valid_styles:
        raise ValueError(f"Invalid style. Must be one of: {', '.join(valid_styles)}")
    
    if context_type not in valid_context_types:
        raise ValueError(f"Invalid context type. Must be one of: {', '.join(valid_context_types)}")
    
    prompt_path = os.path.join('prompts', style, f'{context_type}.txt')
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        raise ValueError(f"Prompt file not found: {prompt_path}")