# Codebase Concerns

**Analysis Date:** 2026-03-20

## Tech Debt

**Dual runtime stacks (`maf_starter/` vs `autogen_*`):**
- Issue: the repo keeps both the active MAF runtime and a substantial legacy AutoGen runtime
- Why: the project migrated paths without removing the older dashboard and provider implementation
- Impact: provider logic, config assumptions, and session behavior can drift in two places
- Fix approach: either retire the legacy stack or clearly isolate and test it as a separate supported mode

**Incomplete dependency manifest:**
- Issue: `requirements.txt` only declares the core MAF stack, while active and legacy code import additional packages such as FastAPI, Anthropic support, and AutoGen modules
- Why: the environment evolved incrementally around a working local setup
- Impact: clean environment setup is fragile and can fail depending on transitive or manually installed packages
- Fix approach: align the manifest with all supported code paths or split active and legacy requirements cleanly

**Duplicated config surfaces:**
- Issue: `maf_starter/config.py` and `autogen_starter/config.py` model similar concerns separately
- Why: the repo carries both generations of runtime
- Impact: provider and env changes must be updated twice or they drift
- Fix approach: centralize provider/config primitives or hard-deprecate the old path

## Known Bugs / Risky Behaviors

**Repo-aware dashboard assumes Git checkout:**
- Symptoms: repo-context features in the legacy dashboard can fail when the repo root is not a git repository
- Trigger: using `autogen_dashboard/repo_context.py` in a workspace without `.git`
- Workaround: run the repo inside a real git checkout or avoid the legacy repo-context path
- Root cause: repo discovery and summary logic expects git metadata to exist

**DevUI UI patch drift risk:**
- Symptoms: route styling and message reshaping can silently stop working after DevUI version changes
- Trigger: upgrading `agent-framework-devui` or changing its shipped frontend bundle
- Workaround: keep the current beta version pinned and validate the patch after upgrades
- Root cause: `maf_starter/devui_patches.py` and `maf_starter/devui_overrides.py` hook private, version-coupled internals

## Security Considerations

**Repo tool file access:**
- Risk: `maf_starter/tools.py` can read and search any text file under the repo root and does not explicitly exclude `.env`
- Current mitigation: repo-root boundary enforcement only
- Recommendations: explicitly deny secret-bearing paths and consider a safer allowlist for agent-readable files

**Legacy dashboard exposure:**
- Risk: `autogen_dashboard/app.py` has mutable session endpoints with permissive CORS and no auth layer
- Current mitigation: intended localhost-only usage
- Recommendations: keep it local-only, restrict host binding, or add authentication before broader exposure

**Plaintext local artifacts:**
- Risk: transcripts, session events, checkpoints, and runtime logs are stored in plaintext under `state/` and root log files
- Current mitigation: `state/` is gitignored
- Recommendations: review retention, expand ignore rules for root logs, and avoid storing sensitive prompts when possible

## Performance Bottlenecks

**Recursive repo scanning in tools:**
- Problem: `maf_starter/tools.py` walks the filesystem with `rglob()` and a small skip list
- Measurement: no numeric benchmark recorded
- Cause: simple implementation optimized for convenience over repo scale
- Improvement path: add stronger exclusions, caching, and tighter file selection for larger repos

**Legacy dashboard frontend size:**
- Problem: `autogen_dashboard/static/app.js` is a very large single-file client script
- Measurement: source file size is large enough to be a clear regression hotspot
- Cause: UI behavior accumulated in one module
- Improvement path: split the client into smaller modules or treat the old dashboard as frozen/legacy

## Fragile Areas

**`maf_starter/devui_overrides.py`:**
- Why fragile: it rewrites the served DevUI JS bundle using string matching against known renderer content
- Common failures: DevUI upgrades break route panel injection or styling with no compile-time signal
- Safe modification: change alongside pinned DevUI version checks and revalidate with manual UI smoke tests
- Test coverage: partial; bundle and root injection are tested, but full browser rendering is not

**`maf_starter/provider_fallback.py`:**
- Why fragile: it mixes provider heuristics, CLI subprocess calls, route metadata, and response wrapping
- Common failures: model-name drift, changed quota error wording, or inconsistent tool availability on fallback
- Safe modification: keep changes small, add targeted tests, and validate at least one live fallback path
- Test coverage: moderate helper coverage, not exhaustive end-to-end provider coverage

**`autogen_dashboard/session_runner.py`:**
- Why fragile: it is a large mixed state machine for prompts, fallback, events, and persistence
- Common failures: edge-case session transitions and fallback-state bugs
- Safe modification: refactor behind tests before major behavior changes
- Test coverage: weak in the current checked-in test set

## Dependencies at Risk

**`agent-framework-devui` beta pin:**
- Risk: version-specific internals can break the UI patch layer
- Impact: DevUI customization fails even if the base runtime still works
- Migration plan: keep it pinned or move to a custom UI that does not patch private internals

**Preview model defaults and hard-coded names:**
- Risk: preview Gemini model IDs and CLI defaults can expire or change semantics
- Impact: routing and fallback can break without code changes elsewhere
- Migration plan: centralize model catalog management and validate via probe commands regularly

## Test Coverage Gaps

**Legacy dashboard runtime:**
- What's not tested: most of `autogen_dashboard/app.py`, `autogen_dashboard/session_runner.py`, and the static UI behavior
- Risk: regressions in the retained legacy stack can go unnoticed
- Priority: High if the legacy dashboard remains supported
- Difficulty to test: Medium; needs API and frontend coverage reinstated

**Real browser validation for DevUI customization:**
- What's not tested: final DOM rendering of route panels/cards in a browser
- Risk: server-side patching can appear correct while the browser still renders poorly
- Priority: Medium
- Difficulty to test: Medium; requires browser automation or a lightweight UI harness

**Hermetic config testing:**
- What's not tested: all runtime flows with fully synthetic env/config inputs
- Risk: tests depend too much on the local workstation setup
- Priority: Medium
- Difficulty to test: Low to Medium

---

*Concerns audit: 2026-03-20*
*Update as issues are fixed or new ones are discovered*
