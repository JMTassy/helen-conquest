import os

def safe_relpath(base_dir: str, user_path: str) -> str:
    """
    Ensures that user_path is within base_dir.
    Raises ValueError if path traversal is detected.
    """
    base_dir = os.path.abspath(base_dir)
    resolved_path = os.path.abspath(os.path.join(base_dir, user_path))
    
    if not resolved_path.startswith(base_dir):
        raise ValueError(f"LNSA_ERROR: Path traversal detected! {user_path} is outside {base_dir}")
        
    return resolved_path
