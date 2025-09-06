import os
import json
from typing import Dict, Any
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from together import Together
from dotenv import load_dotenv

load_dotenv()


def load_prompt(file_name: str) -> str:
    """Load system prompt from file."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    prompt_path = os.path.join(dir_path, "prompts", f"{file_name}.txt")

    try:
        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Could not find file: {prompt_path}")
        raise


# Configuration
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
NGROK_URL = os.getenv("NGROK_URL")
PORT = int(os.getenv("PORT", 8000))

SYSTEM_MESSAGE = load_prompt("system_prompt_llama")
LLAMA_MODEL = "meta-llama/Llama-3-70b-chat-hf"

app = FastAPI()

if not TOGETHER_API_KEY:
    raise ValueError("Missing Together API key. Please set it in the .env file.")

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
    raise ValueError("Missing Twilio configuration. Please set it in the .env file.")

together_client = Together(api_key=TOGETHER_API_KEY)

conversation_sessions: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "AI Calling Agent (Llama3) is running!"}


class CallRequest(BaseModel):
    to_phone_number: str


@app.post("/make-call")
async def make_call(request: CallRequest):
    """Initiate an outbound call to the specified phone number."""
    if not request.to_phone_number:
        return {"error": "Phone number is required"}
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            url=f"{NGROK_URL}/voice-handler",
            to=request.to_phone_number,
            from_=TWILIO_PHONE_NUMBER,
            record=True,
            recording_status_callback=f"{NGROK_URL}/recording-status",
            recording_status_callback_method="POST"
        )
        print(f"Call initiated with SID: {call.sid}")
        return {"call_sid": call.sid, "status": "success"}
    except Exception as e:
        print(f"Error initiating call: {e}")
        return {"error": str(e), "status": "failed"}


@app.api_route("/voice-handler", methods=["GET", "POST"])
async def handle_voice_interaction(request: Request):
    """Handle voice interactions using Llama3 through Together AI."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    speech_result = form_data.get("SpeechResult", "")
    
    print(f"Call SID: {call_sid}")
    
    if call_sid not in conversation_sessions:
        print(f"New conversation session: {call_sid}")
        conversation_sessions[call_sid] = {
            "conversation_history": [
                {"role": "system", "content": SYSTEM_MESSAGE}
            ]
        }
        
        ai_response = "Hello! Thank you for calling. How can I assist you today?"
    else:
        if speech_result:
            print(f"User said: {speech_result}")
            
            conversation_sessions[call_sid]["conversation_history"].append(
                {"role": "user", "content": speech_result}
            )
            
            ai_response = await generate_llama_response(call_sid)
            
            conversation_sessions[call_sid]["conversation_history"].append(
                {"role": "assistant", "content": ai_response}
            )
        else:
            ai_response = "I didn't catch that. Could you please repeat?"
    
    print(f"AI Response: {ai_response}")
    
    # Create TwiML response
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/voice-handler",
        method="POST",
        enhanced=True,
        speech_model="phone_call",
        speech_timeout="auto",
        timeout=10
    )
    
    gather.say(ai_response, voice="Polly.Joanna")
    response.append(gather)
    
    # Fallback if no input received
    response.say("Thank you for calling. Have a great day!")
    
    return Response(content=str(response), media_type="application/xml")


async def generate_llama_response(call_sid: str) -> str:
    """Generate response using Llama3 through Together AI."""
    try:
        session = conversation_sessions[call_sid]
        
        response = together_client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=session["conversation_history"],
            max_tokens=150,
            temperature=0.3,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1.0
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating Llama response: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again."


@app.api_route("/recording-status", methods=["POST"])
async def handle_recording_status(request: Request):
    """Handle recording status updates from Twilio."""
    form_data = await request.form()
    recording_status = form_data.get("RecordingStatus")
    recording_sid = form_data.get("RecordingSid")
    call_sid = form_data.get("CallSid")
    recording_url = form_data.get("RecordingUrl")
    recording_duration = form_data.get("RecordingDuration")
    
    print(f"Recording status update:")
    print(f"  Call SID: {call_sid}")
    print(f"  Recording SID: {recording_sid}")
    print(f"  Status: {recording_status}")
    
    if recording_status == "completed":
        print(f"  Recording URL: {recording_url}")
        print(f"  Duration: {recording_duration} seconds")
        
        # Clean up session when call ends
        if call_sid in conversation_sessions:
            del conversation_sessions[call_sid]
            print(f"Cleaned up session: {call_sid}")
    
    return {"status": "received"}


@app.on_event("shutdown")
async def cleanup_sessions():
    """Clean up all sessions on shutdown."""
    conversation_sessions.clear()
    print("All conversation sessions cleared")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
