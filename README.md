BRONE-X
========

BRONE-X is a workspace that powers voice, audio, and WhatsApp related tooling.  
This repository is structured as a monorepo-style project containing multiple apps and services.

## Structure

- `src/`: Core source code for BRONE-X services.
- `my-audio-app/`: Audio-related application logic and utilities.
- `whatsapp/`: WhatsApp-related integration or tooling.
- `received_audio/`: Folder for incoming audio artifacts.
- `tts_outputs/`: Folder for generated text-to-speech outputs.
- `agent_venv/`: Python virtual environment for local development (not intended for version control).

## Getting Started

1. **Clone the repository**

   ```bash
   git clone https://github.com/Bhupendra1770/BRONE-X.git
   cd BRONE-X
   ```

2. **Set up Python environment**

   ```bash
   python -m venv agent_venv
   source agent_venv/bin/activate  # On Windows: agent_venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

3. **Run your services**

   Depending on which app or service you want to run (e.g. audio tools, WhatsApp integration),  
   navigate into the appropriate subdirectory and follow its local instructions or entrypoints.

## Development

- Keep the existing frontend and tooling style consistent across new features.
- Use virtual environments to isolate dependencies.
- Avoid committing large generated artifacts in `received_audio/` and `tts_outputs/` unless necessary.

## Contributing

1. Create a feature branch.
2. Make your changes and ensure everything runs locally.
3. Open a pull request on GitHub with a clear description of your changes.

## License

This project is currently proprietary. Update this section if/when you choose a specific open-source license.


