import whisper
import asyncio

model  = whisper.load_model("base")

def transcribe_audio(file_path: str) -> str:
    return model.transcribe(file_path)["text"]

async def transcribe_audio_async(file_path: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, transcribe_audio, file_path)
