# Contributing to MusicBarber

Thank you for your interest in contributing to MusicBarber! We welcome contributions from everyone. Here are some guidelines to help you get started.

## How to Contribute

### 1. Fork the Repository
- Click the "Fork" button on the top right of the repository page
- Clone your fork locally: `git clone https://github.com/your-username/musicbarber-collaborative.git`
- Add the upstream remote: `git remote add upstream https://github.com/JamesOliasAI/musicbarber-collaborative.git`

### 2. Create a Feature Branch
- Create a new branch for your feature: `git checkout -b feature/your-feature-name`
- Use descriptive branch names that explain what you're working on

### 3. Make Your Changes
- Write clear, concise commit messages
- Follow the existing code style and conventions
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
- Run the existing tests: `npm test`
- Test your changes manually
- Ensure the application still works correctly

### 5. Submit a Pull Request
- Push your branch to your fork: `git push origin feature/your-feature-name`
- Go to the original repository and click "New Pull Request"
- Choose your branch from the "compare" dropdown
- Fill out the pull request template
- Click "Create Pull Request"

## Development Workflow

### Branch Naming Convention
- `feature/feature-name` - for new features
- `bugfix/bug-description` - for bug fixes
- `docs/description` - for documentation updates
- `refactor/description` - for code refactoring

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat` - new feature
- `fix` - bug fix
- `docs` - documentation
- `style` - code style changes
- `refactor` - code refactoring
- `test` - adding tests
- `chore` - maintenance tasks

### Code Style
- Use 2 spaces for indentation
- Follow JavaScript ES6+ standards
- Use meaningful variable and function names
- Add comments for complex logic

## Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/JamesOliasAI/musicbarber-collaborative.git
   cd musicbarber-collaborative
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Run tests**
   ```bash
   npm test
   ```

## Pull Request Process

1. **Create a pull request** with a clear title and description
2. **Reference any related issues** in the description
3. **Wait for review** from maintainers
4. **Address any feedback** by making additional commits
5. **Pull request will be merged** once approved

## Code Review Process

- All pull requests require at least 1 approval from a maintainer
- Automated tests must pass
- Code must follow project standards
- Documentation must be updated for new features

## Reporting Issues

- Use the GitHub issue tracker for bug reports and feature requests
- Search existing issues before creating a new one
- Provide clear steps to reproduce bugs
- Include relevant error messages and screenshots

## Getting Help

- Check the existing documentation
- Search closed issues for similar problems
- Ask questions in the discussions section
- Join our community chat (if available)

## License

By contributing to MusicBarber, you agree that your contributions will be licensed under the same license as the original project.

---

Thank you for contributing to MusicBarber! 🎵