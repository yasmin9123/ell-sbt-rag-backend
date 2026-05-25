import os
import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# Allow your website to call this backend.
# Later, you can replace "*" with your exact GitHub Pages website URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# IMPORTANT:
# Replace this with YOUR actual GitHub Pages website URL.
# Example:
# https://yasminkorin.github.io/ELL-SBT
SBT_BASE_URL = os.environ.get("SBT_BASE_URL", "PASTE_YOUR_GITHUB_PAGES_URL_HERE")


class AskRequest(BaseModel):
    question: str


def fetch_json(path: str):
    url = f"{SBT_BASE_URL}/{path}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


def load_sbt_context():
    manifest = fetch_json("rag_manifest.json")

    context_parts = []
    context_parts.append("RAG MANIFEST:\n" + json.dumps(manifest, indent=2))

    for file_info in manifest.get("canonical_files", []):
        path = file_info["path"]
        try:
            data = fetch_json(path)
            context_parts.append(f"\n\nFILE: {path}\n" + json.dumps(data, indent=2))
        except Exception as e:
            context_parts.append(f"\n\nFILE: {path}\nERROR LOADING FILE: {str(e)}")

    return "\n".join(context_parts)


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "ELL SBT RAG backend is running. Use POST /ask to ask questions."
    }


@app.post("/ask")
def ask_sbt(request: AskRequest):
    question = request.question.strip()

    if not question:
        return {"answer": "Please enter a question."}

    sbt_context = load_sbt_context()

    system_prompt = """
You are a RAG assistant for a public Soulbound Token profile.

Rules:
1. Answer only using the provided SBT context.
2. Cite claim IDs, evidence IDs, file names, or schema fields whenever possible.
3. Do not invent facts.
4. If the available SBT evidence does not support an answer, say that clearly.
5. Keep answers clear, professional, and evidence-backed.
"""

    user_prompt = f"""
SBT CONTEXT:
{sbt_context}

USER QUESTION:
{question}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return {
        "question": question,
        "answer": response.output_text
    }
