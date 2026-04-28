# Contributing to Bitnet Launcher

Thank you for your interest in contributing to the Bitnet Launcher project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to the D-sorganization Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your contribution
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- uv (for dependency management)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/D-sorganization/Bitnet_Launcher.git
cd Bitnet_Launcher

# Create virtual environment and install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check if the issue already exists. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Any relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Any relevant examples or mock-ups
- The motivation for the enhancement

### Contributing Code

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards

3. Add tests for new functionality

4. Run the test suite:
   ```bash
   uv run pytest
   ```

5. Commit your changes with a clear, descriptive commit message:
   ```bash
   git commit -m "feat: add new launcher capability"
   ```

## Pull Request Process

1. Update the README.md or documentation with details of changes if applicable
2. Ensure all tests pass and code coverage is maintained
3. Update release notes if maintainers request them
4. Your pull request will be reviewed by maintainers
5. Address any feedback from reviewers
6. Once approved, a maintainer will merge your pull request

## Coding Standards

### Python Code Style

We use the following tools to enforce code quality:

- **ruff**: Linting and import sorting
- **black**: Code formatting
- **mypy**: Static type checking

All code must pass these checks before being merged. Run them locally with:

```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy src
```

### Design Principles

- **DRY (Don't Repeat Yourself)**: Avoid code duplication
- **Orthogonality**: Keep modules independent
- **Design by Contract**: Use explicit preconditions and postconditions
- **Test-Driven Development**: Write tests before implementing features

## Testing

- All new code must include tests
- Maintain or improve code coverage
- Tests should be clear and descriptive
- Use pytest for unit tests

Run tests with:

```bash
uv run pytest
```

## Documentation

- Update relevant documentation for any changes
- Use clear, concise language
- Include code examples where appropriate
- Follow the SPEC.md template for architectural changes

## Reporting Issues

When reporting issues, please use the GitHub issue tracker and provide:

- Issue type (bug, feature request, question)
- Detailed description
- Steps to reproduce (for bugs)
- Expected and actual behavior
- Environment information

## Questions?

If you have questions, feel free to open an issue with the `question` label or reach out to the maintainers.

---

Thank you for contributing to Bitnet Launcher!
