import base64
from fastapi import FastAPI, Request, HTTPException
from app.utils import download_audio_from_url
from app.puch_ai import transcribe_audio_async
from app.llm import summarize_transcript, ask_question_about_transcript
import os
import uvicorn

app = FastAPI()
MCP_TOKEN = os.getenv("AUTH_TOKEN")

@app.middleware("http")
async def verify_token(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {MCP_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)

def decode_url(encoded_url: str) -> str:
    return base64.urlsafe_b64decode(encoded_url.encode()).decode()

@app.get("/summarize/")
async def summarize_video(encoded_url: str):
    video_url = decode_url(encoded_url)
    audio_path = download_audio_from_url(video_url)
    transcript = await transcribe_audio_async(audio_path)
    summary = summarize_transcript(transcript)
    return {"summary": summary}

@app.get("/ask/")
async def ask_question(encoded_url: str, question: str):
    video_url = decode_url(encoded_url)
    audio_path = download_audio_from_url(video_url)
    transcript = await transcribe_audio_async(audio_path)
    answer = ask_question_about_transcript(transcript, question)
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
