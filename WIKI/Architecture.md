# Architecture

Autogen utilizes a dynamic Graph-of-Agents approach managed by a Meta-Manager.

## Swarm Orchestration Flow

\\\mermaid
graph TD;
    User[User Prompt] --> Meta[Meta-Manager]
    Meta -->|Spawns Swarm| Planner[Planner Agent]
    Planner --> Researcher[Researcher Agent]
    Researcher --> Implementer[Implementer Agent]
    Implementer --> Reviewer[Reviewer Agent]
    Reviewer -->|MCTS Execution| Sandbox[Simulation Sandbox]
    Sandbox -->|Winning Path| MainBranch[Main Branch]
    
    Watchdog[Autonomous Watchdog] -.->|Monitors Health| Meta
    Watchdog -->|Failure| TestGen[Generates pytest]
\\\

## Memory Subsystem
The system utilizes **ChromaDB** for hyper-dimensional vector embeddings, allowing it to retrieve lessons learned from past runs instantaneously.
