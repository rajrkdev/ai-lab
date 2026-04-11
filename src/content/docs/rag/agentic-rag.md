---
title: Agentic RAG
description: Self-RAG, CRAG, tool-calling RAG, query routing, and multi-agent retrieval patterns — with LangGraph and LangChain implementation examples.
sidebar:
  order: 10
---

## What Is Agentic RAG?

In standard RAG, retrieval is a fixed step: query → retrieve → generate. In **Agentic RAG**, an LLM agent dynamically decides:

- **Whether** to retrieve (or answer from memory)
- **What** to retrieve (which knowledge source, search query)
- **When** to retrieve (before or during generation)
- **Whether to retry** (if retrieved context is insufficient)
- **How to synthesize** across multiple retrieval rounds

Agentic RAG trades simplicity for significantly higher answer quality on complex, multi-hop questions.

---

## Self-RAG

**Paper:** Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection" (2023)  
**Model:** `selfrag/selfrag_llama3_8b` (fine-tuned Llama 3 8B)

Self-RAG is a fine-tuned LLM that generates **special reflection tokens** inline with its output to control retrieval and evaluate quality:

| Token | Type | Meaning |
|---|---|---|
| `[Retrieve]` | Retrieval decision | "I need to look this up" |
| `[No Retrieve]` | Retrieval decision | "I can answer from memory" |
| `[ISREL]` | Relevance | Retrieved passage is relevant |
| `[ISIRREL]` | Relevance | Retrieved passage is irrelevant |
| `[ISSUP]` | Support | My generation is supported by the passage |
| `[ISPART]` | Support | Partially supported |
| `[ISUSE]` | Utility | Response is useful for the query |
| `[ISNOUSE]` | Utility | Response is not useful |

### Self-RAG Generation Loop

```
Start generating response
    ↓
Model emits [Retrieve]
    ↓
System retrieves relevant documents
    ↓
Model generates passage evaluation tokens ([ISREL], [ISSUP])
    ↓
If [ISIRREL]: discard passage, try another
    ↓
Continue generation
    ↓
Model emits [ISUSE] at end → validate final response
```

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Load Self-RAG fine-tuned model
model_name = "selfrag/selfrag_llama3_8b"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map="auto")

def self_rag_generate(query: str, retriever, max_new_tokens=200):
    # Format instruction
    instruction = f"### Instruction:\n{query}\n\n### Response:\n"
    inputs = tokenizer(instruction, return_tensors="pt").to(model.device)

    # Generate with beam search
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
        )

    generated = tokenizer.decode(outputs[0], skip_special_tokens=False)

    # Parse reflection tokens (real implementation is more complex)
    if "[Retrieve]" in generated:
        # Re-run with retrieved context
        docs = retriever.invoke(query)
        context = "\n".join([d.page_content for d in docs[:3]])
        prompt_with_ctx = f"### Instruction:\n{query}\n\n### Input:\n{context}\n\n### Response:\n"
        inputs2 = tokenizer(prompt_with_ctx, return_tensors="pt").to(model.device)
        outputs2 = model.generate(**inputs2, max_new_tokens=max_new_tokens)
        return tokenizer.decode(outputs2[0], skip_special_tokens=True)

    return generated
```

---

## Corrective RAG (CRAG)

**Paper:** Yan et al., "Corrective Retrieval Augmented Generation" (2024)

CRAG uses a **lightweight relevance evaluator** to classify retrieved documents. If documents are deemed irrelevant, it corrects by web search before generating.

### Decision Flow

```
Query → Retrieve from vector store
             ↓
    Evaluate relevance of each doc
             ↓
    ┌────────┴──────────┐
  CORRECT          INCORRECT          AMBIGUOUS
    ↓                  ↓                  ↓
Use docs          Web search        Use both
    ↓                  ↓
    └──────────┬────────┘
               ↓
           Generate
```

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_community.tools import TavilySearchResults

class CRAGState(TypedDict):
    question: str
    documents: list
    web_results: list
    generation: str
    relevance: str

def retrieve(state: CRAGState) -> CRAGState:
    docs = retriever.invoke(state["question"])
    return {**state, "documents": docs}

def evaluate_relevance(state: CRAGState) -> CRAGState:
    prompt = f"""Evaluate if these documents are relevant to the question.
Question: {state["question"]}
Documents: {[d.page_content[:300] for d in state["documents"][:3]]}
Answer with exactly: CORRECT, INCORRECT, or AMBIGUOUS"""
    result = llm.invoke(prompt).content.strip().upper()
    relevance = "CORRECT" if "CORRECT" in result else ("INCORRECT" if "INCORRECT" in result else "AMBIGUOUS")
    return {**state, "relevance": relevance}

def web_search(state: CRAGState) -> CRAGState:
    search = TavilySearchResults(max_results=3)
    results = search.invoke(state["question"])
    web_docs = [Document(page_content=r["content"], metadata={"source": r["url"]}) for r in results]
    return {**state, "web_results": web_docs}

def generate(state: CRAGState) -> CRAGState:
    docs = state["documents"]
    if state["relevance"] == "INCORRECT":
        docs = state["web_results"]
    elif state["relevance"] == "AMBIGUOUS":
        docs = state["documents"] + state.get("web_results", [])

    context = "\n\n".join([d.page_content for d in docs])
    answer = llm.invoke(f"Context:\n{context}\n\nQuestion: {state['question']}\nAnswer:").content
    return {**state, "generation": answer}

def route_after_eval(state: CRAGState) -> str:
    return "web_search" if state["relevance"] in ("INCORRECT", "AMBIGUOUS") else "generate"

# Build LangGraph workflow
workflow = StateGraph(CRAGState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("evaluate_relevance", evaluate_relevance)
workflow.add_node("web_search", web_search)
workflow.add_node("generate", generate)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "evaluate_relevance")
workflow.add_conditional_edges("evaluate_relevance", route_after_eval, {"web_search": "web_search", "generate": "generate"})
workflow.add_edge("web_search", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()
result = app.invoke({"question": "What is CRAG in RAG systems?"})
print(result["generation"])
```

---

## Tool-Calling RAG

An agent equipped with multiple retrieval tools chooses which to invoke based on query classification:

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import tool

llm = ChatOpenAI(model="gpt-4o", temperature=0)

@tool
def search_technical_docs(query: str) -> str:
    """Search the internal technical documentation and API references."""
    docs = tech_docs_retriever.invoke(query)
    return "\n\n".join([d.page_content for d in docs[:3]])

@tool
def search_support_kb(query: str) -> str:
    """Search the customer support knowledge base for troubleshooting guides."""
    docs = support_retriever.invoke(query)
    return "\n\n".join([d.page_content for d in docs[:3]])

@tool
def search_web(query: str) -> str:
    """Search the web for current information not available in internal docs."""
    results = TavilySearchResults(max_results=3).invoke(query)
    return "\n".join([r["content"] for r in results])

tools = [search_technical_docs, search_support_kb, search_web]

from langchain import hub
prompt = hub.pull("hwchase17/openai-tools-agent")

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

response = agent_executor.invoke({
    "input": "How do I fix a 429 rate limit error when calling the embeddings API?"
})
```

---

## Adaptive RAG

**Paper:** Jeong et al., "Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity" (2024)

A classifier routes queries to the most appropriate retrieval strategy based on complexity:

| Query type | Strategy | Example |
|---|---|---|
| Simple factual | No retrieval (LLM memory) | "What is 2+2?" |
| Single-hop | Single retrieval round | "What year was BERT published?" |
| Multi-hop | Iterative retrieval | "Compare the architectures of BERT and GPT in 2024" |

```python
from langchain_core.prompts import ChatPromptTemplate

classify_prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify the query complexity:\n- simple: answerable without retrieval\n- single_hop: needs one retrieval round\n- multi_hop: needs multiple retrieval rounds\nOutput one of: simple, single_hop, multi_hop"),
    ("human", "{question}"),
])

def adaptive_rag(question: str) -> str:
    complexity = (classify_prompt | llm | StrOutputParser()).invoke({"question": question})

    if complexity == "simple":
        return llm.invoke(question).content

    elif complexity == "single_hop":
        docs = retriever.invoke(question)
        context = format_docs(docs)
        return llm.invoke(f"Context:\n{context}\n\nQuestion: {question}").content

    else:  # multi_hop
        return iterative_retrieval_generate(question)

def iterative_retrieval_generate(question: str, max_rounds: int = 3) -> str:
    context = ""
    for _ in range(max_rounds):
        new_docs = retriever.invoke(question)
        context += "\n\n" + format_docs(new_docs)
        # Check if enough context
        check = llm.invoke(f"Context: {context}\nQuestion: {question}\nDo you have enough information? Reply YES or NO.")
        if "YES" in check.content:
            break
    return llm.invoke(f"Context:\n{context}\n\nAnswer: {question}").content
```

---

## Agentic RAG with LangGraph

LangGraph models agentic RAG as a directed graph with conditional edges — enabling cycles (self-correction) and parallel retrieval.

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    question: str
    retrieved_docs: Annotated[list, operator.add]   # accumulate across rounds
    generation: str
    iterations: int

MAX_ITERATIONS = 3

def retrieve_node(state: AgentState) -> AgentState:
    query = state.get("revised_query", state["question"])
    docs = retriever.invoke(query)
    return {**state, "retrieved_docs": docs, "iterations": state.get("iterations", 0) + 1}

def generate_node(state: AgentState) -> AgentState:
    context = "\n\n".join([d.page_content for d in state["retrieved_docs"]])
    answer = llm.invoke(f"Context:\n{context}\n\nQuestion: {state['question']}\nAnswer:").content
    return {**state, "generation": answer}

def grade_generation(state: AgentState) -> AgentState:
    check = llm.invoke(f"""
    Question: {state['question']}
    Answer: {state['generation']}
    Is the answer grounded in the context and fully answers the question?
    Answer in JSON: {{"grounded": true/false, "complete": true/false, "revised_query": "..."}}
    """).content
    import json
    try:
        result = json.loads(check)
        return {**state, **result}
    except:
        return {**state, "grounded": True, "complete": True}

def should_continue(state: AgentState) -> str:
    if state.get("grounded") and state.get("complete"):
        return "end"
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        return "end"
    return "retrieve"

workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.add_node("grade", grade_generation)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", "grade")
workflow.add_conditional_edges("grade", should_continue, {"retrieve": "retrieve", "end": END})

app = workflow.compile()
```

---

## Comparison: Self-RAG vs CRAG vs Tool-Calling vs Adaptive

| Feature | Self-RAG | CRAG | Tool-calling | Adaptive RAG |
|---|---|---|---|---|
| **Controls retrieval** | Via reflection tokens | Via relevance classifier | Via agent decision | Via query classifier |
| **Model fine-tuning needed** | Yes (special tokens) | No | No | Yes (classifier) |
| **External search fallback** | No | Yes | Yes | Optional |
| **Multiple retrieval rounds** | Yes | No | Yes | Yes (multi-hop) |
| **Latency** | High | Medium | High | Low–High |
| **Best for** | Quality-critical, no latency constraint | Improving unreliable retrieval | Multi-source routing | Scaling large query volumes |

---

## See Also

- [Advanced RAG](./advanced-rag) — pre/post retrieval optimizations (simpler, no agent required)
- [Retrieval Strategies](./retrieval-strategies) — underlying retrieval mechanisms used by agents
- [Evaluation](./evaluation) — measuring whether agentic approaches actually improve scores
- [RAG Types](./rag-types) — interactive side-by-side architecture comparison
