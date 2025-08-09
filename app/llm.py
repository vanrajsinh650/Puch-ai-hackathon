import httpx
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def summarize_transcript(transcript: str) -> str:
    prompt = f"Summarize this transcript:\n{transcript}"
    return call_llm(prompt)

def ask_question_about_transcript(transcript: str, question: str) -> str:
    prompt = f"Answer this question based on transcript:\nTranscript: {transcript}\nQuestion: {question}"
    return call_llm(prompt)

def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = httpx.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
    return response.json()["choices"][0]["message"]["content"]
