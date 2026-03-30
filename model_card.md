# DocuBot Model Card
# 👉 [Model Card](model_card.md) | [ReadMe](ReadMe.md) | 

This model card reflects on the design, behaviour, and limitations of DocuBot after implementing retrieval and testing all three system modes.

1. Naive LLM over full docs  
2. Retrieval only  
3. RAG (retrieval plus LLM)

---

## 1. System Overview

**What is DocuBot trying to do?**  
DocuBot is a lightweight documentation assistant designed to help developers
answer questions using only the information available in a local documentation
folder. Its goal is to demonstrate how retrieval improves reliability compared
to naive language model generation.

**What inputs does DocuBot take?**  
DocuBot takes the following inputs:
- A user question
- Documentation files stored in the `docs/` folder (`.txt` and `.md`)
- An optional `GEMINI_API_KEY` environment variable for LLM features

**What outputs does DocuBot produce?**  
DocuBot outputs:
- Retrieved documentation snippets (retrieval-only mode)
- A grounded, LLM-generated answer (RAG mode)
- An explicit refusal (“I do not know”) when documentation does not support an answer

---

## 2. Retrieval Design

**How does your retrieval system work?**  
The retrieval system:
- Splits each document into paragraph-level snippets
- Builds a simple inverted index over lowercase words
- Scores each paragraph by counting how many query terms appear
- Sorts paragraphs by score and returns the top-k matches

**What tradeoffs did you make?**  
- Chose simplicity and transparency over sophisticated ranking
- Used keyword matching instead of embeddings to keep behavior explainable
- Accepted lower recall in exchange for clearer refusal behavior

---

## 3. Use of the LLM (Gemini)

**When does DocuBot call the LLM and when does it not?**  

- **Naive LLM mode:** Sends the full documentation corpus to the LLM with no retrieval
- **Retrieval-only mode:** Never calls the LLM; returns raw snippets only
- **RAG mode:** Retrieves relevant snippets first, then calls the LLM using only those snippets

**What instructions do you give the LLM to keep it grounded?**  
The LLM is explicitly instructed to:
- Use only the retrieved snippets
- Refuse to guess if the snippets are insufficient
- Avoid inventing endpoints, functions, or configuration values
- Say “I do not know based on the docs I have” when appropriate

---

## 4. Experiments and Comparisons

| Query | Naive LLM | Retrieval Only | RAG | Notes |
|-----|-----------|----------------|-----|------|
| Where is the auth token generated? | Sounded confident but vague | Returned correct snippet | Clear and grounded | RAG balanced clarity and evidence |
| How do I connect to the database? | Mixed details incorrectly | Accurate but long | Accurate and readable | Retrieval prevented guessing |
| Which endpoint lists all users? | Confident but unsupported | Correct snippet | Correct summary | Naive mode risks hallucination |
| How does a client refresh an access token? | Looked plausible | No result | Refused safely | Correct refusal behavior |

**What patterns did you notice?**
- Naive LLM often sounds impressive but ungrounded
- Retrieval-only is accurate but harder to interpret
- RAG provides the best balance when documentation exists
- Refusal is safer than confident guessing

---

## 5. Failure Cases and Guardrails

**Failure case 1**  
- Question: “How do I deploy this service to AWS?”
- System behavior: Retrieval and RAG refused
- Correct behavior: Refusal (no deployment info exists)

**Failure case 2**  
- Question: Vague query using synonyms not in docs
- System behavior: No retrieval results
- Correct behavior: Explicit refusal instead of guessing

**When should DocuBot say “I do not know based on the docs I have”?**
- When no relevant snippets match the query
- When retrieved snippets are insufficient to answer confidently

**What guardrails did you implement?**
- Refusal when retrieval returns no results
- Hard limit on number of snippets passed to the LLM
- Prompt rules preventing unsupported claims

---

## 6. Limitations and Future Improvements

**Current limitations**
1. Retrieval depends on exact keyword overlap
2. No semantic understanding or synonyms
3. No ranking beyond simple term counts

**Future improvements**
1. Add semantic embeddings for retrieval
2. Improve snippet chunking strategy
3. Add confidence indicators in responses

---

## 7. Responsible Use

**Where could this system cause real-world harm if used carelessly?**  
If users overtrust naive LLM mode, they may act on incorrect or invented
information. Missing or outdated documentation can also lead to false assumptions.

**Instructions for safe use**
- Do not trust naive LLM outputs without verification
- Treat “I do not know” responses as safety features, not failures
- Always verify answers against source documentation when making decisions