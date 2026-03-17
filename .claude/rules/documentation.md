# Documentation Rules

## Scope

These rules apply to `README.md`, `docs/**`, `CHANGELOG.md`, and any public-facing documentation files.

## MUST Rules

### 1. Version Numbers Must Match pyproject.toml

All version numbers in documentation MUST match the actual version in `pyproject.toml`.

**Enforced by**: documentation-validator agent, intermediate-reviewer pre-commit check
**Violation**: BLOCK release

### 2. Repository URLs Must Point to Praxis

All GitHub URLs MUST point to `terrene-foundation/praxis`.

**Correct**:

```
https://github.com/terrene-foundation/praxis
https://github.com/terrene-foundation/praxis/issues
```

### 3. No Internal References in Public Docs

Public-facing documentation MUST NOT contain:

- Internal domain names (use `example.com` for examples)
- References to proprietary products, codebases, or commercial entities (see `independence.md`)
- Internal project names or private repo references

**Enforced by**: intermediate-reviewer pre-commit check
**Violation**: BLOCK commit for public-facing files

### 4. Foundation-Only References

Documentation MUST only reference Terrene Foundation open-source products and open standards. See `independence.md` for the full policy.

## MUST NOT Rules

### 1. No Dead Link References

MUST NOT reference paths that don't exist in the repo.

### 2. No Placeholder URLs

MUST NOT use placeholder URLs like `your-org` or `YOUR_USERNAME` in production documentation. Use `terrene-foundation` for org references.

## Documentation Update Triggers

Documentation MUST be reviewed when:

- Package version is bumped
- Repository is restructured
- New module is added
- Public-facing URLs change

## Exceptions

Documentation exceptions require:

1. Explicit human approval
2. Tracked issue for remediation
