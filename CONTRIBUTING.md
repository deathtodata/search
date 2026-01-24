# Contributing to Death2Data

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to Death2Data. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Pull Request Process](#pull-request-process)
5. [Style Guidelines](#style-guidelines)
6. [Security](#security)

---

## Code of Conduct

**Be respectful, constructive, and collaborative.**

We're building privacy-preserving technology. Let's keep the community welcoming and focused on the mission.

---

## How Can I Contribute?

### Reporting Bugs

**Before creating a bug report:**
- Check existing issues to avoid duplicates
- Verify the bug exists in the latest version

**When creating a bug report, include:**
- OS and Python version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs

**Template:**
```markdown
## Bug Report

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.11.2
- Death2Data: v1.0.0

**Steps to reproduce:**
1. Start server with `python3 gateway.py`
2. Visit `http://localhost:3000/?token=invalid`
3. See error

**Expected:** Proper error message
**Actual:** Server crashes

**Logs:**
```
[paste logs here]
```
```

### Suggesting Enhancements

**Good enhancement suggestions include:**
- Clear use case
- Expected behavior
- Why it improves privacy/usability
- Example implementation (optional)

**Example:**
```markdown
## Feature Request: Rate Limiting

**Use case:** Prevent token abuse

**Proposal:** Limit searches to 100/hour per token

**Implementation idea:**
- Add `rate_limits` table
- Check count before each search
- Return 429 if exceeded

**Privacy impact:** Requires logging search counts (acceptable for abuse prevention)
```

### Your First Code Contribution

**Good first issues:**
- Documentation improvements
- UI/UX enhancements
- Test coverage
- Error message improvements

Look for issues tagged `good-first-issue`.

---

## Development Setup

### Prerequisites

- Python 3.7+
- Docker (for SearXNG)
- Git

### Setup

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/search.git
cd search

# 3. Add upstream remote
git remote add upstream https://github.com/deathtodata/search.git

# 4. Create a branch
git checkout -b feature/your-feature-name

# 5. Start development environment
docker run -d -p 8080:8080 searxng/searxng
python3 gateway.py

# 6. Make changes, test locally

# 7. Commit and push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature-name

# 8. Open pull request on GitHub
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass (if applicable)
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] No unnecessary files committed

### PR Template

```markdown
## Description
[What does this PR do?]

## Motivation
[Why is this change needed?]

## Changes
- [ ] Feature 1
- [ ] Feature 2

## Testing
[How did you test this?]

## Privacy Impact
[Does this change data collection? How?]

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass
```

### Review Process

1. Maintainers review within 48 hours
2. Address feedback
3. Once approved, maintainers merge
4. PR gets included in next release

---

## Style Guidelines

### Python

**Follow PEP 8 with these specifics:**

```python
# Good: Clear, simple, auditable
def verify_token(token: str) -> bool:
    """Check if token is valid and not expired."""
    if not token or not token.startswith("d2d_"):
        return False

    token_hash = hash_token(token)
    # ... rest of function

# Bad: Clever, hard to audit
def verify_token(t):
    return (h:=hash_token(t)) in db if t[:4]=="d2d_" else False
```

**Key principles:**
- **Clarity over cleverness** - Code must be auditable
- **Minimal dependencies** - Stdlib only
- **Explicit over implicit** - No magic
- **Simple > complex** - Easy to verify

### Documentation

**Good docs are:**
- Concise but complete
- Example-driven
- Verifiable (commands that work)

**Example:**
```markdown
## Token Generation

Generate a new access token:

```bash
python3 gateway.py --generate-token
```

Output:
```
Token: d2d_abc123...
Hash: a1b2c3...
Expires: 2026-02-21
```

Save the token - it's shown only once.
```

### Commit Messages

**Format:**
```
type: short description

Longer explanation if needed.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat: add rate limiting per token

Limits searches to 100/hour to prevent abuse.
Adds rate_limits table to track usage.

Fixes #45

---

fix: handle missing user-agent header

Some clients don't send user-agent, causing crash.
Now defaults to "Unknown" if missing.

Fixes #67
```

---

## Security

### Reporting Security Issues

**DO NOT open public issues for security vulnerabilities.**

Email: security@death2data.com

Include:
- Description of vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if you have one)

We'll respond within 24 hours.

### Security Guidelines

When contributing, ensure:
- No query logging (ever)
- Minimal data collection
- Secure defaults
- No external dependencies without discussion
- Token hashing (never plaintext storage)

**Privacy-first mindset:**
- "Do we need to store this?" → Usually no
- "Can this be client-side?" → Prefer yes
- "Is this auditable?" → Must be yes

---

## Areas We Need Help

### High Priority

- **Security audits** - Review code for vulnerabilities
- **Performance testing** - How does it scale?
- **Documentation** - Improve guides, add examples
- **Accessibility** - Make UI more accessible

### Medium Priority

- **Internationalization** - Multi-language support
- **UI improvements** - Better search interface
- **Mobile responsiveness** - Better mobile UX
- **Error handling** - More graceful failures

### Nice to Have

- **Dark mode** - UI theme
- **Search filters** - Date, type, etc.
- **Keyboard shortcuts** - Power user features
- **Export tokens** - Bulk token management

---

## Testing

### Manual Testing

```bash
# 1. Start server
python3 gateway.py

# 2. Generate token
python3 gateway.py --generate-token

# 3. Test search
open "http://localhost:3000/?token=YOUR_TOKEN&q=test"

# 4. Verify no query logging
sqlite3 data/d2d.db "SELECT * FROM logins;"
# Should show login, NOT query

# 5. Check error handling
open "http://localhost:3000/?token=invalid"
# Should show error page, not crash
```

### Automated Tests (Future)

We're working on test coverage. Help welcome!

---

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md
- Release notes
- GitHub contributors page

Significant contributions may get:
- Free hosted instance access
- Listed as project contributor
- Thank you in documentation

---

## Questions?

- Open a discussion: https://github.com/deathtodata/search/discussions
- Email: hello@death2data.com
- Join chat: [Coming soon]

---

## Thank You!

Your contributions make privacy tools accessible to everyone.

**Privacy is a human right. Let's build it together.** 🔒
