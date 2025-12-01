import asyncio
import edge_tts
import os
import uuid

async def generate_tts_webm(text: str, voice: str = "en-IN-PrabhatNeural", rate: str = "+30%") -> str:
    """
    Generate TTS audio from text using Edge TTS and return the WebM file path.
    'rate' controls speaking speed. Examples: '+20%' faster, '-20%' slower
    """
    # Output folder
    output_folder = "/root/voice_websocket/tts_outputs"
    os.makedirs(output_folder, exist_ok=True)

    # Unique filenames
    file_id = str(uuid.uuid4())
    mp3_path = os.path.join(output_folder, f"{file_id}.mp3")
    webm_path = os.path.join(output_folder, f"{file_id}.webm")

    # Create communicator (pass text normally)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)  # <-- pass rate here

    # Save as MP3
    await communicate.save(mp3_path)

    # Convert to WebM using ffmpeg
    ffmpeg_cmd = f'/usr/bin/ffmpeg -y -i "{mp3_path}" "{webm_path}"'
    result = os.system(ffmpeg_cmd)
    if result != 0:
        raise RuntimeError(f"ffmpeg conversion failed with exit code {result}")

    # Cleanup MP3
    os.remove(mp3_path)

    return webm_path
