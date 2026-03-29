"""
Gemini client wrapper used by DocuBot.

Handles:
- Configuring the Gemini client from the GEMINI_API_KEY environment variable
- Naive "generation only" answers over the full docs corpus (Phase 0)
- RAG style answers that use only retrieved snippets (Phase 2)

Experiment with:
- Prompt wording
- Refusal conditions
- How strictly the model is instructed to use only the provided context
"""

import os
import google.generativeai as genai
from google.api_core import exceptions
import time

# Central place to update the model name if needed.
# You can swap this for a different Gemini model in the future.
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds


class GeminiClient:
    """
    Simple wrapper around the Gemini model.

    Usage:
        client = GeminiClient()
        answer = client.naive_answer_over_full_docs(query, all_text)
        # or
        answer = client.answer_from_snippets(query, snippets)
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY environment variable. "
                "Set it in your shell or .env file to enable LLM features."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)

    def _call_api_with_retry(self, prompt):
        """
        Call the Gemini API with retry logic and error handling.
        
        Handles:
        - Rate limiting (ResourceExhausted)
        - Transient errors with exponential backoff
        - Other API errors gracefully
        """
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.model.generate_content(prompt)
                return response.text or ""
            except exceptions.ResourceExhausted as e:
                # Out of quota - don't retry immediately, give clear feedback
                error_msg = (
                    f"API quota exceeded (attempt {attempt + 1}/{MAX_RETRIES}). "
                    f"Please check your plan and billing at https://ai.google.dev/billing/quota"
                )
                last_error = error_msg
                print(f"\n⚠️  {error_msg}")
                
                if attempt < MAX_RETRIES - 1:
                    delay = INITIAL_RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    print(f"   Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    break
            except (exceptions.DeadlineExceeded, exceptions.ServiceUnavailable) as e:
                # Transient errors - retry with exponential backoff
                last_error = str(e)
                print(f"\n⚠️  API temporarily unavailable (attempt {attempt + 1}/{MAX_RETRIES}). Retrying...")
                
                if attempt < MAX_RETRIES - 1:
                    delay = INITIAL_RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    break
            except exceptions.GoogleAPIError as e:
                # Other API errors
                error_msg = f"API Error: {str(e)}"
                last_error = error_msg
                print(f"\n❌ {error_msg}")
                break
            except Exception as e:
                # Unexpected errors
                error_msg = f"Unexpected error: {str(e)}"
                last_error = error_msg
                print(f"\n❌ {error_msg}")
                break
        
        # If we exhausted retries or hit an error, return error message
        return f"[Error: Unable to get response from LLM. {last_error}]"

    # -----------------------------------------------------------
    # Phase 0: naive generation over full docs
    # -----------------------------------------------------------

    def naive_answer_over_full_docs(self, query, all_text):
        # We ignore all_text and send a generic prompt instead
        prompt = f"""
    You are a documentation assistant. 
    Answer this developer question: {query}
    """
        return self._call_api_with_retry(prompt)

    # -----------------------------------------------------------
    # Phase 2: RAG style generation over retrieved snippets
    # -----------------------------------------------------------

    def answer_from_snippets(self, query, snippets):
        """
        Phase 2:
        Generate an answer using only the retrieved snippets.

        snippets: list of (filename, text) tuples selected by DocuBot.retrieve

        The prompt:
        - Shows each snippet with its filename
        - Instructs the model to rely only on these snippets
        - Requires an explicit "I do not know" refusal when needed
        """

        if not snippets:
            return "I do not know based on the docs I have."

        context_blocks = []
        for filename, text in snippets:
            block = f"File: {filename}\n{text}\n"
            context_blocks.append(block)

        context = "\n\n".join(context_blocks)

        prompt = f"""
You are a cautious documentation assistant helping developers understand a codebase.

You will receive:
- A developer question
- A small set of snippets from project files

Your job:
- Answer the question using only the information in the snippets.
- If the snippets do not provide enough evidence, refuse to guess.

Snippets:
{context}

Developer question:
{query}

Rules:
- Use only the information in the snippets. Do not invent new functions,
  endpoints, or configuration values.
- If the snippets are not enough to answer confidently, reply exactly:
  "I do not know based on the docs I have."
- When you do answer, briefly mention which files you relied on.
"""

        return self._call_api_with_retry(prompt).strip()
