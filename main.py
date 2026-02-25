from fastapi import FastAPI, Request, Query, HTTPException
import uvicorn
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ── Load from .env ──────────────────────────────────────────────
# ACCESS_TOKEN     = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "EAAU4n6sTZBO0BQ3zbmsnZBJFSSzWip7tqHi5BUQgiCkR8slWHSyig7ui6KAbYwUqYc6pjtHdnDt7HGhjhgezhZBnbr95DDZB6mL74q4bD6jzF2ydz76pzCOrj7Y4aNz5IVkOBnXnCOjWlIAAmgUGBrNFB3A22dBoWBLHsbrqrT3YoKtipGsBsxMwQS2opqZBg9wZDZD")
PHONE_NUMBER_ID  = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN     = os.getenv("VERIFY_TOKEN", "fastpeer123")
API_VERSION      = os.getenv("API_VERSION", "v22.0")

WA_URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"


# ── 1. Root health check ────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "FastPeer WhatsApp Bot is running ✅"}


# ── 2. Webhook Verification (Meta calls this once to verify) ────
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    print(f"[VERIFY] mode={hub_mode}, token={hub_verify_token}")

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("[VERIFY] ✅ Webhook verified successfully!")
        return int(hub_challenge)   # Must return challenge as integer

    print("[VERIFY] ❌ Verification failed — token mismatch")
    raise HTTPException(status_code=403, detail="Verification failed")


# ── 3. Receive Incoming WhatsApp Messages ───────────────────────
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print(f"[INCOMING] {data}")   # prints full payload in your terminal

    try:
        entry   = data["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

        # Ignore delivery/read status updates — only process real messages
        if "messages" not in value:
            return {"status": "ignored"}

        message   = value["messages"][0]
        sender    = message["from"]          # e.g. 917008857139
        msg_type  = message.get("type", "")

        if msg_type == "text":
            user_text = message["text"]["body"].strip().lower()
            print(f"[MSG] From: {sender} | Text: {user_text}")

            # ── Your core logic ──
            if user_text == "agents":
                reply = get_agents_reply()
            else:
                reply = "👋 Welcome! Send *agents* to get started."

            await send_message(sender, reply)

    except (KeyError, IndexError) as e:
        print(f"[ERROR] Could not parse webhook: {e}")

    # Always return 200 to Meta — or it will keep retrying
    return {"status": "ok"}


# ── 4. Send a WhatsApp message via Meta API ─────────────────────
async def send_message(to: str, text: str):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(WA_URL, json=payload, headers=headers)
        print(f"[SEND] Status: {response.status_code} | Response: {response.text}")
        return response.json()


# ── 5. Your business logic ──────────────────────────────────────
def get_agents_reply() -> str:
    """
    This is where you put your real logic.
    Fetch from DB, call another API, etc.
    For now it returns a hardcoded welcome message.
    """
    return (
        "👋 *Welcome to FastPeer!*\n\n"
        "🤖 Our agents are ready to help you.\n\n"
        "Here's what I can do:\n"
        "• Help you find the right agent\n"
        "• Answer your queries instantly\n"
        "• Connect you with support\n\n"
        "Reply with your question and we'll get back to you shortly! ✅"
    )


# ── Run server ──────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=5000, reload=True)