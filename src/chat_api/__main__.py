import os
import uvicorn


def main() -> None:
    host = os.getenv("HOST", "192.168.1.6")
    port_str = os.getenv("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080

    # Runs the Starlette app defined in server.py
    uvicorn.run("src.chat_api.server:app", host=host, port=port, reload=False, factory=False)


if __name__ == "__main__":
    main()


