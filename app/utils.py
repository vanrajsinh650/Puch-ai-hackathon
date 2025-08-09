def download_audio_from_url(url: str) -> str:
    try:
        import yt_dlp
        import tempfile, os

        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "audio.mp3")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(audio_path):
            raise RuntimeError("Audio download failed — no file found.")

        return audio_path
    except Exception as e:
        print(f"[ERROR] download_audio_from_url failed: {e}")
        return None
