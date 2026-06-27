# Documentation Operating System

## Purpose

This `docs/` directory is the operating system for Inference Autopsy. It is the
single source of truth for product direction, architecture, engineering
standards, AI-agent behavior, and release discipline.

Inference Autopsy is an open-source local CLI, trace recorder, workload
replayer, report generator, and CI regression gate for OpenAI-compatible LLM
inference endpoints. The project optimizes for reproducible measurements,
clear diagnosis, static HTML reports, and maintainable Python code.

## Reference When

Read this file when onboarding, starting a task, configuring an AI coding tool,
or deciding which deeper documentation file to open.

## AI Agents Must Obey

Use this index to route work to the relevant standards and templates before
editing code, docs, examples, workflows, or public contracts.

## How to Use These Docs

Before changing code, humans and AI agents should read the smallest relevant
set of docs:

1. `docs/context/current-project-state.md` for current scope.
2. `docs/ai/task-execution-protocol.md` for the required workflow.
3. The matching engineering, frontend, product, or workflow standard.
4. The matching template in `docs/templates/`.
5. `docs/ai/definition-of-done.md` before finishing.

AI agents must treat these docs as constraints, not suggestions. If a requested
change conflicts with these docs, call out the conflict and propose the smallest
safe path forward.

## Directory Tree

```txt
docs/
  README.md
  ai/
    agent-rules.md
    coding-contract.md
    pr-review-checklist.md
    task-execution-protocol.md
    anti-patterns.md
    definition-of-done.md
    ide-integration.md
  engineering/
    principles.md
    architecture.md
    code-style.md
    naming-conventions.md
    project-structure.md
    error-handling.md
    logging-monitoring.md
    testing-strategy.md
    performance-guidelines.md
    security-guidelines.md
    api-design.md
    database-guidelines.md
    state-management.md
    dependency-policy.md
    refactoring-guidelines.md
  frontend/
    ui-principles.md
    design-system.md
    component-architecture.md
    accessibility.md
    responsive-design.md
    frontend-performance.md
    interaction-guidelines.md
    animation-guidelines.md
    content-design.md
    forms-and-validation.md
  product/
    project-spec.md
    owner-project-guide.md
    product-principles.md
    feature-spec-template.md
    roadmap.md
    user-personas.md
    decision-log.md
    kpi-framework.md
    feature-prioritization.md
  context/
    current-project-state.md
    domain-knowledge.md
    business-rules.md
    glossary.md
    known-issues.md
    technical-debt.md
  workflow/
    phase-1-build-guide.md
    phase-2-learning-notes.md
    phase-2-testing-guide.md
    development-lifecycle.md
    branching-strategy.md
    release-process.md
    code-review-process.md
    debugging-guide.md
    local-development.md
    deployment-checklists.md
  governance/
    decision-framework.md
    tech-stack-policy.md
    dependency-approval.md
    contribution-guidelines.md
    change-management.md
  templates/
    feature-implementation.md
    bug-fix.md
    refactoring.md
    migration.md
    api-addition.md
    ui-change.md
    performance-optimization.md
    incident-remediation.md
    architecture-rfc.md
    adr-template.md
    postmortem-template.md
  documentation/
    documentation-quality.md
    adr-guidelines.md
    changelog-guidelines.md
  enforcement/
    README.md
    ci-checks.md
    architecture-fitness.md
    code-ownership.md
    ai-validation.md
```

## File Catalog

| File | Purpose | Referenced When | AI Agents Must Obey |
| --- | --- | --- | --- |
| `ai/agent-rules.md` | Global AI behavior rules | Every task | Stay scoped, explicit, tested, and consistent |
| `ai/coding-contract.md` | Contract for code changes | Before editing code | Preserve architecture and user changes |
| `ai/pr-review-checklist.md` | Self-review checklist | Before PR or handoff | Find risks before declaring done |
| `ai/task-execution-protocol.md` | Task workflow | Start of any implementation | Inspect, plan, implement, verify, summarize |
| `ai/anti-patterns.md` | Forbidden patterns | Design and review | Reject complexity, coupling, and drift |
| `ai/definition-of-done.md` | Completion bar | Before finishing | Verify behavior, tests, docs, and risk |
| `ai/ide-integration.md` | Cursor, Claude, Copilot guidance | Configuring AI tools | Keep IDE memory aligned with docs |
| `engineering/*.md` | Technical standards | Any code change | Follow local architecture and quality rules |
| `frontend/*.md` | Static report and UI standards | Report or UI work | Make reports usable, accessible, and polished |
| `product/project-spec.md` | Hard product and resume contract | Before implementing V1 scope | Make every resume claim demonstrable |
| `product/owner-project-guide.md` | Human-facing complete project guide | Learning, planning, demos, and interview prep | Understand the project end to end |
| `product/*.md` | Product decision system | Planning features | Protect the local CLI and report-first product shape |
| `context/*.md` | Project memory | Onboarding and task start | Avoid re-learning known constraints |
| `workflow/phase-1-build-guide.md` | Step-by-step Phase 1 implementation guide | Building the first CLI/schema/JSONL/summary milestone | Keep Phase 1 focused and testable |
| `workflow/phase-2-learning-notes.md` | Concise Phase 2 concept notes | Learning the real client/parser path | Keep protocol and streaming concepts grounded |
| `workflow/phase-2-testing-guide.md` | Step-by-step Phase 2 testing guide | Verifying install, CLI, SSE parser, real endpoint calls, and trace output | Debug local setup and prove the single-request path |
| `workflow/*.md` | Development and release process | Daily execution | Keep changes reviewable and releasable |
| `governance/*.md` | Decision authority | Tradeoffs and policy | Escalate architectural changes explicitly |
| `templates/*.md` | Reusable execution templates | Starting task types | Fill risk, tests, rollback, and docs sections |
| `documentation/*.md` | Docs quality system | Writing docs | Keep docs current, concrete, and owned |
| `enforcement/*.md` | Automation and checks | CI and review | Convert rules into measurable checks |

## Maintenance Rules

- Update docs in the same change that changes behavior, architecture, CLI
  contracts, trace schema, metrics, report UX, or release process.
- Prefer specific examples over abstract principles.
- Mark temporary decisions with an owner and review date.
- Remove stale guidance instead of adding contradictory guidance.
- Keep these docs short enough to be read and strong enough to constrain work.
