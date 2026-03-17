# Platform Principles

## Praxis Must Be Genuinely Open

These principles are non-negotiable. They exist to ensure Praxis serves the community, not a commercial agenda.

### 1. No Open-Washing

Every feature Praxis ships must be fully implemented, properly tested, and genuinely useful. No artificial limitations. No features that exist only in name. No "contact us for the real version."

**Test**: If a university adopts Praxis for their entire research faculty, can they do everything they need without paying anyone? The answer must be yes.

### 2. No Artificial Ceilings

Praxis does not limit:
- Number of users (within the hosting capacity)
- Number of sessions
- Number of domains
- Storage of trust chains
- Verification bundle generation
- API rate limits (beyond what prevents abuse)

If a capability exists, it works fully. There is no "upgrade for more."

### 3. Full Feature Depth

| Capability | Requirement |
|---|---|
| Session management | Full lifecycle with persistence |
| Constraint enforcement | All 5 dimensions, runtime enforcement |
| Trust chains | Full EATP with Ed25519, hash chains, verification |
| Verification gradient | All 4 levels with real consequences |
| Domain applications | Full domain engine with configuration API |
| Verification bundles | Self-contained, independently verifiable |
| Web dashboard | All persona views (practitioner, supervisor, auditor) |
| API | Full MCP + REST + CLI |

### 4. Community-Driven Development

- Public roadmap on GitHub
- Issue-driven development
- Community pull requests welcome
- RFC process for significant changes
- Regular releases (not just when convenient)

### 5. Standards Fidelity

Praxis is the reference implementation of CO, EATP, and CARE. If Praxis deviates from the specification, the specification is wrong — file an issue against the spec, don't deviate silently.

### 6. No Vendor Lock-In

- Data stored in open formats (JSON, SQLite, PostgreSQL)
- Trust chains use EATP standard format (not Praxis-proprietary)
- Verification bundles are self-contained (no server callback)
- Domain configurations are portable files (YAML)
- API follows MCP standard (not Praxis-proprietary extensions)

Any organization should be able to:
1. Export all their data from Praxis
2. Verify all trust chains without Praxis installed
3. Build their own client that connects to Praxis API
4. Build their own server that accepts Praxis client connections

### 7. Privacy by Default

- All data stays on the user's infrastructure (no telemetry, no phone-home)
- No user tracking
- No usage analytics sent externally
- Crash reports are opt-in only
- Trust chains contain only what the user explicitly records

---

## Quality Standards

### Code

- Python 3.11+ with full type annotations
- 100% of public API has docstrings
- Test coverage target: 90%+
- No stubs, TODOs, or placeholder implementations in release builds
- Security review before every release

### Documentation

- Every feature has usage documentation
- Every API endpoint has request/response examples
- Architecture documented with diagrams
- Domain application creation guide with worked examples
- Contribution guide that actually helps contributors

### Release

- Semantic versioning (MAJOR.MINOR.PATCH)
- Changelog for every release
- Migration guide for breaking changes
- Minimum 2-week deprecation notice for public API changes
- LTS releases for production users (12-month support minimum)

---

## Sustainability

Praxis is funded by the Terrene Foundation. The Foundation's sustainability comes from:

1. **Standards licensing** — CARE, EATP, CO specifications under CC BY 4.0 enable commercial products
2. **SDK licensing** — Kailash SDKs under Apache 2.0 enable commercial use
3. **Ecosystem growth** — More Praxis users → more CO adoption → more demand for Foundation standards and SDKs
4. **Grants and partnerships** — Academic and institutional partnerships for CO adoption

Praxis's job is to be the best possible CO platform, which grows the ecosystem that sustains the Foundation. This is not charity — it is strategic. A thriving open-source ecosystem creates demand for the standards and SDKs that the Foundation publishes.
