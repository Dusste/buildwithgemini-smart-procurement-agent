"""FastAPI proxy & local web server for Smart Procurement Agent.

Supports both local ADK execution and deployed Agent Engine (A2A) execution.
"""

import sys
import os
import uuid
from pathlib import Path

# Enable Vertex AI credentials mode
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Add parent directory to sys.path so app module can be imported
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from app.agent import root_agent

app = FastAPI()

# Local ADK runner instance for local testing
session_service = InMemorySessionService()
local_runner = Runner(agent=root_agent, app_name="smart_procurement_app", session_service=session_service)
_user_sessions = {}

@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )

@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"

    if user_id not in _user_sessions:
        session = await local_runner.session_service.create_session(
            app_name="smart_procurement_app", user_id=user_id
        )
        _user_sessions[user_id] = session.id
        
    session_id = _user_sessions[user_id]
    
    parts = []
    content = types.Content(role="user", parts=[types.Part(text=message)])
    
    agent_text_chunks = []
    a2ui_data_chunks = []
    
    # Async stream turn from local ADK runner
    async for event in local_runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if hasattr(event, "content") and event.content and getattr(event.content, "parts", None):
            for p in event.content.parts:
                if hasattr(p, "text") and p.text:
                    agent_text_chunks.append(p.text)
                elif hasattr(p, "inline_data") and p.inline_data:
                    blob_data = p.inline_data.data
                    if blob_data and b"<a2a_datapart_json>" in blob_data:
                        try:
                            import json
                            raw_str = blob_data.decode("utf-8")
                            clean_str = raw_str.replace("<a2a_datapart_json>", "").replace("</a2a_datapart_json>", "")
                            data_obj = json.loads(clean_str)
                            if "data" in data_obj:
                                a2ui_data_chunks.append(data_obj["data"])
                        except Exception as e:
                            print(f"A2UI parse exception: {e}")

    for a2ui_msg in a2ui_data_chunks:
        parts.append({"kind": "a2ui", "data": a2ui_msg})
        
    if agent_text_chunks and not a2ui_data_chunks:
        full_text = "\n".join(agent_text_chunks)
        parts.append({"kind": "text", "text": full_text})

    if not parts:
        parts = [{"kind": "text", "text": "(Procurement audit complete.)"}]
        
    return JSONResponse({"parts": parts})

# Mount frontend static files
app.mount("/", StaticFiles(directory=os.path.join(Path(__file__).resolve().parent, "static"), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8085)))
