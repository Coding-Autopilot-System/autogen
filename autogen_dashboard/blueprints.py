import json

def generate_blueprint_event(nodes, edges):
    return [
        {
            "type": "snapshot",
            "nodes": nodes,
            "edges": edges
        }
    ]

# PHASE 1: Planning and Architecture
phase1_nodes = [
    {"id": "p1-group", "label": "Phase 1: Planning & Architecture", "type": "phaseGroup", "status": "Active Pipeline", "style": {"width": 1600, "height": 600}},
    {"id": "human-operator", "label": "Human Operator (You)", "type": "customNode", "status": "System Prompt", "instructions": "You govern the entire OS.", "parentId": "p1-group"},
    {"id": "1.1", "label": "Intent Translation", "type": "meta", "status": "Active", "instructions": "Translating user stories to verifyable endpoints.", "parentId": "p1-group"},
    {"id": "1.2", "label": "Rev-Eng SRS", "type": "agent", "status": "Idle", "instructions": "Mining commits for Requirements.", "parentId": "p1-group"},
    {"id": "1.3", "label": "Dependency Mapping", "type": "agent", "status": "Idle", "instructions": "Traversing enterprise architecture via MCP.", "parentId": "p1-group"},
    {"id": "1.4", "label": "IaC Planning", "type": "agent", "status": "Idle", "instructions": "Drafting Terraform configs.", "parentId": "p1-group"},
    {"id": "1.5", "label": "Work Breakdown", "type": "agent", "status": "Idle", "instructions": "Splitting epics into atomic tasks.", "parentId": "p1-group"},
    {"id": "1.6", "label": "API Contract", "type": "agent", "status": "Idle", "instructions": "Negotiating OpenAPI specifications.", "parentId": "p1-group"},
    {"id": "1.7", "label": "Threat Modeling", "type": "agent", "status": "Idle", "instructions": "Analyzing against OWASP Top 10.", "parentId": "p1-group"}
]
phase1_edges = [
    {"type": "edge_created", "data": {"id": "p1-e0", "source": "human-operator", "target": "1.1", "label": "Triggers Phase"}},
    {"type": "edge_created", "data": {"id": "p1-e1", "source": "1.1", "target": "1.5", "label": "Provides specs"}},
    {"type": "edge_created", "data": {"id": "p1-e2", "source": "1.2", "target": "1.1", "label": "Feeds into"}},
    {"type": "edge_created", "data": {"id": "p1-e3", "source": "1.5", "target": "1.6", "label": "Spawns API work"}},
    {"type": "edge_created", "data": {"id": "p1-e4", "source": "1.5", "target": "1.3", "label": "Maps deps"}},
    {"type": "edge_created", "data": {"id": "p1-e5", "source": "1.3", "target": "1.4", "label": "Plans IaC"}},
    {"type": "edge_created", "data": {"id": "p1-e6", "source": "1.4", "target": "1.7", "label": "Secures IaC"}}
]
PHASE1_BLUEPRINT = generate_blueprint_event(phase1_nodes, phase1_edges)

# PHASE 2: Development and Generation
phase2_nodes = [
    {"id": "p2-group", "label": "Phase 2: Development & Generation", "type": "phaseGroup", "status": "Active Pipeline", "style": {"width": 1600, "height": 600}},
    {"id": "human-operator", "label": "Human Operator (You)", "type": "customNode", "status": "System Prompt", "instructions": "You govern the entire OS.", "parentId": "p2-group"},
    {"id": "2.1", "label": "Feature Impl (GSD)", "type": "meta", "status": "Active", "instructions": "Writing code in isolated workspaces.", "parentId": "p2-group"},
    {"id": "2.2", "label": "Cross-File Refactor", "type": "agent", "status": "Idle", "instructions": "Optimizing structure and fixing compiler errors.", "parentId": "p2-group"},
    {"id": "2.3", "label": "Scaffold Gen", "type": "agent", "status": "Idle", "instructions": "Generating project architecture.", "parentId": "p2-group"},
    {"id": "2.4", "label": "API Endpoint", "type": "agent", "status": "Idle", "instructions": "Synthesizing backend logic.", "parentId": "p2-group"},
    {"id": "2.5", "label": "UI Component", "type": "agent", "status": "Idle", "instructions": "Iterating DOM and CSS.", "parentId": "p2-group"},
    {"id": "2.6", "label": "Legacy Translation", "type": "agent", "status": "Idle", "instructions": "Translating legacy services.", "parentId": "p2-group"},
    {"id": "2.7", "label": "Code Documentation", "type": "agent", "status": "Idle", "instructions": "Generating inline comments and READMEs.", "parentId": "p2-group"}
]
phase2_edges = [
    {"type": "edge_created", "data": {"id": "p2-e0", "source": "human-operator", "target": "2.1", "label": "Triggers Phase"}},
    {"type": "edge_created", "data": {"id": "p2-e1", "source": "2.3", "target": "2.1", "label": "Scaffolds"}},
    {"type": "edge_created", "data": {"id": "p2-e2", "source": "2.1", "target": "2.4", "label": "Builds backend"}},
    {"type": "edge_created", "data": {"id": "p2-e3", "source": "2.1", "target": "2.5", "label": "Builds frontend"}},
    {"type": "edge_created", "data": {"id": "p2-e4", "source": "2.6", "target": "2.2", "label": "Refactors"}},
    {"type": "edge_created", "data": {"id": "p2-e5", "source": "2.1", "target": "2.7", "label": "Documents"}}
]
PHASE2_BLUEPRINT = generate_blueprint_event(phase2_nodes, phase2_edges)

# PHASE 3: Testing and QA
phase3_nodes = [
    {"id": "p3-group", "label": "Phase 3: Testing & Quality Assurance", "type": "phaseGroup", "status": "Active Pipeline", "style": {"width": 1600, "height": 600}},
    {"id": "human-operator", "label": "Human Operator (You)", "type": "customNode", "status": "System Prompt", "instructions": "You govern the entire OS.", "parentId": "p3-group"},
    {"id": "3.1", "label": "Auto Test Gen", "type": "agent", "status": "Active", "instructions": "Evaluating codebase and writing missing tests.", "parentId": "p3-group"},
    {"id": "3.2", "label": "Flaky Test Res", "type": "agent", "status": "Idle", "instructions": "Fixing brittle UI locators.", "parentId": "p3-group"},
    {"id": "3.3", "label": "F2P Validation", "type": "sandbox", "status": "Running", "instructions": "Re-running tests until green.", "parentId": "p3-group"},
    {"id": "3.4", "label": "Performance Bench", "type": "agent", "status": "Idle", "instructions": "Executing A/B load tests.", "parentId": "p3-group"},
    {"id": "3.5", "label": "Edge Case Fuzzing", "type": "agent", "status": "Idle", "instructions": "Generating hostile inputs.", "parentId": "p3-group"},
    {"id": "3.6", "label": "Mobile Cert", "type": "sandbox", "status": "Idle", "instructions": "Live screen hierarchy inspection.", "parentId": "p3-group"},
    {"id": "3.7", "label": "Pipeline Sim", "type": "meta", "status": "Idle", "instructions": "Simulating all microservices locally.", "parentId": "p3-group"}
]
phase3_edges = [
    {"type": "edge_created", "data": {"id": "p3-e0", "source": "human-operator", "target": "3.1", "label": "Triggers Phase"}},
    {"type": "edge_created", "data": {"id": "p3-e1", "source": "3.1", "target": "3.3", "label": "Feeds tests"}},
    {"type": "edge_created", "data": {"id": "p3-e2", "source": "3.5", "target": "3.3", "label": "Breaks tests"}},
    {"type": "edge_created", "data": {"id": "p3-e3", "source": "3.3", "target": "3.7", "label": "Triggers Pipeline"}},
    {"type": "edge_created", "data": {"id": "p3-e4", "source": "3.7", "target": "3.4", "label": "Profiles"}},
    {"type": "edge_created", "data": {"id": "p3-e5", "source": "3.7", "target": "3.6", "label": "Runs on Device"}},
    {"type": "edge_created", "data": {"id": "p3-e6", "source": "3.2", "target": "3.7", "label": "Stabilizes"}}
]
PHASE3_BLUEPRINT = generate_blueprint_event(phase3_nodes, phase3_edges)

# PHASE 4: Security and DevSecOps
phase4_nodes = [
    {"id": "p4-group", "label": "Phase 4: Security & DevSecOps", "type": "phaseGroup", "status": "Active Pipeline", "style": {"width": 1600, "height": 600}},
    {"id": "human-operator", "label": "Human Operator (You)", "type": "customNode", "status": "System Prompt", "instructions": "You govern the entire OS.", "parentId": "p4-group"},
    {"id": "4.1", "label": "Auto Patching", "type": "agent", "status": "Active", "instructions": "Rewriting code safely to clear SAST alerts.", "parentId": "p4-group"},
    {"id": "4.2", "label": "Dep Upgrade", "type": "agent", "status": "Idle", "instructions": "Identifying and swapping outdated libraries.", "parentId": "p4-group"},
    {"id": "4.3", "label": "False-Pos Triage", "type": "agent", "status": "Idle", "instructions": "Evaluating ASTs for reachability.", "parentId": "p4-group"},
    {"id": "4.4", "label": "Guardrail Enforce", "type": "sandbox", "status": "Active", "instructions": "Blocking operations violating boundaries.", "parentId": "p4-group"},
    {"id": "4.5", "label": "Secrets Detection", "type": "agent", "status": "Idle", "instructions": "Scrubbing repo history of API keys.", "parentId": "p4-group"},
    {"id": "4.6", "label": "Compliance Audit", "type": "meta", "status": "Idle", "instructions": "Gathering immutability logs for audits.", "parentId": "p4-group"},
    {"id": "4.7", "label": "Attack Modeling", "type": "agent", "status": "Idle", "instructions": "Simulating external breaches.", "parentId": "p4-group"}
]
phase4_edges = [
    {"type": "edge_created", "data": {"id": "p4-e0", "source": "human-operator", "target": "4.1", "label": "Triggers Phase"}},
    {"type": "edge_created", "data": {"id": "p4-e1", "source": "4.7", "target": "4.1", "label": "Finds path"}},
    {"type": "edge_created", "data": {"id": "p4-e2", "source": "4.1", "target": "4.3", "label": "Triages"}},
    {"type": "edge_created", "data": {"id": "p4-e3", "source": "4.4", "target": "4.6", "label": "Logs"}},
    {"type": "edge_created", "data": {"id": "p4-e4", "source": "4.5", "target": "4.4", "label": "Blocks push"}},
    {"type": "edge_created", "data": {"id": "p4-e5", "source": "4.2", "target": "4.4", "label": "Scans dep"}}
]
PHASE4_BLUEPRINT = generate_blueprint_event(phase4_nodes, phase4_edges)

# PHASE 5: Deployment and SRE
phase5_nodes = [
    {"id": "p5-group", "label": "Phase 5: Deployment & SRE", "type": "phaseGroup", "status": "Active Pipeline", "style": {"width": 1600, "height": 600}},
    {"id": "human-operator", "label": "Human Operator (You)", "type": "customNode", "status": "System Prompt", "instructions": "You govern the entire OS.", "parentId": "p5-group"},
    {"id": "5.1", "label": "PR Review", "type": "meta", "status": "Active", "instructions": "Executing final merge upon policy satisfaction.", "parentId": "p5-group"},
    {"id": "5.2", "label": "Auto Rollback", "type": "agent", "status": "Idle", "instructions": "Reverting system state on anomaly.", "parentId": "p5-group"},
    {"id": "5.3", "label": "Root Cause Analysis", "type": "agent", "status": "Idle", "instructions": "Deduplicating remediation plans.", "parentId": "p5-group"},
    {"id": "5.4", "label": "Self-Healing Infra", "type": "sandbox", "status": "Running", "instructions": "Restarting pods to restore health.", "parentId": "p5-group"},
    {"id": "5.5", "label": "SOP Extraction", "type": "agent", "status": "Idle", "instructions": "Generating wiki SOPs.", "parentId": "p5-group"},
    {"id": "5.6", "label": "Sandbox Lifecycle", "type": "meta", "status": "Idle", "instructions": "Provisioning secure ephemeral containers.", "parentId": "p5-group"},
    {"id": "5.7", "label": "Multi-Region Orchestration", "type": "agent", "status": "Idle", "instructions": "Staged global rollout.", "parentId": "p5-group"}
]
phase5_edges = [
    {"type": "edge_created", "data": {"id": "p5-e0", "source": "human-operator", "target": "5.1", "label": "Triggers Phase"}},
    {"type": "edge_created", "data": {"id": "p5-e1", "source": "5.1", "target": "5.6", "label": "Spawns sandbox"}},
    {"type": "edge_created", "data": {"id": "p5-e2", "source": "5.6", "target": "5.7", "label": "Deploys"}},
    {"type": "edge_created", "data": {"id": "p5-e3", "source": "5.7", "target": "5.2", "label": "Monitors", "style": {"stroke": "red", "strokeDasharray": "5,5"}}},
    {"type": "edge_created", "data": {"id": "p5-e4", "source": "5.2", "target": "5.3", "label": "Triggers RCA"}},
    {"type": "edge_created", "data": {"id": "p5-e5", "source": "5.3", "target": "5.5", "label": "Writes SOP"}},
    {"type": "edge_created", "data": {"id": "p5-e6", "source": "5.4", "target": "5.7", "label": "Heals nodes"}}
]
PHASE5_BLUEPRINT = generate_blueprint_event(phase5_nodes, phase5_edges)

# PHASE 6: Maintenance and Knowledge
phase6_nodes = [
    {"id": "p6-group", "label": "Phase 6: Maintenance & Knowledge", "type": "phaseGroup", "status": "Active Pipeline", "style": {"width": 1600, "height": 600}},
    {"id": "human-operator", "label": "Human Operator (You)", "type": "customNode", "status": "System Prompt", "instructions": "You govern the entire OS.", "parentId": "p6-group"},
    {"id": "6.1", "label": "Continuous Tech Debt", "type": "agent", "status": "Active", "instructions": "Refactoring overgrown god-files.", "parentId": "p6-group"},
    {"id": "6.2", "label": "Memory Sync", "type": "agent", "status": "Idle", "instructions": "Distilling behavioral history to vectors.", "parentId": "p6-group"},
    {"id": "6.3", "label": "Ruleset Updating", "type": "agent", "status": "Idle", "instructions": "Updating AGENTS.md dynamically.", "parentId": "p6-group"},
    {"id": "6.4", "label": "Multi-Repo Triage", "type": "meta", "status": "Running", "instructions": "Scanning global issue trackers.", "parentId": "p6-group"},
    {"id": "6.5", "label": "Stale Deprecation", "type": "agent", "status": "Idle", "instructions": "Removing dead API code.", "parentId": "p6-group"},
    {"id": "6.6", "label": "DB Schema Migration", "type": "agent", "status": "Idle", "instructions": "Drafting zero-downtime migrations.", "parentId": "p6-group"},
    {"id": "6.7", "label": "Knowledge Deduplication", "type": "agent", "status": "Idle", "instructions": "Resolving wiki discrepancies.", "parentId": "p6-group"}
]
phase6_edges = [
    {"type": "edge_created", "data": {"id": "p6-e0", "source": "human-operator", "target": "6.1", "label": "Triggers Phase"}},
    {"type": "edge_created", "data": {"id": "p6-e1", "source": "6.4", "target": "6.1", "label": "Finds debt"}},
    {"type": "edge_created", "data": {"id": "p6-e2", "source": "6.1", "target": "6.2", "label": "Saves state"}},
    {"type": "edge_created", "data": {"id": "p6-e3", "source": "6.4", "target": "6.3", "label": "Finds pattern"}},
    {"type": "edge_created", "data": {"id": "p6-e4", "source": "6.4", "target": "6.5", "label": "Finds stale"}},
    {"type": "edge_created", "data": {"id": "p6-e5", "source": "6.5", "target": "6.6", "label": "Cleans DB"}},
    {"type": "edge_created", "data": {"id": "p6-e6", "source": "6.3", "target": "6.7", "label": "Updates docs"}}
]
PHASE6_BLUEPRINT = generate_blueprint_event(phase6_nodes, phase6_edges)
