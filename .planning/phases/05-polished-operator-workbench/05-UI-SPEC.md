---
phase: 5
slug: polished-operator-workbench
status: draft
shadcn_initialized: false
preset: none
created: 2026-03-22
---

# Phase 5 - UI Design Contract

> Visual and interaction contract for frontend phases. Generated for the operator workbench product surface.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none |
| Icon library | inline SVG and Unicode-safe text symbols only |
| Font | `Aptos` for UI text, `Iowan Old Style` for display headings, `Cascadia Mono` for technical strings |

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Inline chips, icon gaps, micro-padding |
| sm | 8px | Compact controls and label spacing |
| md | 16px | Default element spacing and form rhythm |
| lg | 24px | Card padding and section spacing |
| xl | 32px | Workspace and panel gaps |
| 2xl | 48px | Major section breaks and large cards |
| 3xl | 64px | Hero and page-level spacing |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 15px | 400 | 1.6 |
| Label | 12px | 700 | 1.2 |
| Heading | 20px | 700 | 1.15 |
| Display | 48px | 700 | 1.05 |

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#f5f0e8` | Page background, soft atmospheric fills, large surfaces |
| Secondary (30%) | `#fffaf4` | Cards, rails, control panels, transcript surfaces |
| Accent (10%) | `#0f766e` | Primary CTA, selected state, route chips, active tabs, key status indicators |
| Destructive | `#b42318` | Destructive actions, failure state, risky approval scopes only |

Accent reserved for: primary actions, active tab state, selected session state, route and model chips, and positive system status indicators

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | Start run |
| Empty state heading | No run selected |
| Empty state body | Choose a run from the queue or create a new one to inspect routing, specialists, timeline, and artifacts. |
| Error state | Run action failed. Inspect the status strip, adjust the prompt or approval, then retry. |
| Destructive confirmation | Approve risky action: review the exact scope before continuing. |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| none | none | not required |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-03-22
