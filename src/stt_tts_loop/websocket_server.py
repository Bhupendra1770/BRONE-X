import asyncio
import websockets
import tempfile
import os
import uuid
import shutil
import base64

from src.stt_tts_loop.transcriber import transcribe_audio
from src.stt_tts_loop.response_generator.simple_mcp_client import initialize_mcp, get_enhanced_response, cleanup_mcp
from src.stt_tts_loop.tts_creator import generate_tts_webm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = "0.0.0.0"
PORT = 8000


async def handle_connection(websocket):
    print("Client connected")

    try:
        async for message in websocket:
            audio_bytes = None

            if isinstance(message, bytes):
                # Raw binary audio
                audio_bytes = message
            elif isinstance(message, str):
                try:
                    # Try base64 decode
                    audio_bytes = base64.b64decode(message)
                    print("Received base64 encoded audio")
                except Exception:
                    print(f"Received non-audio text: {message[:50]}")
                    continue

            if not audio_bytes:
                continue

            # Save audio temporarily
            temp_dir = tempfile.mkdtemp()
            audio_path = os.path.join(temp_dir, f"{uuid.uuid4()}.webm")

            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            print(f"Received audio file: {audio_path}")

            # Step 1: Transcribe
            text = transcribe_audio(audio_path)
            print(f"Transcribed: {text}")

            # Step 2: Get enhanced response using MCP tools
            response_text = await get_enhanced_response(text)
            print(f"Response: {response_text}")

            # Step 3: Convert response to TTS (WebM)
            try:
                tts_path = await generate_tts_webm(response_text)
                print(f"TTS generated: {tts_path}")
            except Exception as e:
                print(f"TTS generation failed: {e}")
                # Send error message back to client
                await websocket.send(f"Error generating audio: {str(e)}".encode())
                continue

            # Step 4: Send audio back to client
            with open(tts_path, "rb") as f:
                await websocket.send(f.read())
            print("Sent audio back to client")

            # Add small delay to ensure WebSocket transmission completes
            await asyncio.sleep(0.1)

            # Cleanup
            os.remove(audio_path)
            if os.path.exists(tts_path):
                os.remove(tts_path)
            shutil.rmtree(temp_dir)

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Client disconnected: {e}")
    except Exception as e:
        print(f"Error: {e}")


async def main():
    # Initialize MCP system
    logger.info("Initializing MCP system...")
    mcp_initialized = await initialize_mcp()
    
    if mcp_initialized:
        logger.info("MCP system initialized successfully")
    else:
        logger.warning("MCP system initialization failed, running in fallback mode")
    
    try:
        async with websockets.serve(handle_connection, HOST, PORT):
            print(f"WebSocket server running on ws://{HOST}:{PORT}")
            print("Ready to process voice messages with MCP tool support!")
            await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    finally:
        # Cleanup MCP resources
        await cleanup_mcp()


if __name__ == "__main__":
    asyncio.run(main())
