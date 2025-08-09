import sys
import os
import base64
import re
import shutil
import traceback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from typing import Annotated
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken
from pydantic import BaseModel, Field
from app.utils import download_audio_from_url
from app.puch_ai import transcribe_audio
from app.llm import summarize_transcript, ask_question_about_transcript

# --- Load environment variables ---
load_dotenv()
TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")

assert TOKEN is not None, "Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"

# --- Auth Provider ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(token=token, client_id="puch-client", scopes=["*"], expires_at=None)
        return None

# --- Rich Tool Description ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None

VIDEO_SUMMARIZER_DESCRIPTION = RichToolDescription(
    description="Summarize a video and answer questions about it using audio transcription.",
    use_when="Use this when the user provides a video URL and asks for a summary or specific insights.",
    side_effects="Downloads and processes video audio locally.",
)

# --- Helper for Base64 encoding ---
def encode_url_if_needed(url: str) -> str:
    if re.match(r"^https?://|^www\.", url):
        return base64.urlsafe_b64encode(url.encode()).decode()
    return url

def check_dependencies():
    missing = []
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
    return missing

# --- MCP Server ---
mcp = FastMCP("Video Summarizer MCP Server", auth=SimpleBearerAuthProvider(TOKEN))

@mcp.tool(description=VIDEO_SUMMARIZER_DESCRIPTION.model_dump_json())
async def video_summarizer(
    video_url: Annotated[str, Field(description="The URL of the video to summarize.")],
    user_question: Annotated[str | None, Field(description="Optional user question about the video content.")] = None
) -> str:
    try:
        # ✅ Only base64 decode if it actually looks encoded
        if re.match(r'^[A-Za-z0-9_-]+={0,2}$', video_url) and not video_url.startswith("http"):
            try:
                video_url = base64.urlsafe_b64decode(video_url).decode()
            except Exception:
                pass  # If decoding fails, just use original

        # ✅ Download audio safely
        audio_path = download_audio_from_url(video_url)
        if not audio_path or not os.path.exists(audio_path):
            return "❌ Failed to download audio. Check if the URL is valid and `yt-dlp` + `ffmpeg` are installed."

        # ✅ Transcribe safely
        transcript = transcribe_audio(audio_path)
        if not transcript:
            return "❌ Failed to transcribe audio."

        # ✅ Summarize + answer
        summary = summarize_transcript(transcript)
        if user_question:
            answer = ask_question_about_transcript(transcript, user_question)
            return f"**Answer**: {answer}\n\n**Summary**:\n\n{summary}"
        else:
            return f"**Summary**:\n\n{summary}"

    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print(f"ERROR in video_summarizer: {err}")
        return f"Tool failed: {e}"


@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# --- Run MCP Server ---
async def main():
    print("🚀 Starting MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())
