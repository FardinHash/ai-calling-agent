# AI Calling Agent (Llama3 Version)

A real-time voice AI system that integrates Meta's Llama3 model through Together AI with Twilio Voice to create intelligent voice conversations. This version uses traditional speech-to-text and text-to-speech instead of real-time streaming.

## Features

- **Llama3 Integration** - Powered by Meta's Llama-3-70b-chat-hf model
- **Traditional Voice Flow** - Speech-to-text → AI processing → Text-to-speech
- **Conversation Memory** - Maintains context throughout the call
- **Session Management** - Handles multiple concurrent calls
- **Call Recording** - Automatic recording with status callbacks
- **Production Ready** - Built with FastAPI for scalability

## Quick Start

### Prerequisites

- Python 3.8+
- Together AI API key
- Twilio account (SID, Auth Token, Phone Number)
- ngrok or similar tunneling tool

### Installation

1. **Clone the repository and switch to llama3 branch**

   ```bash
   git clone https://github.com/intellwe/ai-calling-agent.git
   cd ai-calling-agent
   git checkout llama3  # Switch to Llama3 branch
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements-llama.txt
   ```

3. **Configure environment**

   ```bash
   cp .env.example.llama .env
   # Edit .env with your credentials
   ```

4. **Start the server**

   ```bash
   uvicorn main_llama:app --port 8000
   ```

5. **Expose with ngrok**
   ```bash
   ngrok http 8000
   ```

## Configuration

Create a `.env` file with the following variables:

```env
TOGETHER_API_KEY=your_together_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
NGROK_URL=your_ngrok_url
PORT=8000
```

## API Endpoints

| Method | Endpoint            | Description               |
| ------ | ------------------- | ------------------------- |
| GET    | `/`                 | Health check              |
| POST   | `/make-call`        | Initiate outbound call    |
| POST   | `/voice-handler`    | Handle voice interactions |
| POST   | `/recording-status` | Recording status webhook  |

### Making a Call

```bash
curl -X POST "http://localhost:8000/make-call" \
  -H "Content-Type: application/json" \
  -d '{"to_phone_number": "+1234567890"}'
```

## Architecture

```
┌─────────────┐    Speech-to-Text   ┌─────────────┐    API Call    ┌─────────────┐
│   Twilio    │ ──────────────────► │  FastAPI    │ ─────────────► │   Llama3    │
│   Voice     │                     │   Server    │                │ (Together)  │
│             │ ◄────────────────── │             │ ◄───────────── │             │
└─────────────┘   Text-to-Speech    └─────────────┘    Response    └─────────────┘
```

## Differences from OpenAI Version

| Feature              | OpenAI Realtime       | Llama3 Version       |
| -------------------- | --------------------- | -------------------- |
| **Latency**          | Ultra-low (streaming) | Traditional (higher) |
| **Model**            | GPT-4o Realtime       | Llama-3-70b-chat-hf  |
| **Cost**             | Higher                | Lower                |
| **Voice Processing** | Native streaming      | Speech-to-text → TTS |
| **Interruption**     | Real-time             | Turn-based           |

## Development

### Customizing AI Behavior

Edit `prompts/system_prompt_llama.txt` to modify the AI's personality and responses.

### Model Configuration

You can change the Llama model in `main_llama.py`:

```python
LLAMA_MODEL = "meta-llama/Llama-3-70b-chat-hf"  # or other variants
```

Available models:

- `meta-llama/Llama-3-8b-chat-hf` (faster, less capable)
- `meta-llama/Llama-3-70b-chat-hf` (slower, more capable)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

- [@FardinHash](https://github.com/FardinHash) -> [LinkedIn](https://linkedin.com/in/fardinkai)
- [@RianaAzad](https://github.com/RianaAzad) -> [LinkedIn](https://linkedin.com/in/riana-azad)

## Disclaimer

This project is not officially affiliated with Meta, Together AI, or Twilio. Use responsibly and in accordance with their terms of service.

---

⭐ If you find this project helpful, please give it a star!
