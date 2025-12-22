# Contributing to EZSell

Thank you for considering contributing to EZSell! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/mahmedddd/ezsell/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Your environment (OS, Python version, Node version)

### Suggesting Features

1. Check [Issues](https://github.com/mahmedddd/ezsell/issues) for existing suggestions
2. Create a new issue with:
   - Clear description of the feature
   - Why it would be useful
   - Possible implementation approach

### Pull Requests

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/ezsell.git
   cd ezsell
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make Your Changes**
   - Follow the code style guidelines
   - Add tests if applicable
   - Update documentation

4. **Test Your Changes**
   ```bash
   # Backend tests
   cd ezsell/ezsell/backend
   pytest
   
   # Frontend tests
   cd ezsell/ezsell/frontend
   npm test
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting)
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template
   - Submit!

## 📝 Code Style Guidelines

### Python (Backend)

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Write docstrings for functions and classes
- Maximum line length: 100 characters

```python
def calculate_price(
    category: str,
    base_price: float,
    adjustments: Dict[str, Any]
) -> Tuple[float, List[str]]:
    """
    Calculate final price with adjustments.
    
    Args:
        category: Product category
        base_price: Starting price
        adjustments: Dictionary of price adjustments
        
    Returns:
        Tuple of (final_price, list_of_adjustments)
    """
    # Implementation
    pass
```

### TypeScript/JavaScript (Frontend)

- Use TypeScript for type safety
- Follow React best practices
- Use functional components with hooks
- Maximum line length: 100 characters

```typescript
interface ListingProps {
  id: number;
  title: string;
  price: number;
}

export const ListingCard: React.FC<ListingProps> = ({ id, title, price }) => {
  // Implementation
  return <div>...</div>;
};
```

### File Naming

- Backend: `snake_case.py`
- Frontend: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Use descriptive names

## 🧪 Testing

### Backend Tests

```bash
cd ezsell/ezsell/backend
pytest tests/
pytest --cov=. --cov-report=html  # With coverage
```

### Frontend Tests

```bash
cd ezsell/ezsell/frontend
npm test
npm run test:coverage  # With coverage
```

## 📚 Documentation

- Update README.md if adding features
- Add comments for complex logic
- Update API documentation
- Add examples for new features

## 🔄 Development Workflow

1. Pull latest changes from main
   ```bash
   git checkout main
   git pull origin main
   ```

2. Create feature branch
   ```bash
   git checkout -b feature/my-feature
   ```

3. Make changes and test locally

4. Commit changes with clear messages

5. Push to your fork

6. Create Pull Request

7. Address review comments

8. Get approved and merged!

## ✅ Pull Request Checklist

Before submitting your PR, ensure:

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No merge conflicts with main
- [ ] PR description is complete

## 🚀 Development Setup

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions.

Quick setup:
```bash
# Backend
cd ezsell/ezsell/backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd ezsell/ezsell/frontend
npm install
```

## 📋 Project Structure

```
ezsell/
├── ezsell/ezsell/
│   ├── backend/           # FastAPI backend
│   │   ├── routers/       # API endpoints
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── core/          # Core utilities
│   │   └── ml_pipeline/   # ML training
│   │
│   └── frontend/          # React frontend
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   └── lib/
│       └── public/
```

## 🐛 Debugging Tips

### Backend
```bash
# Run with debug logging
uvicorn main:app --reload --log-level debug

# Python debugger
import pdb; pdb.set_trace()
```

### Frontend
```bash
# Run with source maps
npm run dev

# Browser DevTools
# Press F12 and check Console/Network tabs
```

## 💬 Communication

- **GitHub Issues**: Bug reports, feature requests
- **Pull Requests**: Code contributions
- **Discussions**: General questions and ideas

## 🎯 Areas to Contribute

- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🧪 Test coverage
- 🎨 UI/UX improvements
- ♿ Accessibility improvements
- 🌍 Internationalization
- ⚡ Performance optimizations

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🙏 Thank You!

Your contributions make EZSell better for everyone. We appreciate your time and effort!

---

**Questions?** Open an issue or reach out to the maintainers.
