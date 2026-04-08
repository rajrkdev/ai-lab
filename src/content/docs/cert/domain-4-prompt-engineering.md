---
title: "Domain 4: Prompt Engineering"
---

# Domain 4: Prompt Engineering & Structured Output

## Weight: 20% of Exam

**Appears in Scenarios:** 5 (CI/CD), 6 (Structured Data Extraction)

---

## Task Statement 4.1: Explicit Criteria for Precision

### Vague Instructions Fail

```python
# ❌ VAGUE — Claude interprets inconsistently
system_prompt = "Review this code and check that comments are accurate."
# Some runs flag every comment. Others flag none.

# ❌ STILL VAGUE — "be conservative" doesn't help
system_prompt = "Review code. Be conservative. Only report high-confidence findings."
# "Conservative" and "high-confidence" mean different things to the model each run.

# ✅ EXPLICIT CRITERIA — Consistent behavior
system_prompt = """Review this code. Flag comments ONLY when:
1. The comment claims a function does X, but the code actually does Y
2. The comment references a variable/function that doesn't exist
3. The comment describes a deprecated behavior that was changed

Do NOT flag:
- Minor style differences in comment formatting
- Comments that are technically correct but could be more detailed
- TODO/FIXME comments (these are intentional markers)
"""
```

### Severity Criteria with Concrete Examples

```python
system_prompt = """
Classify each finding by severity:

CRITICAL (blocks merge):
  - SQL injection: user input directly in query string
  - Unvalidated file paths allowing directory traversal
  - Exposed API keys or credentials in code
  Example: `db.query(f"SELECT * FROM users WHERE id = {user_input}")`

WARNING (should fix before merge):
  - Missing input validation on public API endpoints
  - Unbounded loops without timeout
  - Error messages that expose internal implementation details
  Example: Missing `if (!userId) return 400` before database lookup

INFO (nice to have):
  - Function could be simplified
  - Variable naming could be more descriptive
  - Missing JSDoc on internal helper functions
  Example: `const x = calculateTotal(items)` → rename `x` to `orderTotal`
"""
```

### False Positive Impact on Trust

High false positive rates in one category undermine confidence in ALL categories:

```
If "comment accuracy" findings are wrong 60% of the time:
  → Developers start dismissing ALL findings
  → Including the accurate "security" findings

Fix: Temporarily DISABLE the high-false-positive category
  → Restore trust in remaining categories
  → Improve the disabled category's prompts separately
  → Re-enable once false positive rate is acceptable
```

---

## Task Statement 4.2: Few-Shot Prompting

### When to Use Few-Shot Examples

Use few-shot when:
- Detailed instructions alone produce inconsistent results
- Ambiguous cases need demonstrated judgment
- You need consistent output format
- You want the model to generalize to novel patterns (not just match pre-specified cases)

### Creating Effective Few-Shot Examples

```python
system_prompt = """
You are a code review agent. Analyze code changes and report issues.

## Examples of correct analysis:

### Example 1: True positive (report this)
Code: `user_age = int(request.params["age"])`
Finding: {
  "file": "api/users.py",
  "line": 15,
  "severity": "warning",
  "issue": "Uncaught ValueError if 'age' parameter is not numeric",
  "detected_pattern": "unvalidated_type_cast",
  "suggestion": "Wrap in try/except or validate input first"
}
Reasoning: User input goes directly to int() without validation. This will crash the server with a 500 error if a non-numeric value is passed.

### Example 2: False positive (do NOT report this)
Code:
```python
# Process items in reverse order
for item in reversed(items):
    process(item)
```
Analysis: The comment says "reverse order" and the code uses `reversed()`. This is NOT an issue — the comment accurately describes the code behavior. Do not flag accurate comments as issues.

### Example 3: Ambiguous case (how to decide)
Code:
```python
# Cache results for 5 minutes
@cache(ttl=300)
def get_user(id):
    return db.find(id)
```
Analysis: The comment says "5 minutes" and the TTL is 300 seconds (= 5 minutes). This is CORRECT. Do not flag minor unit differences when the values match.

### Example 4: True positive in comments
Code:
```python
# Returns the user's full name
def get_email(user_id):
    return db.get_email(user_id)
```
Finding: {
  "file": "utils.py",
  "line": 8,
  "severity": "warning",
  "issue": "Comment claims 'Returns the user's full name' but function returns email",
  "detected_pattern": "misleading_comment",
  "suggestion": "Update comment to 'Returns the user's email address'"
}
"""
```

### Few-Shot for Extraction Tasks

Few-shot examples reduce hallucination when extracting from varied document formats:

```python
system_prompt = """
Extract property details from real estate listings.

### Example 1: Standard format
Document: "Beautiful 3BR/2BA home, 1,850 sq ft, built 2005. Listed at $450,000."
Extraction: {
  "bedrooms": 3,
  "bathrooms": 2,
  "sqft": 1850,
  "year_built": 2005,
  "price": 450000
}

### Example 2: Informal format
Document: "Charming cottage with three beds and a bath and a half. About eighteen hundred square feet. Asking mid-fours."
Extraction: {
  "bedrooms": 3,
  "bathrooms": 1.5,
  "sqft": 1800,
  "year_built": null,  ← Not mentioned, use null (don't fabricate!)
  "price": null         ← "mid-fours" is too vague to extract reliably
}

### Example 3: Missing information
Document: "Renovated studio apartment in downtown core. $1,200/month rent."
Extraction: {
  "bedrooms": 0,        ← Studio = 0 bedrooms
  "bathrooms": null,     ← Not mentioned
  "sqft": null,          ← Not mentioned
  "year_built": null,    ← Not mentioned
  "price": null          ← This is rent, not sale price. Different field.
}
"""
```

### Key Principle: Generalization

Few-shot examples teach the model to generalize judgment to NEW patterns, not just match the examples you showed. In Example 3 above, showing how to handle a studio teaches the model to handle any non-standard property type.

---

## Task Statement 4.3: Structured Output via tool_use

### Why tool_use Is the Most Reliable Approach

```python
# ❌ UNRELIABLE — Asking Claude to output JSON as text
response = client.messages.create(
    messages=[{"role": "user", "content": "Extract data and return as JSON"}],
)
# Problem: Claude might include markdown formatting, explanatory text,
# or produce invalid JSON syntax.

# ✅ RELIABLE — Using tool_use with JSON schema
response = client.messages.create(
    tools=[{
        "name": "extract_invoice",
        "description": "Extract structured data from an invoice document",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_name": {"type": "string"},
                "invoice_number": {"type": "string"},
                "total_amount": {"type": "number"},
                "currency": {"type": "string", "enum": ["USD", "EUR", "GBP", "other"]},
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit_price": {"type": "number"},
                            "total": {"type": "number"}
                        }
                    }
                }
            },
            "required": ["vendor_name", "total_amount"]
        }
    }],
    tool_choice={"type": "tool", "name": "extract_invoice"},  # Force this tool
    messages=[{"role": "user", "content": f"Extract data from:\n{invoice_text}"}],
)

# Extract structured data from the tool_use response
for block in response.content:
    if block.type == "tool_use":
        extracted_data = block.input  # Guaranteed valid JSON matching schema
```

### TypeScript Version

```typescript
const response = await client.messages.create({
  model: "claude-sonnet-4-20250514",
  max_tokens: 4096,
  tools: [{
    name: "extract_invoice",
    description: "Extract structured data from an invoice document",
    input_schema: {
      type: "object",
      properties: {
        vendor_name: { type: "string" },
        invoice_number: { type: "string" },
        total_amount: { type: "number" },
        currency: { type: "string", enum: ["USD", "EUR", "GBP", "other"] },
        line_items: {
          type: "array",
          items: {
            type: "object",
            properties: {
              description: { type: "string" },
              quantity: { type: "number" },
              unit_price: { type: "number" },
              total: { type: "number" },
            },
          },
        },
      },
      required: ["vendor_name", "total_amount"],
    },
  }],
  tool_choice: { type: "tool", name: "extract_invoice" },
  messages: [{ role: "user", content: `Extract data from:\n${invoiceText}` }],
});

const toolUseBlock = response.content.find(b => b.type === "tool_use");
const extractedData = toolUseBlock?.input; // Typed, valid JSON
```

### Syntax Errors vs Semantic Errors

**Tool use eliminates SYNTAX errors** (invalid JSON, missing brackets, wrong types). But it does NOT prevent **SEMANTIC errors**:

```json
// Syntax error (eliminated by tool_use): ✅ Fixed
{"total": 99.99   ← missing closing brace

// Semantic error (NOT caught by tool_use): ❌ Still possible
{
  "line_items": [
    {"description": "Widget A", "quantity": 2, "unit_price": 10, "total": 20},
    {"description": "Widget B", "quantity": 3, "unit_price": 15, "total": 45}
  ],
  "total_amount": 100  // ← WRONG! Should be 65 (20 + 45), but schema can't catch this
}
```

### Schema Design Best Practices

**Optional/Nullable Fields (Prevent Fabrication):**
```json
{
  "type": "object",
  "properties": {
    "vendor_name": {"type": "string"},
    "tax_id": {"type": ["string", "null"]},  // Nullable — may not exist in document
    "discount": {"type": ["number", "null"]}   // Nullable — not all invoices have discounts
  },
  "required": ["vendor_name"]  // Only require what MUST exist
}
```

**Enum with "other" + Detail String:**
```json
{
  "document_type": {
    "type": "string",
    "enum": ["invoice", "receipt", "contract", "other"]
  },
  "document_type_detail": {
    "type": ["string", "null"],
    "description": "If document_type is 'other', describe the actual type"
  }
}
```

**"unclear" Enum Value:**
```json
{
  "payment_status": {
    "type": "string",
    "enum": ["paid", "unpaid", "partial", "unclear"],
    "description": "Use 'unclear' when the document contains conflicting or ambiguous payment information"
  }
}
```

---

## Task Statement 4.4: Validation, Retry, and Feedback Loops

### Retry-with-Error-Feedback

When extraction fails validation, send the original document, the failed extraction, AND the specific error:

```python
# First attempt
extraction = extract_from_document(document_text)
errors = validate_extraction(extraction)

if errors:
    # Retry with specific feedback
    retry_prompt = f"""
The following extraction from this document had validation errors.

ORIGINAL DOCUMENT:
{document_text}

FAILED EXTRACTION:
{json.dumps(extraction, indent=2)}

VALIDATION ERRORS:
{json.dumps(errors, indent=2)}

Please re-extract, fixing these specific errors.
"""
    corrected = extract_from_document(retry_prompt)
```

### When Retries Are Ineffective

Retries work for **format/structural errors** (wrong date format, misplaced field).
Retries DON'T work when **information is absent** from the source document.

```python
# ✅ RETRY WILL HELP (format mismatch):
error = "Expected date in YYYY-MM-DD format, got 'January 5, 2025'"
# Claude can convert the format on retry.

# ❌ RETRY WON'T HELP (info doesn't exist):
error = "Required field 'tax_id' is null"
# If the document doesn't contain a tax ID, no amount of retrying will find one.
# Solution: Make the field optional (nullable) in the schema.
```

### Feedback Loops with detected_pattern

Add `detected_pattern` fields to enable analysis of false positive patterns:

```json
{
  "file": "auth.py",
  "line": 42,
  "severity": "warning",
  "issue": "Potential SQL injection in user query",
  "detected_pattern": "string_concatenation_in_sql",
  "suggestion": "Use parameterized queries"
}
```

When developers dismiss findings, you can analyze which `detected_pattern` values get dismissed most frequently and improve prompts for those patterns.

### Self-Correction Validation Flows

Extract both calculated and stated values to catch semantic errors:

```json
{
  "line_items": [...],
  "stated_total": 150.00,      // What the document says
  "calculated_total": 135.00,   // Sum of line items
  "conflict_detected": true,    // Flag the discrepancy
  "conflict_note": "Stated total ($150) differs from sum of line items ($135)"
}
```

---

## Task Statement 4.5: Batch Processing Strategies

### Message Batches API — Key Facts

| Fact | Detail |
|---|---|
| **Cost savings** | 50% of standard pricing |
| **Processing window** | Up to 24 hours |
| **Latency SLA** | None guaranteed |
| **Request correlation** | `custom_id` field on each request |
| **Multi-turn tool calling** | NOT supported |
| **Max requests per batch** | 100,000 |
| **Result availability** | 29 days |
| **Typical completion** | Under 1 hour |

### Appropriate vs Inappropriate Workloads

```
✅ APPROPRIATE (latency-tolerant, non-blocking):
  - Overnight technical debt reports
  - Weekly audit analysis
  - Nightly test generation
  - Batch document extraction (100+ documents)

❌ INAPPROPRIATE (blocking, latency-sensitive):
  - Pre-merge code review checks (developers waiting)
  - Real-time customer support
  - Interactive code generation
```

### Batch Submission with custom_id

```python
import anthropic

client = anthropic.Anthropic()

# Create batch of extraction requests
requests = []
for i, document in enumerate(documents):
    requests.append({
        "custom_id": f"doc-{document.id}",  # YOUR unique identifier
        "params": {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "tools": [extraction_tool],
            "tool_choice": {"type": "tool", "name": "extract_data"},
            "messages": [{"role": "user", "content": document.text}]
        }
    })

# Submit batch
batch = client.messages.batches.create(requests=requests)
print(f"Batch ID: {batch.id}")

# Poll for completion
import time
while True:
    status = client.messages.batches.retrieve(batch.id)
    if status.processing_status == "ended":
        break
    time.sleep(60)  # Check every minute

# Process results
results = client.messages.batches.results(batch.id)
for result in results:
    doc_id = result.custom_id           # Correlate back to your document
    if result.result.type == "succeeded":
        extraction = result.result.message
    elif result.result.type == "errored":
        # Resubmit this specific document
        failed_docs.append(doc_id)
    elif result.result.type == "expired":
        # Didn't complete within 24 hours
        expired_docs.append(doc_id)
```

### Handling Batch Failures

```python
# Resubmit only failed documents with modifications
retry_requests = []
for doc_id in failed_docs:
    document = get_document(doc_id)
    if document.token_count > context_limit:
        # Chunk oversized documents
        chunks = chunk_document(document, max_tokens=context_limit // 2)
        for j, chunk in enumerate(chunks):
            retry_requests.append({
                "custom_id": f"{doc_id}-chunk-{j}",
                "params": {
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4096,
                    "tools": [extraction_tool],
                    "messages": [{"role": "user", "content": chunk.text}]
                }
            })
    else:
        retry_requests.append({
            "custom_id": doc_id,
            "params": {...}  # Same as original
        })

retry_batch = client.messages.batches.create(requests=retry_requests)
```

### Prompt Refinement Before Batch Processing

Test prompts on a sample set before processing large volumes:

```python
# Step 1: Test on 10 sample documents
sample_results = process_sample(documents[:10], extraction_prompt)

# Step 2: Analyze accuracy
accuracy = evaluate_results(sample_results, ground_truth)
print(f"First-pass accuracy: {accuracy}%")

# Step 3: Refine prompt based on errors
if accuracy < 95:
    refined_prompt = improve_prompt(extraction_prompt, sample_errors)
    # Test again on a different sample
    
# Step 4: Only then batch-process the full 10,000 documents
batch = submit_batch(documents, refined_prompt)
```

---

## Task Statement 4.6: Multi-Instance and Multi-Pass Review

### Self-Review Limitations

A model retains reasoning context from generation. If Claude generated code, it remembers WHY it made each decision. This makes it less likely to question those decisions in the same session.

```python
# ❌ SAME SESSION — Claude reviews its own work with bias
session_1 = generate_code("Build auth middleware")
review = ask_same_session("Now review the code you just wrote for bugs")
# Claude is unlikely to find issues in its own reasoning.

# ✅ INDEPENDENT INSTANCE — No prior reasoning context
session_1 = generate_code("Build auth middleware")
# Start a completely fresh session for review
session_2 = review_code(session_1.output, "Review this auth middleware for bugs")
# Fresh Claude instance examines code without knowing why decisions were made.
```

### Multi-Pass Review for Large PRs

Split into focused passes to avoid attention dilution:

```
14-file PR review:

PASS 1 — Per-File Local Analysis:
  For each file individually:
    "Review auth.ts for: bugs, type errors, unhandled exceptions"
    "Review users.ts for: bugs, type errors, unhandled exceptions"
    ...
    → Consistent depth for each file

PASS 2 — Cross-File Integration:
  With summaries from Pass 1:
    "Given these per-file findings, check cross-file data flow:
     - Does auth.ts export match what users.ts imports?
     - Are error types from errors.ts handled in api.ts?
     - Do database queries in db.ts match the schema in models.ts?"
    → Catches integration issues that per-file reviews miss
```

### Confidence-Based Review Routing

```json
{
  "finding": "Potential null pointer on line 42",
  "confidence": 0.9,
  "routing": "auto-approve"
}

{
  "finding": "Logic might cause race condition under load",
  "confidence": 0.4,
  "routing": "human-review"
}
```

---

## Quick Reference — Domain 4 Cheat Sheet

| Concept | Key Fact |
|---|---|
| **Explicit criteria** | "Flag only when X contradicts Y" beats "check accuracy" |
| **"Be conservative"** | Fails to improve precision. Use specific categorical criteria. |
| **False positives** | Disable high-FP categories to restore trust, improve separately |
| **Few-shot examples** | Most effective for consistent formatting and ambiguous cases |
| **Few-shot count** | 2-4 targeted examples for ambiguous scenarios |
| **Generalization** | Few-shot enables novel pattern recognition, not just matching |
| **tool_use for structured output** | Most reliable approach. Eliminates JSON syntax errors. |
| **Syntax vs semantic errors** | tool_use fixes syntax. Cannot catch logical/semantic errors. |
| **Nullable fields** | Make optional when info may be absent. Prevents fabrication. |
| **Enum with "other"** | Add "other" + detail string for extensible categories |
| **"unclear" enum** | For ambiguous cases in extraction |
| **Retry-with-feedback** | Include original doc + failed extraction + specific errors |
| **When retries fail** | When info is absent from source (not a format issue) |
| **detected_pattern** | Track which code patterns trigger findings for FP analysis |
| **Batch API savings** | 50% cost reduction |
| **Batch processing time** | Up to 24 hours, no SLA |
| **Batch limitations** | No multi-turn tool calling |
| **custom_id** | Correlate batch request/response pairs |
| **Batch appropriate** | Overnight reports, weekly audits, nightly test gen |
| **Batch inappropriate** | Blocking pre-merge checks |
| **Self-review limitation** | Retained reasoning context = biased review |
| **Independent instance** | More effective than self-review or extended thinking |
| **Multi-pass review** | Per-file local + cross-file integration passes |
