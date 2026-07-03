# autogen Developer Documentation

Welcome to the `autogen` developer documentation. `autogen` is a local-first, multi-agent engineering workbench built on the Microsoft Agent Framework (MAF).

## Core Philosophy

`autogen` is designed to run autonomous engineering workflows against a real repository with built-in safety, visibility, and control. It moves beyond the typical chat-bot paradigm by providing an orchestration model that coordinates multiple specialized agents under a structured, manager-led workflow.

### Key Features
- **Manager-Led Orchestration**: A structured workflow directing a planner, researcher, implementer, and reviewer.
- **Bounded Repo Operations**: Scoped tools that enforce boundaries on read/write operations to keep destructive changes from proceeding without approval.
- **Routed Provider Execution**: Dynamic routing across models and CLI providers depending on task requirements and availability.
- **Durable Artifacts**: Persisted session stores, run state, diffs, and attempts to ensure traceability and reproducibility.
- **Operator-Facing Dashboard**: A local UI for pausing, approving, and auditing workflow progression.

## Getting Started
Please refer to the repository `README.md` for the quickstart guide and environment setup.

## Next Steps
- [Architecture Overview](architecture.md) - Deep dive into the orchestration, agent interactions, and artifact stores.
