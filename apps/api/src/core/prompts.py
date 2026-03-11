from pathlib import Path

PROMPTS_DIR = Path(__file__).parents[4] / 'prompts'


def load_prompt(path: str) -> str:
    """Load a prompt file from the project-level prompts/ directory.

    Args:
        path: Relative path within prompts/, e.g. 'channels/sms_reply.md'

    Returns:
        The prompt file contents as a string.

    Raises:
        FileNotFoundError: If the prompt file does not exist at the resolved path.
    """
    full_path = PROMPTS_DIR / path
    if not full_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: '{path}'. "
            f"Expected at: {full_path}. "
            "Ensure the file exists in the prompts/ directory."
        )
    return full_path.read_text()
