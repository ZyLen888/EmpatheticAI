import os

def load_prompt_template(style: str, approach: str) -> str:
    """
    Load a prompt template based on therapy style and approach.
    
    Args:
        style: The therapy style ('pct', 'mi', or 'integrated')
        approach: The prompt approach ('zero_shot', 'one_shot', or 'few_shot')
    
    Returns:
        str: The prompt template content
    
    Raises:
        ValueError: If the style or approach is invalid or file not found
    """
    valid_styles = ['pct', 'mi', 'integrated']
    valid_approaches = ['zero_shot', 'one_shot', 'few_shot']
    
    if style not in valid_styles:
        raise ValueError(f"Invalid style. Must be one of: {', '.join(valid_styles)}")
    
    if approach not in valid_approaches:
        raise ValueError(f"Invalid approach. Must be one of: {', '.join(valid_approaches)}")
    
    prompt_path = os.path.join('prompts', style, f'{approach}.txt')
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        raise ValueError(f"Prompt file not found: {prompt_path}")