# Changelog

## [1.1.0](https://github.com/Coding-Autopilot-System/autogen/compare/v1.0.0...v1.1.0) (2026-07-13)


### Features

* **01-01:** require explicit workspace selection at run creation ([f6e51f0](https://github.com/Coding-Autopilot-System/autogen/commit/f6e51f0a3c18acc1d3433ca4b735825d7a06cb8e))
* **01-01:** tighten workspace discovery and run schema ([70f9a96](https://github.com/Coding-Autopilot-System/autogen/commit/70f9a96cbc35f856a9d89aa1e789cd0c3d058469))
* **01-02:** normalize durable run storage layout ([dd3e281](https://github.com/Coding-Autopilot-System/autogen/commit/dd3e28157e9d867b00c7ac5c9c7a089d5159fb46))
* **01-02:** separate retry seeds from human decisions ([88c13de](https://github.com/Coding-Autopilot-System/autogen/commit/88c13de169b265d2e6ad17bd5130626fff1eb473))
* **01-03:** make MAF runtime workspace-scoped ([15d5a0d](https://github.com/Coding-Autopilot-System/autogen/commit/15d5a0dce8fa39313ffcb9f07827907eb83ed3b6))
* **01-03:** surface workspace freshness in dashboard runs ([47b6b3a](https://github.com/Coding-Autopilot-System/autogen/commit/47b6b3a810598632374d0ea6f51c5a8994356043))
* **02-01:** build manager orchestration contract ([c17e722](https://github.com/Coding-Autopilot-System/autogen/commit/c17e722f37aefdf783591ec8c0e44058a8d9c8ca))
* **02-02:** add stage-aware resume and gsd autofill ([d90a48f](https://github.com/Coding-Autopilot-System/autogen/commit/d90a48ff78d78d6d9e027e716f47f7baef2e5e74))
* **02-03:** surface orchestration state in dashboard ([ba1a3d6](https://github.com/Coding-Autopilot-System/autogen/commit/ba1a3d68f142e46315bddb10f912b376513f2ec2))
* **03-01:** add specialist roster and handoff contract ([a96d7c0](https://github.com/Coding-Autopilot-System/autogen/commit/a96d7c0d647adb543ac2f4b2c7ec6dc9a96efd38))
* **03-02:** formalize lane-first routing metadata ([3a57da3](https://github.com/Coding-Autopilot-System/autogen/commit/3a57da3277f7bed7e3e1580c78c2c6b495725df3))
* **03-02:** formalize routing visibility contract ([fcbf166](https://github.com/Coding-Autopilot-System/autogen/commit/fcbf1668da2694b2faf119c4c04133c76113bc37))
* **03-03:** expose specialist routing visibility ([4dcfa52](https://github.com/Coding-Autopilot-System/autogen/commit/4dcfa524401cf7e3fcf000ba3025efa6931d1ad9))
* **04:** add autonomous execution and approval guardrails ([076efdb](https://github.com/Coding-Autopilot-System/autogen/commit/076efdbe8fca3da4924b9181bc97199cf582f277))
* **05-01:** redesign operator shell and message surfaces ([f36ae38](https://github.com/Coding-Autopilot-System/autogen/commit/f36ae38e7068664ef4209a044d3f517af54eca25))
* **05-02:** add operator timeline and artifact views ([4755e17](https://github.com/Coding-Autopilot-System/autogen/commit/4755e17825c6e4285a94a7602170c9fdf64daa3f))
* **05-03:** polish operator workbench ergonomics ([a7bb2e6](https://github.com/Coding-Autopilot-System/autogen/commit/a7bb2e6e816e55ea86d98a25fc13de12f9b27b9d))
* **maf:** consolidate refresh stack and workflow hardening ([#17](https://github.com/Coding-Autopilot-System/autogen/issues/17)) ([b0524b7](https://github.com/Coding-Autopilot-System/autogen/commit/b0524b762024237d047fde25b50679da42e1a5e2))
* Phase 7 — Worker Boundary and Cloud-Safe Execution Profiles ([#2](https://github.com/Coding-Autopilot-System/autogen/issues/2)) ([f537373](https://github.com/Coding-Autopilot-System/autogen/commit/f537373ef92f61cd2afe93338cd5fbe987dc9056))
* **v1.2:** add Ollama tier-0 provider + OpenAPI 3.1 spec export ([fd40169](https://github.com/Coding-Autopilot-System/autogen/commit/fd4016920dc083d93f49dea3410940ca83d646db))


### Bug Fixes

* **api:** resolve F-04 enforce explicit non-credentialed CORS ([92e3adf](https://github.com/Coding-Autopilot-System/autogen/commit/92e3adfb2c79e4cea9b74cd13590effe6d521951))
* **audit:** resolve linting and formatting errors ([#5](https://github.com/Coding-Autopilot-System/autogen/issues/5)) ([5127cb9](https://github.com/Coding-Autopilot-System/autogen/commit/5127cb9d38bb5131542f8134985f473d39dc38c1))
* **ci:** repin release-please reusable workflow to reachable SHA ([#24](https://github.com/Coding-Autopilot-System/autogen/issues/24)) ([ca23646](https://github.com/Coding-Autopilot-System/autogen/commit/ca23646708d9b8e48fdba5025e664b7d4727609e))
* **ci:** resolve F-02 enforce full cross-platform validation ([7a6d8e3](https://github.com/Coding-Autopilot-System/autogen/commit/7a6d8e3a6bf204155053b9d1310c979b25a40557))
* **ci:** resolve F-02 enforce full cross-platform validation ([fa78d6b](https://github.com/Coding-Autopilot-System/autogen/commit/fa78d6b7659709dd8dcfc3e13485c71b50099f6b))
* **ci:** resolve F-02 use Node 24-compatible actions ([ad2d45d](https://github.com/Coding-Autopilot-System/autogen/commit/ad2d45dec2e61cb96151591f891e5c0577cb0f83))
* **ci:** resolve F-02 use Node 24-compatible actions ([19dcc4d](https://github.com/Coding-Autopilot-System/autogen/commit/19dcc4d7babccf18212f9364d7ad0323ee25c67b))
* **ci:** wire release-please PAT into reusable workflow caller ([#31](https://github.com/Coding-Autopilot-System/autogen/issues/31)) ([b952932](https://github.com/Coding-Autopilot-System/autogen/commit/b9529322287e9d04b23d83c2f28bd1561549f475))
* **execution:** resolve F-05 make repo writes atomic UTF-8 ([76eda85](https://github.com/Coding-Autopilot-System/autogen/commit/76eda85473e04294d0d5737e9ef67e40197ca509))
* **hygiene:** resolve F-06 protect secrets and runtime artifacts ([4975e0b](https://github.com/Coding-Autopilot-System/autogen/commit/4975e0b636da897ea839ad3021d34c24834a614e))
* **repo:** remove invalid worktree gitlink ([#29](https://github.com/Coding-Autopilot-System/autogen/issues/29)) ([6442cde](https://github.com/Coding-Autopilot-System/autogen/commit/6442cdef953094c028630f203f26b3e9f71af5c3))
* restore runnable enterprise-grade autogen workbench ([c829c76](https://github.com/Coding-Autopilot-System/autogen/commit/c829c76a594d3ca7012400c69a97ff43dda2682a))
* **runtime:** resolve F-01 restore runnable clean-clone contract ([65cb4f2](https://github.com/Coding-Autopilot-System/autogen/commit/65cb4f2d1aa8e9bba5d77a25498fc9860cba3d0f))
* **security:** resolve F-03 normalize cross-platform traversal paths ([d2c0fc1](https://github.com/Coding-Autopilot-System/autogen/commit/d2c0fc1faa28ceee2544543547f40f8694430a66))
* **storage:** resolve F-03 reject path traversal identifiers ([48bdb95](https://github.com/Coding-Autopilot-System/autogen/commit/48bdb95e6b36e6849f2524425918fc6440b6a51b))

## 1.0.0 (2026-07-11)


### Features

* **01-01:** require explicit workspace selection at run creation ([f6e51f0](https://github.com/Coding-Autopilot-System/autogen/commit/f6e51f0a3c18acc1d3433ca4b735825d7a06cb8e))
* **01-01:** tighten workspace discovery and run schema ([70f9a96](https://github.com/Coding-Autopilot-System/autogen/commit/70f9a96cbc35f856a9d89aa1e789cd0c3d058469))
* **01-02:** normalize durable run storage layout ([dd3e281](https://github.com/Coding-Autopilot-System/autogen/commit/dd3e28157e9d867b00c7ac5c9c7a089d5159fb46))
* **01-02:** separate retry seeds from human decisions ([88c13de](https://github.com/Coding-Autopilot-System/autogen/commit/88c13de169b265d2e6ad17bd5130626fff1eb473))
* **01-03:** make MAF runtime workspace-scoped ([15d5a0d](https://github.com/Coding-Autopilot-System/autogen/commit/15d5a0dce8fa39313ffcb9f07827907eb83ed3b6))
* **01-03:** surface workspace freshness in dashboard runs ([47b6b3a](https://github.com/Coding-Autopilot-System/autogen/commit/47b6b3a810598632374d0ea6f51c5a8994356043))
* **02-01:** build manager orchestration contract ([c17e722](https://github.com/Coding-Autopilot-System/autogen/commit/c17e722f37aefdf783591ec8c0e44058a8d9c8ca))
* **02-02:** add stage-aware resume and gsd autofill ([d90a48f](https://github.com/Coding-Autopilot-System/autogen/commit/d90a48ff78d78d6d9e027e716f47f7baef2e5e74))
* **02-03:** surface orchestration state in dashboard ([ba1a3d6](https://github.com/Coding-Autopilot-System/autogen/commit/ba1a3d68f142e46315bddb10f912b376513f2ec2))
* **03-01:** add specialist roster and handoff contract ([a96d7c0](https://github.com/Coding-Autopilot-System/autogen/commit/a96d7c0d647adb543ac2f4b2c7ec6dc9a96efd38))
* **03-02:** formalize lane-first routing metadata ([3a57da3](https://github.com/Coding-Autopilot-System/autogen/commit/3a57da3277f7bed7e3e1580c78c2c6b495725df3))
* **03-02:** formalize routing visibility contract ([fcbf166](https://github.com/Coding-Autopilot-System/autogen/commit/fcbf1668da2694b2faf119c4c04133c76113bc37))
* **03-03:** expose specialist routing visibility ([4dcfa52](https://github.com/Coding-Autopilot-System/autogen/commit/4dcfa524401cf7e3fcf000ba3025efa6931d1ad9))
* **04:** add autonomous execution and approval guardrails ([076efdb](https://github.com/Coding-Autopilot-System/autogen/commit/076efdbe8fca3da4924b9181bc97199cf582f277))
* **05-01:** redesign operator shell and message surfaces ([f36ae38](https://github.com/Coding-Autopilot-System/autogen/commit/f36ae38e7068664ef4209a044d3f517af54eca25))
* **05-02:** add operator timeline and artifact views ([4755e17](https://github.com/Coding-Autopilot-System/autogen/commit/4755e17825c6e4285a94a7602170c9fdf64daa3f))
* **05-03:** polish operator workbench ergonomics ([a7bb2e6](https://github.com/Coding-Autopilot-System/autogen/commit/a7bb2e6e816e55ea86d98a25fc13de12f9b27b9d))
* **maf:** consolidate refresh stack and workflow hardening ([#17](https://github.com/Coding-Autopilot-System/autogen/issues/17)) ([b0524b7](https://github.com/Coding-Autopilot-System/autogen/commit/b0524b762024237d047fde25b50679da42e1a5e2))
* Phase 7 — Worker Boundary and Cloud-Safe Execution Profiles ([#2](https://github.com/Coding-Autopilot-System/autogen/issues/2)) ([f537373](https://github.com/Coding-Autopilot-System/autogen/commit/f537373ef92f61cd2afe93338cd5fbe987dc9056))
* **v1.2:** add Ollama tier-0 provider + OpenAPI 3.1 spec export ([fd40169](https://github.com/Coding-Autopilot-System/autogen/commit/fd4016920dc083d93f49dea3410940ca83d646db))


### Bug Fixes

* **api:** resolve F-04 enforce explicit non-credentialed CORS ([92e3adf](https://github.com/Coding-Autopilot-System/autogen/commit/92e3adfb2c79e4cea9b74cd13590effe6d521951))
* **audit:** resolve linting and formatting errors ([#5](https://github.com/Coding-Autopilot-System/autogen/issues/5)) ([5127cb9](https://github.com/Coding-Autopilot-System/autogen/commit/5127cb9d38bb5131542f8134985f473d39dc38c1))
* **ci:** repin release-please reusable workflow to reachable SHA ([#24](https://github.com/Coding-Autopilot-System/autogen/issues/24)) ([ca23646](https://github.com/Coding-Autopilot-System/autogen/commit/ca23646708d9b8e48fdba5025e664b7d4727609e))
* **ci:** resolve F-02 enforce full cross-platform validation ([7a6d8e3](https://github.com/Coding-Autopilot-System/autogen/commit/7a6d8e3a6bf204155053b9d1310c979b25a40557))
* **ci:** resolve F-02 enforce full cross-platform validation ([fa78d6b](https://github.com/Coding-Autopilot-System/autogen/commit/fa78d6b7659709dd8dcfc3e13485c71b50099f6b))
* **ci:** resolve F-02 use Node 24-compatible actions ([ad2d45d](https://github.com/Coding-Autopilot-System/autogen/commit/ad2d45dec2e61cb96151591f891e5c0577cb0f83))
* **ci:** resolve F-02 use Node 24-compatible actions ([19dcc4d](https://github.com/Coding-Autopilot-System/autogen/commit/19dcc4d7babccf18212f9364d7ad0323ee25c67b))
* **execution:** resolve F-05 make repo writes atomic UTF-8 ([76eda85](https://github.com/Coding-Autopilot-System/autogen/commit/76eda85473e04294d0d5737e9ef67e40197ca509))
* **hygiene:** resolve F-06 protect secrets and runtime artifacts ([4975e0b](https://github.com/Coding-Autopilot-System/autogen/commit/4975e0b636da897ea839ad3021d34c24834a614e))
* restore runnable enterprise-grade autogen workbench ([c829c76](https://github.com/Coding-Autopilot-System/autogen/commit/c829c76a594d3ca7012400c69a97ff43dda2682a))
* **runtime:** resolve F-01 restore runnable clean-clone contract ([65cb4f2](https://github.com/Coding-Autopilot-System/autogen/commit/65cb4f2d1aa8e9bba5d77a25498fc9860cba3d0f))
* **security:** resolve F-03 normalize cross-platform traversal paths ([d2c0fc1](https://github.com/Coding-Autopilot-System/autogen/commit/d2c0fc1faa28ceee2544543547f40f8694430a66))
* **storage:** resolve F-03 reject path traversal identifiers ([48bdb95](https://github.com/Coding-Autopilot-System/autogen/commit/48bdb95e6b36e6849f2524425918fc6440b6a51b))
