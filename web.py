from flask import Flask, render_template, request
from docubot import DocuBot
from llm_client import GeminiClient

app = Flask(__name__)

# Initialize DocuBot and LLM
bot = DocuBot(docs_folder="docs")
try:
    llm = GeminiClient()
    has_llm = True
except RuntimeError:
    llm = None
    has_llm = False

@app.route("/", methods=["GET", "POST"])
def index():
    answer = None

    if request.method == "POST":
        question = request.form.get("question", "")
        mode = request.form.get("mode", "retrieval")

        if mode == "retrieval":
            result = bot.retrieve(question)
            answer = "\n---\n".join(result) if result else "I do not know."

        elif mode == "rag":
            if not has_llm:
                answer = "LLM not available (missing GEMINI_API_KEY)"
            else:
                snippets = bot.retrieve(question)
                if snippets:
                    answer = llm.answer_from_snippets(question, snippets)
                else:
                    answer = "I do not know based on the provided documentation."

    return render_template("index.html", answer=answer)

if __name__ == "__main__":
    app.run(debug = True)