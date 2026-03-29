from flask import Flask, render_template, request
from pathlib import Path
from docubot import DocuBot
from llm_client import LLMClient

app = Flask(__name__)

def load_documents():
    docs = {}
    for path in Path("docs").glob("*.txt"):
        docs[path.name] = path.read_text(encoding="utf-8")
    return docs

documents = load_documents()
bot = DocuBot(documents)
bot.build_index()
llm = LLMClient()

@app.route("/", methods = ["GET", "POST"])
def index():
    answer = None

    if request.method == "POST":
        question = request.form["questiion"]
        mode = request.form["mode"]

        if mode == "retrieval":
            result = bot.retrieve(question)
            answer = result if result else "I do not know."

        elif mode == "rag":
            context = bot.retrieve(question)
            answer = llm.generate(context, question)

    return render_template("index.html", answer = answer)

if __name__ == "__main__":
    app.run(debug = True)