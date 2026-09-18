# UCII Guardian — Managed Usage Economics and Cost-Control Contract

Status: **DOCUMENTED FOR POST-HACKATHON PRODUCTIZATION**

Date: 2026-09-18

## Purpose

UCII Guardian is built with the Strands Agents SDK and UCII. With the UCII SDK now publicly distributable, external developers can build Guardian-style authority enforcement around autonomous agents, including Grok Bot integrations where the developer controls a consequential-action enforcement point.

This creates two distinct economic cases that must not be conflated:

1. **Developer-hosted Guardian protection** — the developer uses the UCII SDK/API while paying for and controlling their own model, Strands process, tools, AWS account, browser, search, compute, and other agent resources.
2. **UCII-managed Guardian/agent execution** — UCII provides a hosted service that consumes UCII-controlled AWS/model/tool resources on behalf of an external caller.

The second case creates direct cost exposure for UCII and therefore requires structural economic controls before broad public availability.

## Strands itself is not the metered service

As of 2026-09-18, the official Strands documentation describes Strands Agents as an open-source SDK and explicitly as **a library, not a platform**. Strands runs inside the application's own process. It can use Amazon Bedrock or other model providers.

Therefore:

> **The Strands SDK itself is not the primary usage bill. The bill comes from the infrastructure and services the agent invokes.**

Relevant official documentation:

- https://strandsagents.com/
- https://strandsagents.com/docs/user-guide/quickstart/overview/
- https://strandsagents.com/docs/user-guide/concepts/model-providers/

Pricing and architecture must be revalidated against current provider documentation before production pricing is changed.

## AWS AgentCore reference pricing snapshot

The following is a **2026-09-18 reference snapshot**, not a permanent price guarantee.

Official AWS source:

- https://aws.amazon.com/bedrock/agentcore/pricing/

At this snapshot, AWS describes AgentCore as consumption-based with no upfront commitment or minimum fee. Selected published rates relevant to managed agent execution include:

| Capability | Published reference price |
| --- | ---: |
| Runtime microVM CPU | $0.0895 per vCPU-hour |
| Runtime microVM memory | $0.00945 per GB-hour |
| Browser CPU | $0.0895 per vCPU-hour |
| Browser memory | $0.00945 per GB-hour |
| Code Interpreter CPU | $0.0895 per vCPU-hour |
| Code Interpreter memory | $0.00945 per GB-hour |
| Web Search | $7.00 per 1,000 queries |
| Gateway API invocation | $0.005 per 1,000 invocations |
| Gateway Search API | $0.025 per 1,000 invocations |
| Short-term memory | $0.25 per 1,000 new events |
| Long-term memory retrieval | $0.50 per 1,000 retrievals |
| Observability | CloudWatch pricing applies |

AWS's published Runtime example uses 18 seconds of active CPU in a 60-second session with varying memory consumption and calculates approximately **$0.0007235 per session** for Runtime CPU + memory. AWS's example scales that specific workload to approximately **$7,235 for 10 million sessions**.

Those examples do **not** establish Guardian's unit cost. Guardian's actual cost depends on its selected model, tokens, number of model turns, tools, searches, browser/code usage, runtime, storage, networking, observability, and any other attached service.

## Primary economic risk

The principal risk is not constructing a Strands agent object. It is allowing an externally initiated agent loop to consume unbounded paid resources.

A poorly constrained flow could become:

```text
external request
  -> model inference
  -> tool
  -> model inference
  -> browser/search
  -> model inference
  -> retry
  -> tool
  -> model inference
  -> ...
```

Each iteration can increase model-token and service consumption.

A public endpoint backed by UCII-funded AWS/model resources MUST NOT depend on user restraint or model behavior to keep the bill bounded.

> **An external user or autonomous agent must never have the ability to create unbounded spend on UCII-controlled infrastructure.**

## Economic separation

Guardian authority and Guardian service economics are separate domains.

```text
identity != authority
authority != payment
payment != execution
entitlement != authority
economic allowance != delegated action authority
```

Paying for service cannot manufacture action authority.

Receiving a first-party/service entitlement cannot manufacture action authority.

Having action authority cannot imply unlimited infrastructure consumption.

The protected executor must satisfy every applicable domain independently.

## External developer model

Where an external developer runs their own Strands/model/tool infrastructure:

```text
External Grok Bot / agent
        |
        v
developer-controlled consequential action boundary
        |
        v
UCII SDK / authoritative UCII service
        |
        v
identity + authentication + authorization
        |
   DENY / ALLOW
        |
        v
developer-controlled executor
```

The developer bears their own agent/model/tool infrastructure costs.

UCII economics apply only to applicable UCII authoritative operations under the UCII service's published economic policy.

This is the preferred low-cost adoption path for third-party Guardian protection.

## UCII-managed service model

If UCII operates the agent/model/tool infrastructure:

```text
external principal / agent
        |
        v
UCII identity + authentication
        |
        v
service economic admission
   |                  |
 x402            entitlement
   |                  |
   +--------+---------+
            |
            v
hard resource budget
            |
            v
UCII authorization
            |
            v
bounded Strands/model/tool execution
            |
            v
protected executor + provenance
```

The economic admission layer MUST NOT replace UCII authorization.

## Required hard limits

Before UCII exposes a managed Guardian/Strands service to arbitrary external users, the service should enforce deterministic limits outside model discretion.

### Per request

At minimum, establish enforceable ceilings for applicable resources such as:

- maximum model invocations;
- maximum input/output token consumption;
- maximum tool calls;
- maximum web searches;
- maximum browser runtime;
- maximum code-interpreter runtime;
- maximum wall-clock execution time;
- maximum retries;
- maximum externally billable resource cost.

### Per identity

Where applicable:

- maximum requests per time window;
- maximum concurrent sessions;
- maximum service spend per time window;
- maximum aggregate model/tool consumption;
- suspension/deny state after quota exhaustion.

### System-wide

The operator must have independent limits such as:

- maximum aggregate daily spend;
- maximum aggregate monthly spend;
- concurrency ceilings;
- provider/service-specific ceilings;
- emergency circuit breaker.

These controls must fail closed.

## Non-escalation invariant

> **The agent may request additional resources. The agent may never authorize itself to receive additional resources.**

Neither prompt text, model output, tool output, browser content, payment attempt, nor repeated retries may raise an established resource ceiling.

Any quota increase or economic-policy change must come from an independently authorized control path.

## x402 and entitlement

The intended UCII product model remains:

### Third-party managed consumption

For applicable UCII-hosted paid operations:

```text
request
 -> authentication
 -> economic admission
 -> x402 where applicable
 -> authorization
 -> bounded execution
```

Pricing should be based on measured unit economics with sufficient safety margin rather than guessed before measurement.

### First-party UCII applications

UCII first-party services should not have to pay UCII itself merely to use UCII.

A valid protected service entitlement may waive the x402 payment requirement:

```text
request
 -> authentication
 -> protected service entitlement
 -> x402 waived
 -> authorization still required
 -> bounded execution
```

Critical invariant:

> **Entitlement waives payment only. It does not create identity, authority, broader scope, execution permission, or unlimited resource consumption.**

An entitled service still requires hard resource limits.

## Required measurement before setting managed-service price

Before choosing x402 pricing for a UCII-managed Guardian service, measure the actual deployed Guardian execution path.

The unit-economics study should identify:

- exact model/provider and model price;
- average and worst-case input tokens;
- average and worst-case output tokens;
- model calls per Guardian interaction;
- tool calls per interaction;
- searches per interaction;
- browser/code runtime where applicable;
- AgentCore/runtime consumption where applicable;
- storage/network/observability costs;
- UCII authoritative-operation costs;
- failure/retry amplification;
- concurrency behavior.

Then calculate measured/controlled cost for at least:

- 1 interaction;
- 100 interactions;
- 1,000 interactions;
- 100,000 interactions.

Also calculate the maximum cost an admitted request can create under the hard limits.

## Pricing acceptance rule

Do not publish a managed Guardian x402 price until all of the following are established:

1. actual service dependency inventory;
2. measured normal unit cost;
3. measured or deterministically bounded worst-case unit cost;
4. hard per-request resource ceiling;
5. hard per-identity quota/rate ceiling;
6. system-wide spend ceiling/circuit breaker;
7. x402 or protected entitlement admission;
8. proof that payment cannot create authority;
9. proof that entitlement cannot create authority;
10. proof that agent/model output cannot raise its own economic ceiling.

## Grok Bot applicability

A Grok Bot can be protected by Guardian where the integrator controls a consequential-action boundary that UCII can gate: for example an API, tool, MCP surface, service, executor, or application backend.

UCII does not claim to intercept arbitrary actions occurring entirely inside a third-party hosted environment when UCII does not control an enforcement point.

This distinction is important economically as well as cryptographically:

- **developer-hosted Grok Bot + developer-hosted execution:** developer pays their model/agent/tool bill;
- **UCII-managed Guardian execution:** UCII must meter and economically admit the request before paid resources can be consumed.

## Product principle

The same philosophy that protects delegated authority should protect infrastructure economics:

> **Capability is not authority.**

and:

> **Access to an agent is not authority to spend without limit.**

UCII should make catastrophic surprise infrastructure bills structurally impossible rather than merely unlikely.

## Next engineering step

**Do not implement pricing from this document alone.**

First perform a read-only dependency and invocation audit of the actual Guardian execution path. Identify every paid AWS/model/tool dependency Guardian currently invokes and the exact usage dimensions that can generate cost. From that evidence, calculate real Guardian unit economics and design the smallest enforceable cost-control boundary before exposing any UCII-funded managed service publicly.
