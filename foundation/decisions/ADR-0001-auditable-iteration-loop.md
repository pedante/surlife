# ADR-0001 — Auditable, model-independent planning loop

**Date:** 2026-10-11  
**Status:** accepted as initial repository workflow by user request (not validation of the arena design)  
**Affected scope:** foundation/ and AI reviewer instructions

## Context
Surlife aims to improve its project ideas through repeated criticism by Codex and other LLMs. Unstructured back-and-forth would overwrite historical proposals, make critiques mutually dependent and confuse conceptual elegance with verified progress.

## Decision
Use one current working PLAN.md, immutable numbered proposal snapshots, separate independent review records, evidence-aware synthesis, a decision log and human-approved revisions. AGENTS.md provides directions for Codex; standalone prompts serve models without repository-instruction support.

## Alternatives not chosen
- Automatically allow models to overwrite the same plan repeatedly (history and accountability lost).
- Put every reviewer exchange in one giant Markdown file (hard to compare and version).
- Start by building an orchestration service that triggers continuous paid review calls (unnecessary complexity).

## Costs and tradeoffs
This requires some bookkeeping and human attention. Reviews can still share biases, invent evidence, or optimize text rather than the actual experiment.

## Verification
First round passes the workflow only when two independently saved critiques of one frozen proposal can be synthesized, decisions traced to sources, and a next proposal generated without modifying the first.

## Revision trigger
If review bookkeeping becomes harder than the experimental questions, reduce template fields while preserving frozen snapshots and traceability.
