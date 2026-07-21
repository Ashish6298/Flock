# ADR 0032 – Enterprise CLI, Interactive REPL & Cluster Management Console

**Date**: 2026-07-21  
**Status**: Accepted  
**Phase**: 32 – Enterprise CLI, Interactive REPL & Cluster Management Console  
**Milestone**: J – Distributed Workflow Orchestration  

---

## Context

Flock requires operational commands execution registries, interactive REPL consoles, autocompleters, contexts config, profile management, and serialization layouts formatters.

---

## Decision

We implement a complete **Enterprise CLI, Interactive REPL & Cluster Management Console**:

1. **CommandRegistry**: Registers built-in operational commands.
2. **CommandParser**: Tokenizes string inputs to argument arrays.
3. **ReplEngine**: Manages session variables.
4. **AutoCompleteEngine**: Filters prefix candidates.
5. **CommandFormatter**: Renders output mappings in JSON and YAML configurations formats.
6. **ConfigurationManager**: Manages endpoints contexts.
7. **ProfileManager**: Registers user identity profiles.
8. **HistoryLogger**: Stores executed commands logs.
9. **SessionManager**: Tracks duration session limits.
10. **CommandExecutionEngine**: Runs commands after checking authorization profiles roles.
11. **CliService**: Registers handlers on the MessageBus.

---

## Consequences

- **Secure Execution**: Command permission checks verify user identity configurations before running action processes.
- **Context Flexibility**: Operator tools seamlessly transition target cluster configurations.
- **Unified Interface**: Integrates execution loops directly onto socket message structures.
