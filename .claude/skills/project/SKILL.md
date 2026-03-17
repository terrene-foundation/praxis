# Praxis Project Skills

Skills specific to the Praxis CO platform implementation.

## Available Skills

| Skill             | File                                                       | Description                                                                                |
| ----------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Architecture      | [praxis-architecture.md](praxis-architecture.md)           | Module dependency graph, data flow, key design decisions                                   |
| Trust Chain       | [praxis-trust-chain.md](praxis-trust-chain.md)             | Ed25519 signing, JCS hashing, chain building, verification, DB persistence                 |
| Constraint System | [praxis-constraint-system.md](praxis-constraint-system.md) | 5-dimension evaluation, gradient thresholds, held actions, middleware                      |
| Domain Engine     | [praxis-domain-engine.md](praxis-domain-engine.md)         | YAML config schema, 6 domains, knowledge, anti-amnesia, rules                              |
| CLI Patterns      | [praxis-cli-patterns.md](praxis-cli-patterns.md)           | Click commands, workspace state, learning/domain/MCP commands                              |
| API Patterns      | [praxis-api-patterns.md](praxis-api-patterns.md)           | 29 handlers, RESTful routes, MCP tools, rate limiting, middleware                          |
| Learning Pipeline | [praxis-learning-pipeline.md](praxis-learning-pipeline.md) | CO Layer 5: observe-analyze-propose-formalize, 5 pattern detectors                         |
| Persistence       | [praxis-persistence.md](praxis-persistence.md)             | 9 DataFlow models, db_ops API, column validation, JSON serialization                       |
| MCP Proxy         | [praxis-mcp-proxy.md](praxis-mcp-proxy.md)                 | Tool interception, constraint enforcement, dimension mapping                               |
| Security          | [praxis-security.md](praxis-security.md)                   | 5 defense layers: SQL prevention, rate limiting, timing-safe, sanitization, key protection |

## When to Use

- **Modifying trust chain code** -> Trust Chain skill
- **Working on constraint evaluation** -> Constraint System skill
- **Adding/modifying CLI commands** -> CLI Patterns skill
- **Working with the API layer** -> API Patterns skill
- **Adding or modifying CO domains** -> Domain Engine skill
- **Understanding module relationships** -> Architecture skill
- **Working on learning pipeline** -> Learning Pipeline skill
- **Working with database models/operations** -> Persistence skill
- **Working on MCP proxy** -> MCP Proxy skill
- **Security review or hardening** -> Security skill
