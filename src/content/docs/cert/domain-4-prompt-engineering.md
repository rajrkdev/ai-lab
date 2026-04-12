---
title: "Domain 4: Prompt Engineering & Structured Output"
description: "20% of the exam. Covers explicit criteria, few-shot prompting, tool_use schemas, validation-retry loops, batch processing, and multi-instance review."
sidebar:
  order: 4
---

# Domain 4: Prompt Engineering & Structured Output

## Weight: 20% (~12 questions)

**Appears in Scenarios:** 5 (CI/CD), 6 (Structured Data Extraction)

---

## What This Domain Tests

- Write explicit, measurable criteria instead of vague instructions
- Use few-shot examples effectively for consistency and generalization
- Force structured output via `tool_use` with JSON schemas
- Design schemas with nullable fields to prevent hallucination
- Implement validation-retry loops with specific error feedback
- Choose when to use the Message Batches API vs synchronous API
- Design multi-instance review to avoid self-review bias

---

## Task Statement 4.1: Explicit Criteria Over Vague Instructions

### Why Vague Instructions Fail

```
❌ VAGUE — Claude interprets inconsistently across runs:
  system_prompt = "Review this code and check that comments are accurate."
  
  Run 1: Flags 12 comments
  Run 2: Flags 2 comments
  Run 3: Flags 0 comments
  → Same prompt, wildly different behavior

❌ STILL VAGUE — "Be conservative" doesn't help:
  system_prompt = "Review code. Be conservative. Only report high-confidence findings."
  
  Problem: "Conservative" and "high-confidence" have no measurable meaning
  → Still inconsistent behavior

✅ EXPLICIT CRITERIA — Consistent behavior every run:
  system_prompt = """Review this code. Flag comments ONLY when ALL of these are true:
  1. The comment explicitly claims the function does X
  2. The code provably does Y (not X)
  3. The discrepancy would cause a developer to misuse the function
  
  Do NOT flag:
  - Style differences in comment phrasing
  - Comments that are technically correct but incomplete
  - TODO/FIXME comments (intentional markers)
  - Minor unit differences when values match (5 mins = 300 secs)
  """
```

### Explicit Severity Criteria with Examples

Attach concrete code examples to each severity level to eliminate interpretation:

```python
system_prompt = """
Classify each finding by severity:

CRITICAL (blocks merge — reject the PR):
  Definition: Active security vulnerability or data corruption risk
  Examples:
    • db.query(f"SELECT * FROM users WHERE id = {user_input}")
      ← SQL injection: user input directly in query string
    • os.path.join("/uploads", request.filename)
      ← Directory traversal: no path sanitization
    • api_key = "sk-prod-..." in source code
      ← Exposed credential in version-controlled file

WARNING (should fix before merge — flag for author):
  Definition: Reliability or correctness issue that will cause bugs
  Examples:
    • Missing if (!userId) return 400 before database lookup
      ← Unvalidated input to database
    • while True: process_item()
      ← Unbounded loop with no exit condition or timeout
    • catch (e) { console.log(e) }
      ← Swallowed exception: error logged but execution continues

INFO (nice to have — optional):
  Definition: Style or readability improvement
  Examples:
    • const x = calculateTotal(items)  →  rename x to orderTotal
    • Missing JSDoc on internal helper function
    • Function could be simplified to one line
"""
```

### The False Positive Problem

High false positive rates in one category destroy trust in ALL categories:

```
SCENARIO: Code review agent flags comments for accuracy
  → 60% of "inaccurate comment" findings are wrong
  → Developers dismiss ALL findings (including valid security findings)
  → The agent is now worse than useless

DIAGNOSIS: "Inaccurate comment" criteria are too broad
  → Agent flags correct comments that "could be more detailed"

FIX:
  Step 1: DISABLE the high-false-positive category entirely
          → Restore developer trust in remaining categories
          
  Step 2: Improve that category's criteria separately
          → Add concrete examples of true positives vs. false positives
          → Test against labeled dataset
          
  Step 3: Re-enable with improved criteria
          → Monitor false positive rate before full deployment

⚠️  Temporarily disabling a category is better than
    destroying trust in everything else.
```

---

## Task Statement 4.2: Few-Shot Prompting

### When to Use Few-Shot Examples

```
USE FEW-SHOT WHEN:
  ✓ Detailed instructions alone produce inconsistent results
  ✓ Ambiguous cases need demonstrated judgment
  ✓ You need consistent output format
  ✓ You want the model to generalize to novel patterns

DO NOT USE FEW-SHOT WHEN:
  ✗ Instructions alone are already producing correct, consistent results
  ✗ You only want to match pre-specified cases (few-shot generalizes beyond)
  ✗ Adding examples would exceed context budget significantly
```

### How to Structure Few-Shot Examples

Include: **input → expected output → reasoning** for each example. The reasoning helps Claude generalize.

```python
system_prompt = """
You are a code review agent. Analyze code changes and report issues.

## Examples of correct analysis:

### EXAMPLE 1: True Positive (DO report this)
Code:
  user_age = int(request.params["age"])

Finding:
  {
    "file": "api/users.py",
    "line": 15,
    "severity": "warning",
    "issue": "Uncaught ValueError if 'age' parameter is not numeric",
    "detected_pattern": "unvalidated_type_cast",
    "suggestion": "Use try/except or validate input: int(x) if x.isdigit() else abort(400)"
  }

Reasoning: User input goes directly to int() without validation. A non-numeric
value (like "abc") will crash the server with an unhandled 500 error.

---

### EXAMPLE 2: True Negative — Do NOT report this
Code:
  # Process items in reverse order
  for item in reversed(items):
      process(item)

Analysis: The comment says "reverse order" and the code uses reversed().
Comment accurately describes code behavior. This is NOT an issue.
Do not flag comments that correctly describe what the code does.

---

### EXAMPLE 3: Ambiguous Case — How to decide
Code:
  # Cache results for 5 minutes
  @cache(ttl=300)
  def get_user(id):
      return db.find(id)

Analysis: Comment says "5 minutes". TTL is 300 seconds = 5 minutes exactly.
This is CORRECT. Do not flag unit conversions when the values match.
Only flag when the values are actually different.

---

### EXAMPLE 4: Subtle True Positive
Code:
  # Returns the user's full name
  def get_email(user_id):
      return db.get_email(user_id)

Finding:
  {
    "file": "utils.py",
    "line": 8,
    "severity": "warning",
    "issue": "Comment says 'Returns full name' but function returns email",
    "detected_pattern": "misleading_comment",
    "suggestion": "Change comment to: 'Returns the user's email address'"
  }

Reasoning: The comment explicitly claims the function returns a name.
The code returns an email. This WILL cause developer misuse.
"""
```

### Few-Shot for Extraction — Handling Missing Data

Show how to handle missing or ambiguous information without fabricating:

```python
system_prompt = """
Extract property details from real estate listings.
If information is not present, use null — NEVER fabricate or infer.

### EXAMPLE 1: Standard format
Input: "Beautiful 3BR/2BA home, 1,850 sq ft, built 2005. Listed at $450,000."
Output: {
  "bedrooms": 3, "bathrooms": 2, "sqft": 1850,
  "year_built": 2005, "price": 450000
}

### EXAMPLE 2: Informal format
Input: "Charming cottage with three beds and a bath and a half. About eighteen
       hundred square feet. Asking mid-fours."
Output: {
  "bedrooms": 3,
  "bathrooms": 1.5,
  "sqft": 1800,
  "year_built": null,    ← Not mentioned: use null, never estimate
  "price": null          ← "mid-fours" is too vague to extract reliably
}

### EXAMPLE 3: Missing fields
Input: "Renovated studio apartment downtown. $1,200/month rent."
Output: {
  "bedrooms": 0,         ← Studio means 0 bedrooms
  "bathrooms": null,     ← Not mentioned
  "sqft": null,          ← Not mentioned
  "year_built": null,    ← Not mentioned
  "price": null          ← This is rent, not sale price — different field
}
"""
```

> **Key principle:** Few-shot examples teach **generalization** — the model applies demonstrated judgment to NEW patterns it hasn't seen, not just the examples shown.

---

## Task Statement 4.3: Structured Output via tool_use

### Why tool_use Is the Most Reliable Approach

```
APPROACH 1: Ask for JSON in text (unreliable)
  ❌ Claude might include markdown formatting around the JSON
  ❌ Claude might add explanatory text before/after
  ❌ Claude might produce syntax errors (unclosed brackets, trailing commas)
  ❌ No schema enforcement — Claude invents its own structure

APPROACH 2: tool_use with JSON schema (reliable)
  ✅ Output is always valid JSON (no syntax errors)
  ✅ Schema is enforced by the API (correct field names and types)
  ✅ No markdown formatting contamination
  ✅ Straightforward to parse programmatically
```

### Complete tool_use Extraction Pattern

```python
import anthropic
import json

client = anthropic.Anthropic()

# Define extraction schema as a tool
extraction_tool = {
    "name": "extract_invoice",
    "description": "Extract all structured data from an invoice document. "
                   "Use null for any field not present in the document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor_name": {
                "type": "string",
                "description": "Name of the company issuing the invoice"
            },
            "invoice_number": {
                "type": ["string", "null"],
                "description": "Invoice identifier. null if not present."
            },
            "invoice_date": {
                "type": ["string", "null"],
                "description": "Invoice date in YYYY-MM-DD format. null if not found."
            },
            "total_amount": {
                "type": "number",
                "description": "Total invoice amount as a number (no currency symbol)"
            },
            "currency": {
                "type": "string",
                "enum": ["USD", "EUR", "GBP", "CAD", "AUD", "other"],
                "description": "Currency code. Use 'other' if currency not listed."
            },
            "currency_detail": {
                "type": ["string", "null"],
                "description": "If currency is 'other', specify the currency name. Else null."
            },
            "payment_status": {
                "type": "string",
                "enum": ["paid", "unpaid", "partial", "unclear"],
                "description": "Use 'unclear' for contradictory or ambiguous payment info."
            },
            "line_items": {
                "type": ["array", "null"],
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity":    {"type": ["number", "null"]},
                        "unit_price":  {"type": ["number", "null"]},
                        "total":       {"type": "number"}
                    },
                    "required": ["description", "total"]
                }
            }
        },
        "required": ["vendor_name", "total_amount", "currency", "payment_status"]
    }
}

def extract_invoice_data(invoice_text: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[extraction_tool],
        tool_choice={"type": "tool", "name": "extract_invoice"},  # Force this tool
        messages=[{"role": "user", "content": f"Extract data from this invoice:\n\n{invoice_text}"}]
    )

    # Extract the structured data from the tool_use response
    for block in response.content:
        if block.type == "tool_use":
            return block.input   # Guaranteed valid JSON matching schema
    
    raise ValueError("No tool_use block in response")
```

### Schema Design Patterns

#### Pattern 1: Nullable Fields Prevent Fabrication

```json
{
  "type": "object",
  "properties": {
    "vendor_name":   {"type": "string"},
    "tax_id":        {"type": ["string", "null"]},  ← May not exist in document
    "discount":      {"type": ["number", "null"]},  ← Not all invoices have discounts
    "purchase_order":{"type": ["string", "null"]}   ← Optional reference number
  },
  "required": ["vendor_name"]
}

WHY: Without null types, Claude fabricates plausible-sounding values for missing fields.
     With null types, Claude returns null (correct) instead of inventing data.
```

#### Pattern 2: Enum + "other" + Detail String

```json
{
  "document_type": {
    "type": "string",
    "enum": ["invoice", "receipt", "purchase_order", "contract", "other"]
  },
  "document_type_detail": {
    "type": ["string", "null"],
    "description": "If document_type is 'other', describe the actual type. Else null."
  }
}

WHY: Closed enums are reliable for known types.
     "other" + detail handles edge cases without schema breakage.
```

#### Pattern 3: "unclear" Enum for Ambiguous Cases

```json
{
  "payment_status": {
    "type": "string",
    "enum": ["paid", "unpaid", "partial", "unclear"],
    "description": "Use 'unclear' when document contains conflicting or ambiguous payment info"
  }
}

WHY: Without "unclear", Claude is forced to pick a definitive answer
     even when the document genuinely can't support one.
     "unclear" is an honest, actionable result that triggers human review.
```

### Syntax Errors vs. Semantic Errors

```
SYNTAX ERRORS ← tool_use ELIMINATES THESE:
  ✗ {"total": 99.99   ← missing closing brace
  ✗ "vendor": "Acme",, ← double comma
  ✗ {vendor: "Acme"}  ← unquoted key

SEMANTIC ERRORS ← tool_use CANNOT CATCH THESE:
  ✓ JSON is valid, but values are wrong:
  {
    "line_items": [
      {"description": "Widget A", "quantity": 2, "unit_price": 10, "total": 20},
      {"description": "Widget B", "quantity": 3, "unit_price": 15, "total": 45}
    ],
    "total_amount": 100   ← WRONG! Should be 65 (20+45) but schema can't detect this
  }

FIX FOR SEMANTIC ERRORS: Extract both stated and calculated values:
  {
    "stated_total": 100.00,       ← What the document says
    "calculated_total": 65.00,    ← Sum of line items
    "conflict_detected": true,    ← Flag the discrepancy
    "conflict_note": "Stated total ($100) differs from sum of line items ($65)"
  }
```

---

## Task Statement 4.4: Validation, Retry, and Feedback Loops

### Validation-Retry Flow

```
FIRST ATTEMPT:
  ┌─────────────────────────────────────────────┐
  │ Extract data from document                  │
  │ Run validation rules against extraction     │
  └──────────────────┬──────────────────────────┘
                     │
           Validation passed?
                     │
               YES   │   NO
                     │
                     ▼   ▼
               Done!    ┌─────────────────────────────────────────┐
                        │ RETRY WITH SPECIFIC ERROR FEEDBACK       │
                        │                                          │
                        │ Send to Claude:                          │
                        │  1. ORIGINAL DOCUMENT (unchanged)        │
                        │  2. FAILED EXTRACTION (what went wrong)  │
                        │  3. SPECIFIC ERRORS (exactly what failed)│
                        │                                          │
                        │ "Re-extract, fixing these specific errors│
                        │  Do NOT change correct fields."          │
                        └──────────────────┬───────────────────────┘
                                           │
                                 Retry validation
                                           │
                             Pass? → Done!  Fail? → Human review
```

```python
def extract_with_retry(document_text: str, max_retries: int = 2) -> dict:
    extraction = extract_from_document(document_text)
    
    for attempt in range(max_retries):
        errors = validate_extraction(extraction)
        
        if not errors:
            return extraction   # Validation passed
        
        # Retry with full context — original + failed attempt + specific errors
        retry_prompt = f"""
The following extraction had validation errors. Please re-extract.

ORIGINAL DOCUMENT:
{document_text}

YOUR PREVIOUS EXTRACTION (with errors):
{json.dumps(extraction, indent=2)}

SPECIFIC VALIDATION ERRORS:
{json.dumps(errors, indent=2)}

Instructions:
- Fix ONLY the fields listed in the errors
- Do NOT change fields that were correct
- If a required field truly isn't in the document, use null
"""
        extraction = extract_from_document(retry_prompt)
    
    # Max retries exceeded — route to human review
    return {"extraction": extraction, "needs_review": True, "errors": errors}
```

### When Retries Help vs. When They Don't

```
RETRIES HELP (format/structure errors):
  ✅ "Expected date in YYYY-MM-DD format, received 'January 5, 2025'"
     → Claude can convert the format on retry

  ✅ "invoice_number should be string, received integer 12345"
     → Claude can convert the type on retry

  ✅ "Subtotals don't sum to stated total"
     → Claude can recalculate and correct on retry

RETRIES DON'T HELP (information absent from source):
  ❌ "Required field 'tax_id' is null"
     If the document doesn't contain a tax ID, retrying won't create one.
     FIX: Make tax_id nullable in the schema.

  ❌ "Required field 'invoice_number' missing"
     If the invoice genuinely has no number, no retry will find one.
     FIX: Make invoice_number optional or handle the null case downstream.
```

### Feedback Loops with detected_pattern

Add `detected_pattern` to findings to enable systematic false positive analysis:

```json
{
  "file": "auth.py",
  "line": 42,
  "severity": "warning",
  "issue": "Potential SQL injection via string concatenation",
  "detected_pattern": "string_concatenation_in_sql",
  "suggestion": "Use parameterized queries: db.query('SELECT * FROM users WHERE id = %s', [user_id])"
}
```

Track which patterns get dismissed most frequently → improve prompts for those patterns specifically.

---

## Task Statement 4.5: Message Batches API

### Key Facts — Memorize These

| Fact | Value |
|---|---|
| **Cost savings** | 50% of standard API pricing |
| **Processing window** | Up to 24 hours maximum |
| **Latency SLA** | None guaranteed (no commitment on timing) |
| **Typical completion** | Usually under 1 hour |
| **Max requests per batch** | 100,000 |
| **Result availability** | 29 days after completion |
| **Multi-turn tool calling** | NOT supported within a single batch request |
| **Request correlation** | `custom_id` field you provide on each request |

### Appropriate vs. Inappropriate Workloads

```
✅ USE BATCH API (latency-tolerant, non-blocking):
  • Overnight technical debt analysis reports
  • Weekly security audit of entire codebase
  • Nightly test generation for modified files
  • Batch document extraction (100+ documents)
  • End-of-day summarization of activity logs

❌ DO NOT USE BATCH API (blocking, latency-sensitive):
  • Pre-merge code review checks (developers are waiting)
  • Real-time customer support responses
  • Interactive code generation during development
  • Any workflow where someone is blocked waiting for the result
```

### Batch Submission with custom_id Correlation

```python
import anthropic
import time

client = anthropic.Anthropic()

# Build requests — each with YOUR unique custom_id
requests = []
for document in documents:
    requests.append({
        "custom_id": f"doc-{document.id}",   # YOUR identifier for correlation
        "params": {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "tools": [extraction_tool],
            "tool_choice": {"type": "tool", "name": "extract_data"},
            "messages": [{"role": "user", "content": document.text}]
        }
    })

# Submit the batch
batch = client.messages.batches.create(requests=requests)
print(f"Batch submitted: {batch.id}")

# Poll for completion (check every 60 seconds)
while True:
    status = client.messages.batches.retrieve(batch.id)
    if status.processing_status == "ended":
        break
    print(f"Still processing... ({status.request_counts})")
    time.sleep(60)

# Process results — correlate back using custom_id
results = client.messages.batches.results(batch.id)
failed_docs = []

for result in results:
    doc_id = result.custom_id            # Correlates to your document.id

    if result.result.type == "succeeded":
        message = result.result.message
        # Extract tool_use data from message
        for block in message.content:
            if block.type == "tool_use":
                save_extraction(doc_id, block.input)

    elif result.result.type == "errored":
        print(f"Error for {doc_id}: {result.result.error}")
        failed_docs.append(doc_id)       # Track for resubmission

    elif result.result.type == "expired":
        print(f"Expired (>24hr) for {doc_id}")
        failed_docs.append(doc_id)
```

### Batch Flow Diagram

```
YOUR DOCUMENTS (10,000 docs)
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 1: Test on sample (validate prompt quality first)    │
│  • Process 10–20 documents synchronously                   │
│  • Evaluate accuracy against known-good results            │
│  • Refine prompt until accuracy is acceptable              │
│  • ONLY THEN submit the full batch                         │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 2: Submit batch                                      │
│  client.messages.batches.create(requests=[...])            │
│  → Returns batch.id immediately                            │
│  → Processing begins in background                         │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               │ (up to 24 hours)
                               ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 3: Poll for completion                               │
│  client.messages.batches.retrieve(batch.id)                │
│  → processing_status: "in_progress" | "ended"             │
└──────────────────────────────┬─────────────────────────────┘
                               │ status == "ended"
                               ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 4: Retrieve and correlate results                    │
│  client.messages.batches.results(batch.id)                 │
│  → For each result: match custom_id to original document   │
│  → Handle: succeeded | errored | expired                   │
└──────────────────────────────┬─────────────────────────────┘
                               │ failed_docs list
                               ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 5: Resubmit failures only                            │
│  → Identify root cause (token limit? → chunk document)    │
│  → Resubmit only failed custom_ids                         │
└────────────────────────────────────────────────────────────┘
```

---

## Task Statement 4.6: Multi-Instance and Multi-Pass Review

### Why Self-Review Is Biased

```
SAME SESSION (biased):
  Claude generates: "Build auth middleware using JWT with 24hr expiry"
  
  Internal state after generation:
  ┌──────────────────────────────────────────────────────────┐
  │ Claude remembers WHY it chose JWT                        │
  │ Claude remembers WHY it chose 24hr expiry                │
  │ Claude has reasoning context that justified each decision│
  └──────────────────────────────────────────────────────────┘
  
  Same session reviews: "Any issues with this auth middleware?"
  → Less likely to question decisions it already justified
  → Confirmation bias built into the review

INDEPENDENT INSTANCE (unbiased):
  Fresh Claude session receives only: the code to review
  ┌──────────────────────────────────────────────────────────┐
  │ No prior reasoning about why JWT was chosen              │
  │ No knowledge of the original constraints                 │
  │ Examines code purely on its own merits                   │
  └──────────────────────────────────────────────────────────┘
  → Catches issues the original reasoning "explained away"
```

### Multi-Pass Review for Large PRs

```
14-FILE PR REVIEW STRATEGY:

PASS 1 — Parallel Per-File Analysis:
┌──────────────────────────────────────────────────────────┐
│ Spawn 14 parallel review instances (one per file)        │
│                                                          │
│ Instance 1: "Review auth.ts for bugs, type errors,       │
│              unhandled exceptions. Be specific."          │
│ Instance 2: "Review users.ts for bugs, type errors..."   │
│ Instance 3: "Review db.ts for bugs, type errors..."      │
│ ...                                                      │
│                                                          │
│ Each instance focuses on ONE file only                   │
│ All run in parallel → fast, consistent depth             │
└──────────────────────────────┬───────────────────────────┘
                               │
                               │ Collect per-file summaries
                               ▼
PASS 2 — Cross-File Integration:
┌──────────────────────────────────────────────────────────┐
│ Coordinator receives ALL per-file summaries              │
│                                                          │
│ Prompt: "Given these per-file findings:                  │
│  auth.ts exports: verifyToken(token): User | null        │
│  users.ts imports verifyToken and passes JWT directly    │
│  db.ts: User type requires non-null id field             │
│                                                          │
│ Check cross-file integration:                            │
│  - Does null User from verifyToken crash in users.ts?    │
│  - Are error types from errors.ts handled in api.ts?     │
│  - Do db.ts queries match models.ts schema?"             │
│                                                          │
│ Catches bugs per-file review CANNOT see                  │
└──────────────────────────────────────────────────────────┘
```

### Confidence-Based Routing

```json
{
  "finding": "Potential null pointer dereference on line 42",
  "confidence": 0.91,
  "routing": "auto-flag",
  "auto_action": "add_pr_comment"
}

{
  "finding": "Logic might cause race condition under high load",
  "confidence": 0.43,
  "routing": "human_review",
  "reason": "Confidence below 0.80 threshold — needs human judgment"
}
```

---

## Practice Questions — Domain 4

### Question 1
Your code review agent flags code comments with 60% false positive rate on the "accuracy" check. Developers are now ignoring ALL findings, including valid security alerts. What's the correct immediate fix?

**A)** Increase the model's temperature for more conservative responses  
**B)** Temporarily disable the high-false-positive "comment accuracy" category, restore developer trust in remaining categories, then improve the disabled category separately  
**C)** Add "be conservative, only report high-confidence findings" to the system prompt  
**D)** Require consensus from three review passes before flagging any finding  

**Correct Answer: B**  
Disabling the category is the right immediate fix — it restores trust in still-valid categories. A doesn't address precision. C is vague instruction ("conservative" has no measurable meaning and historically doesn't help). D suppresses intermittent but real findings without fixing false positives.

---

### Question 2
During invoice extraction, you consistently get `"tax_id": null` but your validation requires tax_id to be non-null. Retrying with error feedback doesn't fix it. Why?

**A)** The retry prompt doesn't include the original document  
**B)** The model needs more few-shot examples of invoices with tax IDs  
**C)** The invoices genuinely don't contain tax IDs — retries cannot create information that isn't in the source  
**D)** The JSON schema isn't enforcing the non-null constraint correctly  

**Correct Answer: C**  
Retries fix format and structural errors, not absent information. If the document doesn't contain a tax ID, no amount of retrying will find one. The correct fix is to make `tax_id` nullable in the schema. All other options assume the information exists somewhere.

---

### Question 3
You're processing 10,000 insurance documents overnight. Each document is independent. Which approach is correct?

**A)** Submit all 10,000 in one Message Batches API call with `custom_id` per document  
**B)** Submit all 10,000 synchronously in parallel API calls  
**C)** Use multi-turn tool calling to process documents in dependency order  
**D)** Batch in groups of 100 using the synchronous API with rate limiting  

**Correct Answer: A**  
Message Batches API is designed for exactly this: latency-tolerant, independent, high-volume processing with 50% cost savings. B would hit rate limits and cost full price. C is wrong — Batch API doesn't support multi-turn tool calling (and documents are independent anyway). D is inefficient and expensive.

---

## Quick Reference — Domain 4 Cheat Sheet

| Concept | Key Fact |
|---|---|
| **Explicit criteria** | "Flag only when X contradicts Y" beats "check accuracy" |
| **"Be conservative"** | Vague — does NOT improve precision |
| **False positives** | Disable high-FP category to restore trust, improve separately |
| **Few-shot: when to use** | Inconsistent results, ambiguous cases, output format consistency |
| **Few-shot: count** | 2–4 targeted examples for ambiguous scenarios |
| **Few-shot: key benefit** | Generalization to novel patterns, not just matching examples |
| **tool_use for structured output** | Most reliable approach — eliminates JSON syntax errors |
| **Syntax vs. semantic errors** | tool_use fixes syntax. Cannot catch logical/calculation errors. |
| **Nullable fields** | Make optional when info may be absent — prevents fabrication |
| **Enum + "other"** | Add "other" + detail string for extensible categories |
| **"unclear" enum value** | For ambiguous/contradictory cases in extraction |
| **Self-correct pattern** | Extract stated + calculated totals → flag if they differ |
| **Retry-with-feedback** | Include original doc + failed extraction + specific errors |
| **When retries fail** | When info is absent from source (not a format issue) |
| **detected_pattern** | Track false positive patterns for systematic improvement |
| **Batch API: cost** | 50% of standard pricing |
| **Batch API: max time** | Up to 24 hours (no latency SLA) |
| **Batch API: limitation** | No multi-turn tool calling within a single batch request |
| **custom_id** | YOUR identifier correlating batch request to result |
| **Batch appropriate** | Overnight reports, weekly audits, nightly generation |
| **Batch NOT appropriate** | Blocking pre-merge checks, real-time responses |
| **Effort levels** | `/effort low/medium/high` (‘max’ removed v2.1.72). Default: `high` for API/pro tiers (v2.1.94) |
| **Self-review limitation** | Retained reasoning = biased. Use independent instance. |
| **Independent instance** | More effective than extended thinking or self-review |
| **Multi-pass review** | Per-file parallel + cross-file integration pass |
| **Confidence routing** | Low confidence → human review. High confidence → auto-flag. |
