---
title: "Domain 5: Context & Reliability"
---

# Domain 5: Context Management & Reliability

## Weight: 15% of Exam

**Appears in Scenarios:** 1 (Customer Support), 3 (Multi-Agent Research), 6 (Structured Data Extraction)

---

## Task Statement 5.1: Manage Conversation Context

### Progressive Summarization Risks

When conversations get long, you might summarize earlier messages to save tokens. But summarization loses critical numerical details:

```
ORIGINAL CONTEXT:
  "Customer ordered 3 items totaling $247.50 on 2025-01-15.
   Requested $82.50 refund for 1 defective item (Widget Pro).
   Customer expects refund by 2025-02-01."

❌ LOSSY SUMMARY:
  "Customer had an order issue and wants a partial refund."
  → Lost: exact amounts, dates, item name, deadline

✅ PRESERVED FACTS (extracted to persistent block):
  Case Facts:
    order_total: $247.50
    order_date: 2025-01-15
    refund_requested: $82.50
    defective_item: Widget Pro
    customer_deadline: 2025-02-01
```

### The "Case Facts" Block Pattern

Extract transactional facts into a persistent block included in EVERY prompt:

```python
# Maintain a case_facts dict throughout the conversation
case_facts = {
    "customer_id": "C-12345",
    "customer_name": "Jane Smith",
    "issues": [
        {
            "order_id": "ORD-789",
            "amount": 247.50,
            "status": "delivered",
            "complaint": "defective Widget Pro",
            "refund_requested": 82.50,
            "deadline": "2025-02-01"
        }
    ]
}

# Include in EVERY API call
system_prompt = f"""
You are a customer support agent.

## Active Case Facts (DO NOT summarize or abbreviate these):
{json.dumps(case_facts, indent=2)}

## Conversation Summary:
{conversation_summary}
"""
```

### The "Lost in the Middle" Effect

Models reliably process information at the **beginning** and **end** of long inputs but may miss findings from **middle sections**.

```
┌──────────────────────────────────────────────┐
│ Long input document                          │
│                                              │
│ Beginning: ████████ ← Processed well         │
│ ...                                          │
│ Middle:    ░░░░░░░░ ← May be missed!         │
│ ...                                          │
│ End:       ████████ ← Processed well         │
└──────────────────────────────────────────────┘
```

**Mitigation strategies:**
1. Place key findings summaries at the BEGINNING
2. Organize with explicit section headers
3. Put critical data in structured blocks at the start or end

```python
# ✅ MITIGATE: Put summary at beginning, details with headers
prompt = f"""
## KEY FINDINGS SUMMARY (read this first):
{key_findings_summary}

## DETAILED RESULTS:

### Section A: Market Analysis
{section_a_details}

### Section B: Competitor Review  
{section_b_details}

### Section C: Financial Projections
{section_c_details}

## CONCLUSIONS:
{conclusions}
"""
```

### Trimming Verbose Tool Outputs

Tool results accumulate and consume tokens disproportionately:

```python
# ❌ FULL TOOL OUTPUT (40+ fields, only 5 relevant)
order_result = {
    "order_id": "ORD-789",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:00:00Z",
    "customer_id": "C-12345",
    "billing_address": {...},        # Not needed for return
    "shipping_address": {...},       # Not needed for return
    "payment_method": {...},         # Not needed for return
    "shipping_carrier": "UPS",       # Not needed for return
    "tracking_number": "1Z999...",   # Not needed for return
    "weight_kg": 2.5,               # Not needed for return
    "warehouse_id": "WH-03",        # Not needed for return
    # ... 30 more irrelevant fields
    "items": [...],                  # ← RELEVANT
    "total": 247.50,                 # ← RELEVANT
    "status": "delivered",           # ← RELEVANT
    "return_eligible": True,         # ← RELEVANT
    "return_window_end": "2025-02-15" # ← RELEVANT
}

# ✅ TRIMMED OUTPUT (only return-relevant fields)
def trim_order_for_return(order):
    return {
        "order_id": order["order_id"],
        "items": order["items"],
        "total": order["total"],
        "status": order["status"],
        "return_eligible": order["return_eligible"],
        "return_window_end": order["return_window_end"]
    }
```

### Subagent Output Design for Context Budgets

When downstream agents have limited context, upstream agents should return structured data instead of verbose content:

```python
# ❌ VERBOSE subagent output (wastes downstream context)
search_output = """
I searched for AI in healthcare and found many interesting results.
The first result was from Nature Medicine, which discussed how AI is 
being used in drug discovery. They found that... [2000 words of reasoning]
"""

# ✅ STRUCTURED subagent output (respects downstream context)
search_output = {
    "findings": [
        {
            "claim": "AI reduces drug discovery time by 40%",
            "source": "Nature Medicine",
            "url": "https://nature.com/...",
            "date": "2025-03",
            "relevance_score": 5
        }
    ],
    "total_sources_reviewed": 15,
    "coverage_gaps": ["Clinical trial phase data limited"]
}
```

---

## Task Statement 5.2: Escalation and Ambiguity Resolution

### Appropriate Escalation Triggers

| Trigger | Action | Why |
|---|---|---|
| Customer explicitly requests human agent | **Escalate immediately** | Honor customer preference — no investigation first |
| Policy exception/gap | **Escalate** | Agent can't make up policy |
| Unable to make meaningful progress | **Escalate** | Don't waste customer's time |
| Complex but within capability | **Attempt resolution** | Don't over-escalate |
| Frustrated customer, solvable issue | **Acknowledge + attempt** | Escalate only if they insist |

### Unreliable Escalation Signals

**Sentiment-based escalation — UNRELIABLE:**
```python
# ❌ WRONG — Sentiment doesn't correlate with case complexity
if customer_sentiment_score < -0.5:
    escalate()  # Angry customer might have simple issue (late delivery)
```

**Self-reported confidence — UNRELIABLE:**
```python
# ❌ WRONG — LLM confidence is poorly calibrated
if agent_confidence_score < 0.7:
    escalate()  # Agent might be incorrectly confident on hard cases
               # and incorrectly uncertain on easy cases
```

### Correct Escalation Examples

```python
# Scenario: Customer asks for human
system_prompt = """
If the customer explicitly asks to speak with a human agent:
  → Escalate IMMEDIATELY. Do not attempt to resolve first.
  → Include structured handoff summary.

Example:
  Customer: "I want to talk to a real person"
  → Call escalate_to_human immediately with handoff summary.
  → Do NOT say "Let me try to help you first."
"""

# Scenario: Policy gap
system_prompt = """
If the customer's request falls outside documented policy:
  → Escalate. Do not improvise policy.

Example:
  Customer: "Your competitor offers price matching. Can you match this price?"
  Policy only covers: own-site price adjustments
  → Escalate because policy doesn't address competitor price matching.
  → Do NOT make up a policy response.
"""

# Scenario: Frustrated but solvable
system_prompt = """
If the customer is frustrated but the issue is within your capability:
  → Acknowledge frustration
  → Offer to resolve
  → Escalate ONLY if customer reiterates preference for human

Example:
  Customer: "This is ridiculous. My order was supposed to arrive yesterday!"
  → "I understand your frustration with the late delivery. Let me check 
     the status of your order right away and see what I can do."
  → Only escalate if customer says "No, I want a person"
"""
```

### Multiple Customer Matches

When a tool returns multiple matches, ask for additional identifiers — don't select based on heuristics:

```python
# ❌ WRONG — Heuristic selection
if len(customers) > 1:
    # Pick the most recent one? Most active? Random?
    customer = customers[0]  # ❌ Might be wrong person

# ✅ CORRECT — Ask for clarification
if len(customers) > 1:
    return "I found multiple accounts matching that information. " \
           "Could you provide your account number or the email " \
           "address associated with your account to help me find " \
           "the right one?"
```

---

## Task Statement 5.3: Error Propagation in Multi-Agent Systems

### Structured Error Context for Recovery

```python
# ❌ GENERIC ERROR — Coordinator can't make informed decisions
search_agent_result = {"status": "error", "message": "Search unavailable"}

# ✅ STRUCTURED ERROR — Enables intelligent recovery
search_agent_result = {
    "status": "error",
    "failure_type": "timeout",
    "attempted_query": "AI drug discovery clinical trials 2024",
    "partial_results": [
        {"title": "AI in Pharma", "url": "...", "status": "retrieved"},
        {"title": "Clinical AI Review", "url": "...", "status": "timeout"}
    ],
    "alternative_approaches": [
        "Try more specific query: 'AI phase 3 clinical trials oncology'",
        "Use document analysis agent with pre-loaded research database"
    ],
    "retry_recommended": True,
    "max_retries_remaining": 2
}
```

### Two Anti-Patterns in Error Handling

**Anti-pattern 1: Silently suppressing errors (returning empty as success)**
```python
# ❌ The coordinator thinks the search succeeded with zero results
except Timeout:
    return {"results": [], "status": "success"}  # LYING about the outcome
```

**Anti-pattern 2: Terminating entire workflow on single failure**
```python
# ❌ One timeout shouldn't kill a 5-subagent pipeline
if any_subagent_failed:
    raise SystemError("Pipeline failed")  # Throws away partial results
```

### Coverage Annotations in Synthesis

When some sources failed, the synthesis should annotate what's well-supported vs what has gaps:

```json
{
  "report_sections": [
    {
      "topic": "AI in Drug Discovery",
      "coverage": "strong",
      "sources_count": 8,
      "confidence": "high",
      "content": "..."
    },
    {
      "topic": "AI in Clinical Trials",
      "coverage": "partial",
      "sources_count": 2,
      "confidence": "medium",
      "gap_note": "Web search timed out for 3 of 5 planned queries. "
                  "Findings based on limited sources.",
      "content": "..."
    }
  ]
}
```

---

## Task Statement 5.4: Large Codebase Exploration

### Context Degradation

In extended sessions, models start giving inconsistent answers and referencing "typical patterns" rather than specific classes discovered earlier. This happens because earlier tool results get pushed deep into the context window.

### Scratchpad Files

Have agents maintain persistent files recording key findings:

```python
# Agent writes findings to a scratchpad file
Write("scratchpad.md", """
# Auth Module Analysis

## Key Findings:
- AuthMiddleware in src/auth/middleware.ts handles JWT validation
- Token refresh logic in src/auth/refresh.ts
- 3 critical functions: validateToken(), refreshSession(), revokeAccess()

## Dependencies:
- Uses jsonwebtoken@9.0.0
- Redis for session storage
- Custom error types in src/errors/auth-errors.ts

## Issues Found:
- No rate limiting on token refresh endpoint
- Expired token check uses local time (timezone issues possible)
""")

# Later, when context degrades, reference the scratchpad
prompt = """
Based on the findings in scratchpad.md, trace the revokeAccess() flow.
Focus on: what happens to active sessions when a token is revoked?
"""
```

### Subagent Delegation for Exploration

Spawn subagents for specific investigation questions:

```python
# Main agent coordinates high-level understanding
# Subagents do the heavy investigation

subagent_1 = "Find all test files and categorize by type (unit/integration/e2e)"
subagent_2 = "Trace the refund flow from API endpoint to database write"
subagent_3 = "Identify all external service dependencies and their failure modes"

# Each subagent works in isolated context
# Returns concise findings to main agent
# Main agent's context stays clean
```

### Crash Recovery with State Manifests

```python
# Each agent exports state to a known location
manifest = {
    "agent_id": "search-agent-1",
    "status": "partial",
    "completed_queries": ["AI drug discovery", "AI diagnostics"],
    "pending_queries": ["AI clinical trials", "AI genomics"],
    "findings_file": "search-findings-1.json",
    "last_checkpoint": "2025-03-15T10:30:00Z"
}
Write(f"manifests/{manifest['agent_id']}.json", json.dumps(manifest))

# On resume, coordinator loads all manifests
manifests = load_all_manifests("manifests/")
for m in manifests:
    if m["status"] == "partial":
        resume_agent(m["agent_id"], m["pending_queries"])
```

### The /compact Command

Use `/compact` to reduce context usage during extended exploration:

```
Before /compact: 180K tokens used (95% of context)
  → Auto-triggers or manual invocation
  → Summarizes conversation, preserves key findings
After /compact: 45K tokens used (25% of context)
  → Fresh room for more exploration
```

---

## Task Statement 5.5: Human Review and Confidence Calibration

### The Aggregate Accuracy Trap

97% overall accuracy can mask poor performance on specific segments:

```
Overall accuracy: 97% ✓

By document type:
  Invoices: 99.5% ✓
  Receipts: 98.0% ✓
  Contracts: 85.0% ✗  ← Hidden problem!
  Handwritten notes: 72.0% ✗  ← Critical problem!

By field:
  Vendor name: 99.0% ✓
  Total amount: 97.0% ✓
  Tax ID: 78.0% ✗  ← Hidden problem!
  Line item descriptions: 82.0% ✗  ← Problem!
```

**Always validate by document type AND field** before automating high-confidence extractions.

### Stratified Random Sampling

Randomly sample high-confidence extractions to detect novel error patterns:

```python
# Don't just review low-confidence extractions
# Also randomly sample high-confidence ones

def sample_for_review(extractions, sample_rate=0.05):
    review_queue = []
    
    # Always review low-confidence
    for e in extractions:
        if e.confidence < 0.8:
            review_queue.append(e)
    
    # ALSO randomly sample high-confidence (stratified by document type)
    high_conf = [e for e in extractions if e.confidence >= 0.8]
    for doc_type in set(e.doc_type for e in high_conf):
        type_samples = [e for e in high_conf if e.doc_type == doc_type]
        sample_count = max(1, int(len(type_samples) * sample_rate))
        review_queue.extend(random.sample(type_samples, sample_count))
    
    return review_queue
```

### Field-Level Confidence Scores

Have the model output confidence per field, then calibrate with labeled validation sets:

```json
{
  "extraction": {
    "vendor_name": {"value": "Acme Corp", "confidence": 0.95},
    "total_amount": {"value": 1250.00, "confidence": 0.92},
    "tax_id": {"value": "12-3456789", "confidence": 0.65},
    "line_items": {"value": [...], "confidence": 0.78}
  },
  "routing": "human_review",
  "review_reason": "tax_id confidence below 0.80 threshold"
}
```

---

## Task Statement 5.6: Information Provenance

### Claim-Source Mappings

Require subagents to output structured mappings that downstream agents preserve:

```json
{
  "claim": "AI reduces drug discovery time by 40%",
  "sources": [
    {
      "url": "https://nature.com/articles/nm-2025-0123",
      "document_name": "Nature Medicine Vol 32, Issue 3",
      "relevant_excerpt": "Our analysis of 50 pharma companies showed...",
      "publication_date": "2025-03-15",
      "methodology": "Meta-analysis of 50 companies over 5 years"
    }
  ]
}
```

### Handling Conflicting Statistics

Don't arbitrarily select one value. Annotate conflicts with both sources:

```json
{
  "claim": "Global AI market size in 2025",
  "values": [
    {"value": "$190 billion", "source": "McKinsey Global Report", "date": "2025-01"},
    {"value": "$214 billion", "source": "Gartner Market Analysis", "date": "2025-03"}
  ],
  "conflict_note": "Discrepancy likely due to different market scope definitions. "
                    "McKinsey excludes embedded AI; Gartner includes it.",
  "resolution": "present_both"
}
```

### Temporal Data

Require publication dates to prevent temporal differences from being misinterpreted as contradictions:

```json
{
  "claim": "Company X revenue",
  "values": [
    {"value": "$5.2B", "source": "Annual Report", "data_date": "2024-12-31"},
    {"value": "$4.8B", "source": "Q3 Forecast", "data_date": "2024-09-30"}
  ],
  "temporal_note": "Not contradictory — Q3 forecast vs full-year actual."
}
```

### Rendering Different Content Types Appropriately

```
❌ UNIFORM FORMAT (everything as prose):
  "Revenue was $5.2B, up from $4.8B the previous year.
   The company operates in 12 countries including..."

✅ APPROPRIATE FORMATS:
  Financial data → Tables
  News/events → Prose
  Technical findings → Structured lists
  Comparisons → Side-by-side tables
```

---

## Practice Questions — Domain 5

### Question 1
Your customer support agent handles multi-issue sessions. After 10 turns of conversation, it starts giving vague responses like "as discussed earlier" instead of referencing specific amounts and dates. What's the best fix?

**A)** Increase the model's context window size.
**B)** Extract transactional facts into a persistent "case facts" block included in each prompt, outside summarized history.
**C)** Add "always be specific" to the system prompt.
**D)** Reduce the number of tools to use fewer tokens per turn.

**Correct Answer: B**
Extracting transactional facts (amounts, dates, order numbers) into a persistent block prevents progressive summarization from losing critical details. A doesn't address the summarization problem. C is vague. D doesn't address context management.

### Question 2
Your extraction system reports 97% overall accuracy. Your team wants to fully automate high-confidence extractions without human review. What should you verify first?

**A)** That the 97% accuracy holds when measured by document type and field segment, not just in aggregate.
**B)** That the model's self-reported confidence scores are above 0.95 for all extractions.
**C)** That a sample of 10 high-confidence extractions were all correct.
**D)** That the extraction prompt includes few-shot examples for all document types.

**Correct Answer: A**
Aggregate accuracy can mask poor performance on specific document types or fields. You must verify consistent performance across ALL segments before automating. B relies on uncalibrated confidence. C is too small a sample. D doesn't validate accuracy.

---

## Quick Reference — Domain 5 Cheat Sheet

| Concept | Key Fact |
|---|---|
| **Progressive summarization** | Loses numerical values, dates, percentages |
| **Case facts block** | Persistent structured data outside summarized history |
| **Lost in the middle** | Models process start and end better than middle |
| **Mitigation** | Key findings at beginning, section headers, structured blocks |
| **Verbose tool outputs** | Trim to only relevant fields before entering context |
| **Subagent output** | Return structured data, not verbose reasoning chains |
| **Escalation triggers** | Customer requests human, policy gaps, inability to progress |
| **Customer says "give me a human"** | Escalate IMMEDIATELY, no investigation first |
| **Sentiment-based escalation** | UNRELIABLE — doesn't correlate with complexity |
| **Self-reported confidence** | UNRELIABLE — poorly calibrated |
| **Multiple customer matches** | Ask for additional identifiers, don't use heuristics |
| **Generic error messages** | Anti-pattern — hide context from coordinator |
| **Suppressing errors as success** | Anti-pattern — prevents recovery |
| **Terminating on single failure** | Anti-pattern — wastes partial results |
| **Context degradation** | Extended sessions → inconsistent answers |
| **Scratchpad files** | Persist key findings across context boundaries |
| **/compact** | Reduce context usage during extended exploration |
| **Crash recovery** | Structured state manifests loaded on resume |
| **97% aggregate accuracy** | May mask poor performance on specific doc types |
| **Stratified sampling** | Sample high-confidence extractions by document type |
| **Field-level confidence** | Calibrate with labeled validation sets |
| **Source attribution** | Claim-source mappings preserved through synthesis |
| **Conflicting statistics** | Annotate both values with sources, don't pick one |
| **Temporal data** | Include publication dates to avoid false contradictions |
