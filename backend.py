import os
import sys
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global variables for the MCP session and lifecycle context
mcp_session = None
mcp_client_ctx = None
mcp_connected = False

# List of common stop words to filter out city name candidates
STOP_WORDS = {
    "what", "is", "the", "temperature", "temp", "weather", "in", "of", "for", "how",
    "current", "today", "now", "please", "give", "me", "show", "tell", "any", "city",
    "like", "a", "an", "at", "about", "degree", "celsius", "fahrenheit",
    "hi", "hello", "hey", "greetings", "good", "morning", "afternoon", "evening", "night",
    "forecast", "status", "report", "conditions", "climatology", "degrees", "c", "f",
    "world", "worldwide", "global", "outside", "international", "country", "region",
    "whats", "hows", "currently", "right", "now", "get", "find", "check", "look",
    "hot", "cold", "warm", "cool", "outside", "temperature's", "climate", "humid",
    "raining", "snowing", "sunny", "cloudy", "windy", "today's", "current", "live"
}

def extract_city_candidate(message: str) -> str | None:
    """
    Extracts a potential city name from the user's message.
    It strips punctuation, tokenizes, filters out stop words, and joins the remainder.
    """
    if not message:
        return None

    cleaned = message.strip()
    for char in "?!.,:;()\"'-":
        cleaned = cleaned.replace(char, " ")

    words = cleaned.split()
    candidates = [w for w in words if w.lower() not in STOP_WORDS]

    if not candidates:
        return None

    # Reassemble remaining words — supports multi-word cities like "New York" or "Los Angeles"
    return " ".join(candidates)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_session, mcp_client_ctx, mcp_connected

    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_mcp_server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script]
    )

    logger.info(f"Starting MCP Server subprocess: {sys.executable} {server_script}")

    try:
        mcp_client_ctx = stdio_client(server_params)
        read, write = await mcp_client_ctx.__aenter__()

        mcp_session = ClientSession(read, write)
        await mcp_session.__aenter__()

        await mcp_session.initialize()
        mcp_connected = True
        logger.info("MCP Server successfully started and initialized!")

    except Exception as e:
        logger.error(f"Failed to start or connect to MCP Server: {e}")
        mcp_connected = False

    yield

    logger.info("Shutting down MCP Server connection...")
    try:
        if mcp_session:
            await mcp_session.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"Error during MCP session shutdown: {e}")

    try:
        if mcp_client_ctx:
            await mcp_client_ctx.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"Error during stdio client shutdown: {e}")

    mcp_connected = False
    logger.info("FastAPI application shutdown complete.")

app = FastAPI(lifespan=lifespan)

@app.get("/api/status")
async def get_status():
    return {"connected": mcp_connected}

@app.post("/api/chat")
async def chat(request: Request):
    global mcp_session, mcp_connected

    body = await request.json()
    message = body.get("message", "").strip()

    if not message:
        return JSONResponse(
            content={"type": "text", "text": "Please type a message first!"},
            status_code=400
        )

    if not mcp_connected or mcp_session is None:
        return JSONResponse(
            content={
                "type": "text",
                "text": "The Weather MCP server is currently offline or initializing. Please try again in a few seconds."
            }
        )

    city_candidate = extract_city_candidate(message)

    if not city_candidate:
        return JSONResponse(
            content={
                "type": "text",
                "text": (
                    "Hello! I am your **Global Weather Chatbot** powered by an MCP server.\n\n"
                    "I can fetch live weather for **any city in the world!**\n\n"
                    "Just ask me something like:\n"
                    "- *What is the temperature in Tokyo?*\n"
                    "- *Weather in New York*\n"
                    "- *How hot is Dubai?*\n"
                    "- *Sitamarhi weather*"
                )
            }
        )

    logger.info(f"User message: '{message}'. Extracted city candidate: '{city_candidate}'")

    try:
        # Call the updated global MCP tool
        response = await mcp_session.call_tool(
            "get_city_weather",
            arguments={"city": city_candidate}
        )

        if not response.content or len(response.content) == 0:
            return JSONResponse(
                content={"type": "text", "text": "Sorry, I received an empty response from the weather service."}
            )

        raw_result = response.content[0].text
        weather_result = json.loads(raw_result)

        if "error" in weather_result:
            error_code = weather_result.get("code")
            error_msg = weather_result.get("error")

            if error_code == "CITY_NOT_FOUND":
                reply = f"I couldn't find any city matching **'{city_candidate}'**. Could you double-check the spelling and try again?"
            else:
                reply = f"Oops! {error_msg}"

            return JSONResponse(content={"type": "text", "text": reply})

        return JSONResponse(content={
            "type": "weather",
            "data": weather_result
        })

    except Exception as e:
        logger.error(f"Error calling MCP weather tool: {e}")
        return JSONResponse(
            content={
                "type": "text",
                "text": f"Sorry, there was an issue communicating with the MCP Weather Server: {str(e)}"
            }
        )

@app.get("/")
async def get_index():
    static_index = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return JSONResponse(content={"error": "Frontend assets not found."}, status_code=404)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
