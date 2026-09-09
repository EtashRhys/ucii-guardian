# UCII Guardian

UCII Guardian is a lean authority-control agent built with AWS Strands Agents for the 2026 Agents for Humans Hackathon.

Guardian turns human intent into bounded autonomous authority: routine actions may proceed when cryptographically verified authority permits them; consequential actions outside that authority are escalated to the human; revoked or invalid authority fails closed.

## Core product promise

> Guardian may reason about what should happen, but it may never manufacture permission to make it happen.

Guardian is intentionally narrow. It is not a general-purpose assistant, workflow platform, multi-agent system, identity provider, or replacement for UCII.

## Architecture boundary

```text
Human
  |
  v
UCII Guardian / AWS Strands Agent
  |
  | proposed normalized action
  v
UCII identity + credential + authorization boundary
  |
  +--> ALLOW -----------------> protected executor
  |
  +--> ESCALATION_REQUIRED ---> human approval / denial
  |
  +--> DENY ------------------> no execution
  |
  v
Durable provenance
```

AWS Strands Agents owns the agentic reasoning/orchestration loop. UCII remains authoritative for identity, credentials, authorization, revocation, and trust. Guardian owns the human-facing authority experience and protected action orchestration.

## Hackathon demonstration target

The initial Guardian build is complete when it can demonstrate one coherent authority lifecycle:

1. A routine action succeeds under existing bounded authority.
2. An action outside that authority does not execute and is escalated.
3. A human explicitly approves or denies the exceptional action.
4. An approved exceptional action executes only under bounded approval.
5. Existing authority is revoked.
6. A later attempt that previously would have succeeded is denied after revocation.
7. A durable provenance record explains what was requested, what authority was checked, what decision occurred, who made the consequential decision, and whether execution happened.

## Non-goals for the hackathon build

Guardian v1 will not become a monolith. The initial scope excludes generalized browsing, vector memory, multi-agent swarms, a workflow builder, mobile applications, voice, marketplaces, broad third-party integrations, duplicate identity/authorization systems, Scout integration, Ambassador integration, and Mission Control integration.

## Repository status

**Phase:** Foundation / Objective 0  
**Visibility:** Private during development  
**Primary track:** Professional Agents  
**Deadline:** September 14, 2026

See `docs/guardian-contract.md` for the governing authority invariants and `docs/roadmap.md` for the bounded build sequence.
