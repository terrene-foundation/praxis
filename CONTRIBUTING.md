# Contributing to Praxis

Thank you for your interest in contributing to the Terrene Foundation's CO Platform.

## Getting Started

```bash
git clone https://github.com/terrene-foundation/praxis.git
cd praxis
pip install -e ".[dev]"
cp .env.example .env
```

## Development Workflow

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Make changes
3. Run tests: `pytest`
4. Run linting: `ruff check src/ && black --check src/`
5. Commit with conventional commits: `feat(scope): description`
6. Open a pull request

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(session): add session persistence`
- `fix(trust): resolve constraint enforcement race condition`
- `docs(readme): update architecture diagram`
- `test(deliberation): add capture integration tests`

## Testing

We use a 3-tier testing strategy:

- **Tier 1 (Unit)**: Fast, isolated, mocks allowed
- **Tier 2 (Integration)**: Real infrastructure, no mocks
- **Tier 3 (E2E)**: Full system validation

## Code Standards

- Python 3.11+
- Black formatting (line length 100)
- Ruff linting
- Type hints throughout
- Apache 2.0 license headers on all source files

## Standards Alignment

All contributions must align with the Terrene Foundation's open standards:

- **CO** (Cognitive Orchestration) — The methodology Praxis implements
- **EATP** (Enterprise Agent Trust Protocol) — Trust layer
- **CARE** (Collaborative Autonomous Reflective Enterprise) — Governance philosophy

## License

By contributing, you agree that your contributions will be licensed under Apache 2.0.
