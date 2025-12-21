# Contributing to HoloViz MCP

Thank you for your interest in contributing to HoloViz MCP! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Git**: For version control
- **Python 3.11+**: Required for running the project
- **Pixi**: Package and environment manager ([installation guide](https://pixi.sh))
- **UV**: Python package installer ([installation guide](https://docs.astral.sh/uv/))

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

```bash
git clone https://github.com/YOUR_USERNAME/holoviz-mcp.git
cd holoviz-mcp
```

3. **Add the upstream remote**:

```bash
git remote add upstream https://github.com/MarcSkovMadsen/holoviz-mcp.git
```

## Development Setup

### Install Dependencies

Install all development dependencies using Pixi:

```bash
# Install pre-commit hooks
pixi run pre-commit-install

# Install the package in development mode
pixi run postinstall

# Verify installation
pixi run test
```

### Create Development Environment

Pixi manages multiple environments defined in `pixi.toml`:

- **default**: Main development environment
- **docs**: Documentation building
- **test**: Testing environment

Activate the default environment:

```bash
pixi shell
```

## How to Contribute

### Ways to Contribute

There are many ways to contribute to HoloViz MCP:

- **Report bugs**: Open an issue describing the bug
- **Suggest features**: Propose new features or enhancements
- **Fix bugs**: Submit pull requests for open issues
- **Add features**: Implement new functionality
- **Improve documentation**: Enhance or clarify documentation
- **Write tests**: Increase test coverage
- **Review pull requests**: Help review and improve contributions

### Finding Issues

Good places to start:

- Issues labeled `good first issue`: Great for newcomers
- Issues labeled `help wanted`: Community contributions welcome
- Issues labeled `documentation`: Documentation improvements

## Development Workflow

### Creating a Feature Branch

Always create a new branch for your work:

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create a feature branch
git checkout -b feature/your-feature-name
```

### Branch Naming Convention

Use descriptive branch names:

- `feature/add-new-tool`: New features
- `fix/bug-description`: Bug fixes
- `docs/update-readme`: Documentation updates
- `refactor/improve-code`: Code refactoring
- `test/add-coverage`: Test additions

### Making Changes

1. **Make your changes** in your feature branch
2. **Follow code style**: Adhere to project conventions
3. **Write tests**: Add tests for new functionality
4. **Update documentation**: Document new features or changes
5. **Run tests locally**: Ensure all tests pass

```bash
# Run all tests
pixi run test

# Run specific test file
pixi run pytest tests/test_specific.py

# Run with coverage
pixi run test-coverage
```

### Commit Guidelines

Write clear, descriptive commit messages:

```bash
# Good commit messages
git commit -m "feat: Add new search tool for documentation"
git commit -m "fix: Resolve panel component parameter issue"
git commit -m "docs: Update Docker installation guide"
git commit -m "test: Add tests for hvPlot integration"
```

#### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Code Quality

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install hooks
pixi run pre-commit-install

# Run manually
pixi run pre-commit
```

Hooks include:
- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Linting
- **mypy**: Type checking
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline

### Code Style

- **PEP 8**: Follow Python style guidelines
- **Type hints**: Use type annotations where appropriate
- **Docstrings**: Write clear docstrings for public APIs
- **Comments**: Add comments for complex logic

Example:

```python
from typing import List, Optional

def search_components(
    query: str,
    limit: Optional[int] = 10
) -> List[dict]:
    """Search for Panel components matching the query.

    Parameters
    ----------
    query : str
        Search query string
    limit : Optional[int], default 10
        Maximum number of results to return

    Returns
    -------
    List[dict]
        List of matching components with metadata
    """
    # Implementation
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pixi run test

# Run specific test file
pixi run pytest tests/test_panel_tools.py

# Run tests with coverage
pixi run test-coverage

# Run tests with verbose output
pixi run pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names
- Test both success and failure cases
- Use fixtures for common setup
- Mock external dependencies

Example:

```python
import pytest
from holoviz_mcp.tools import search_components

def test_search_components_basic():
    """Test basic component search functionality."""
    results = search_components("Button")
    assert len(results) > 0
    assert any("Button" in r["name"] for r in results)

def test_search_components_with_limit():
    """Test search with result limit."""
    results = search_components("Input", limit=5)
    assert len(results) <= 5

@pytest.mark.parametrize("query", ["", None])
def test_search_components_invalid_query(query):
    """Test search with invalid queries."""
    with pytest.raises(ValueError):
        search_components(query)
```

### Test Coverage

Aim for high test coverage:

```bash
# Generate coverage report
pixi run test-coverage

# View HTML coverage report
open htmlcov/index.html
```

## Documentation

### Building Documentation

Build documentation locally:

```bash
# Build documentation
pixi run -e docs build

# Serve documentation locally
pixi run -e docs serve
```

### Documentation Style

- **Clear and concise**: Write for clarity
- **Examples**: Include code examples
- **Cross-references**: Link to related documentation
- **Screenshots**: Add images where helpful
- **Keep updated**: Update docs with code changes

### Docstring Format

Use NumPy-style docstrings:

```python
def my_function(param1: str, param2: int = 0) -> bool:
    """Short description of function.

    Longer description with more details about what
    the function does and how to use it.

    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : int, default 0
        Description of param2

    Returns
    -------
    bool
        Description of return value

    Examples
    --------
    >>> my_function("test", 5)
    True
    """
    pass
```

## Submitting Changes

### Pull Request Process

1. **Update your branch** with the latest upstream changes:

```bash
git fetch upstream
git rebase upstream/main
```

2. **Push your changes** to your fork:

```bash
git push origin feature/your-feature-name
```

3. **Create a Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe your changes in detail
   - Include screenshots for UI changes
   - List any breaking changes

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Related Issues
Closes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] All tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated documentation

## Screenshots (if applicable)
Add screenshots here

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing
```

### Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Keep your PR focused and atomic
- Be patient and respectful
- Once approved, your PR will be merged

### After Merging

1. **Delete your branch** (optional):

```bash
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

2. **Update your main branch**:

```bash
git checkout main
git pull upstream main
git push origin main
```

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Discord**: HoloViz community chat ([join here](https://discord.gg/AXRHnJU6sP))
- **Discourse**: HoloViz forum ([visit here](https://discourse.holoviz.org/))

### Getting Help

If you need help:

1. **Search existing issues** and discussions
2. **Read the documentation**
3. **Ask in Discord** or Discourse
4. **Open a GitHub discussion** for general questions
5. **Open an issue** for bugs or specific problems

### Reporting Bugs

When reporting bugs, include:

- **Description**: Clear description of the bug
- **Steps to reproduce**: Minimal steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: OS, Python version, package versions
- **Logs**: Relevant error messages or logs
- **Screenshots**: If applicable

### Suggesting Features

When suggesting features:

- **Use case**: Explain why this feature is needed
- **Description**: Describe the feature in detail
- **Examples**: Provide usage examples
- **Alternatives**: Mention any alternatives considered

## Development Tips

### Running the MCP Server Locally

Test your changes with the development server:

```bash
# Standard I/O transport
pixi run holoviz-mcp

# HTTP transport (useful for debugging)
HOLOVIZ_MCP_TRANSPORT=http pixi run holoviz-mcp
```

### Debugging

Use Python debugging tools:

```bash
# With pdb
python -m pdb -m holoviz_mcp

# With ipdb (if installed)
ipdb holoviz_mcp
```

### Docker Development

Test Docker changes:

```bash
# Build locally
docker build -t holoviz-mcp:dev .

# Run local build
docker run -it --rm holoviz-mcp:dev
```

### Updating Template

This project uses [copier-template-panel-extension](https://github.com/panel-extensions/copier-template-panel-extension).

Update to latest template:

```bash
pixi exec --spec copier --spec ruamel.yaml -- copier update --defaults --trust
```

## Recognition

Contributors are recognized in:

- GitHub contributors list
- Release notes for significant contributions
- Project README (for major contributions)

Thank you for contributing to HoloViz MCP! Your efforts help make this project better for everyone.

## Questions?

If you have questions about contributing, feel free to:

- Open a GitHub Discussion
- Ask in the HoloViz Discord
- Reach out to the maintainers

We're here to help and appreciate your contributions!
