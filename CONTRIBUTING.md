# Contributing to summarize-mcp

First off, thank you for considering contributing to summarize-mcp! It's people like you that make this tool better for everyone.

## Code of Conduct

By participating in this project, you agree to abide by our code of conduct: be respectful, inclusive, and constructive in all interactions.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Node.js version, etc.)
- Any relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- A clear and descriptive title
- The motivation for the enhancement
- Detailed explanation of the proposed functionality
- Any examples of how it would work

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code, add tests that cover your changes
3. Ensure the test suite passes (`npm test`)
4. Make sure your code follows the existing style
5. Issue the pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/summarize-mcp.git
cd summarize-mcp

# Install dependencies
npm install

# Run in development mode
npm run dev

# Build the project
npm run build

# Run type checking
npm run typecheck

# Run tests
npm test
```

## Style Guidelines

### TypeScript Style

- Use TypeScript strict mode
- Define types/interfaces for all data structures
- Avoid `any` types
- Use meaningful variable and function names
- Add JSDoc comments for public APIs

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add support for ElevenLabs TTS provider

- Implement ElevenLabs API client
- Add voice mapping for ElevenLabs voices
- Update documentation with new provider info

Fixes #123
```

### Code Review Process

All submissions require review. We use GitHub pull requests for this purpose. Consult [GitHub Help](https://help.github.com/articles/about-pull-requests/) for more information on using pull requests.

## Testing

- Write tests for any new functionality
- Ensure all tests pass before submitting PR
- Include both positive and negative test cases
- Test edge cases and error conditions

## Documentation

- Update the README.md if you change functionality
- Add JSDoc comments to new functions
- Update the changelog for notable changes
- Include examples for new features

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉