"""Provides best practices, examples and other documentation for using the HoloViz ecosystem effieciently with LLMs."""

from pathlib import Path

DIR = Path(__file__).parent


def get_best_practices(package) -> str:
    """Get best practices for using a package with LLMs.

    args:
        package (str): The name of the package to get best practices for.
        level (Literal["intermediate"]): The level of best practices to return.
        place (Literal["script"]): The place where the best practices will be used, e.g., "script", "notebook", etc.

    Returns
    -------
        str: A string containing the best practices for the package in Markdown format.
    """
    # read the
    best_practices_file = DIR / "best_practices" / f"{package}.md"
    if not best_practices_file.exists():
        raise FileNotFoundError(f"Best practices file for package '{package}' not found.")

    return best_practices_file.read_text(encoding="utf-8")
