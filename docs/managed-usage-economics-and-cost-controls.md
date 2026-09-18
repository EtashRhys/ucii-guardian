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

## Empirical Guardian cost measurement — September 2026

Status: **MEASURED FROM LOCAL GUARDIAN PROVENANCE + AWS COST EXPLORER**

Measurement date: 2026-09-18.

This section records the first empirical unit-economics study of the actual Guardian hackathon development/demo runtime. It replaces estimates with observed evidence while preserving attribution limits.

### Request-to-model invocation contract

The current runtime establishes this ordering in `run_guardian_request()`:

```text
propose_action(agent, request)
 -> Strands agent(request, structured_output_model=ActionRequest)
 -> structured ActionRequest returned
 -> recorder.record_request(action)
 -> UCII identity verification
 -> UCII authority check
 -> DENY / escalation / ALLOW
 -> protected execution where applicable
```

`propose_action()` contains exactly one explicit Strands `agent(...)` invocation. `REQUEST_RECEIVED` is recorded only after that invocation successfully returns a structured `ActionRequest`. The escalation-continuation path explicitly does not invoke Strands.

Therefore each recorded `REQUEST_RECEIVED` in this measured runtime establishes one successful initial Strands model invocation. A model invocation that fails before producing an `ActionRequest` would not produce `REQUEST_RECEIVED`, so the provenance ledger is not by itself a count of failed/pre-record model attempts.

### Guardian provenance evidence

Two local Guardian provenance ledgers were inspected read-only:

- `guardian-web.jsonl`: 213 valid JSON records, 39 `REQUEST_RECEIVED` events, activity from 2026-09-10 through 2026-09-14 UTC.
- `milestone7-20260910T213023Z.jsonl`: 12 valid JSON records, 2 `REQUEST_RECEIVED` events.

Across both ledgers there were **41 `REQUEST_RECEIVED` events and 41 unique request IDs, with zero duplicate request IDs**.

Observed unique Guardian requests by UTC date:

| UTC date | Unique requests |
| --- | ---: |
| 2026-09-10 | 13 |
| 2026-09-12 | 6 |
| 2026-09-13 | 15 |
| 2026-09-14 | 7 |
| **Total** | **41** |

The main ledger also recorded the expected independent security/execution facts, including identity verification, authority checks, authorization, execution starts/completions/refusals, revocation, escalation, and human decisions. These event classes must not be treated as additional model calls.

### AWS Cost Explorer evidence

AWS Cost Explorer was queried read-only for 2026-09-01 through 2026-09-18 inclusive, grouped by usage type with `UnblendedCost` and `UsageQuantity`.

The account-level model usage for that interval was:

- input: **73,263 tokens**;
- output: **9,613 tokens**;
- total: **82,876 tokens**;
- model inference cost: **$0.41398400**;
- complete AWS cost in the same query: **$0.41445481**.

The Cost Explorer total reconciled to the exported billing CSV total of **$0.41445500** with a difference of only **-$0.00000019**.

Daily model usage was:

| UTC date | Input tokens | Output tokens | Total tokens | Model cost |
| --- | ---: | ---: | ---: | ---: |
| 2026-09-09 | 1,008 | 190 | 1,198 | $0.055874 |
| 2026-09-10 | 27,012 | 3,830 | 30,842 | $0.138486 |
| 2026-09-12 | 12,297 | 1,392 | 13,689 | $0.057771 |
| 2026-09-13 | 19,362 | 2,701 | 22,063 | $0.098601 |
| 2026-09-14 | 13,584 | 1,500 | 15,084 | $0.063252 |

No Guardian `REQUEST_RECEIVED` evidence was present for 2026-09-09, so that day's 1,198 tokens and $0.055874 are **excluded from Guardian-attributed unit economics** rather than guessed to belong to Guardian.

### Correlated Guardian-active window

On the four dates containing recorded Guardian requests, AWS measured:

- **72,255 input tokens**;
- **9,423 output tokens**;
- **81,678 total tokens**;
- **$0.358110 model inference cost**;
- **41 unique recorded Guardian requests**.

Those Guardian-active dates contain approximately **98.55% of all model tokens** measured in the September 1–18 account-level window.

The observed aggregate operational averages over the correlated window are therefore:

- **1,762.32 input tokens per recorded Guardian request**;
- **229.83 output tokens per recorded Guardian request**;
- **1,992.15 total tokens per recorded Guardian request**;
- **$0.00873439 model inference cost per recorded Guardian request**.

That is approximately **0.87 US cents of model inference per recorded Guardian request** in this development/demo workload.

Daily observed cost per recorded request:

| UTC date | Requests | Model cost | Observed cost/request |
| --- | ---: | ---: | ---: |
| 2026-09-10 | 13 | $0.138486 | $0.010653 |
| 2026-09-12 | 6 | $0.057771 | $0.009629 |
| 2026-09-13 | 15 | $0.098601 | $0.006573 |
| 2026-09-14 | 7 | $0.063252 | $0.009036 |

### Attribution boundary

This is strong temporal and architectural correlation, not provider-side per-request cryptographic attribution.

The measured statement is:

> **During the four dates with 41 recorded Guardian requests, the AWS account incurred $0.358110 of model inference for 81,678 tokens, an observed average of approximately $0.00873 per recorded Guardian request.**

Do not silently strengthen that statement to claim that AWS proved every one of those tokens was generated by Guardian. The account-level Cost Explorer data does not carry Guardian request IDs.

The code/provenance relationship does establish that each recorded `REQUEST_RECEIVED` followed one successful initial Strands model invocation. It does not count model attempts that fail before a structured `ActionRequest` is returned.

### Scaling illustrations — not forecasts

Holding the measured $0.00873439/request average constant only for illustration:

| Comparable requests | Straight-line model-cost illustration |
| --- | ---: |
| 100 | ~$0.87 |
| 1,000 | ~$8.73 |
| 10,000 | ~$87.34 |
| 100,000 | ~$873.44 |
| 1,000,000 | ~$8,734.39 |

These are **not production forecasts or prices**. Production prompt size, selected model, provider pricing, retries, failures, concurrency, model behavior, and future functionality can materially change unit cost.

### Current cost-risk conclusion

The measured hackathon runtime does not show a large hidden Strands/AgentCore infrastructure bill. Repository inspection shows Guardian constructs Strands with `tools=[]`; Strands normalizes the human request into an `ActionRequest`, while UCII identity/authority evaluation and the protected executor remain outside model authority.

For the measured September workload, model inference dominated AWS spend. This does not remove the need for hard resource ceilings before any UCII-funded public managed service. It does establish a concrete baseline from which those controls and future pricing can be designed.

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

The initial dependency/invocation audit and September 2026 empirical baseline are now complete.

**Do not publish managed-service pricing from the average alone.** Before exposing any UCII-funded Guardian service publicly, establish the smallest deterministic cost-control boundary: per-request model/token ceilings, per-identity quotas, system-wide spend/circuit-breaker limits, and measured worst-case/failure-path cost. Then remeasure under a production-representative workload and set economic admission/x402 policy from bounded cost rather than from the hackathon average.
