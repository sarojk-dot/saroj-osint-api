import os
import re
import ipaddress
import json
import urllib.request
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(
    title="Saroj OSINT API",
    description="Public information lookup API",
    version="2.0.0"
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def send_message(chat_id, text):
    if not BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()
    except Exception:
        pass


@app.get("/")
def home():
    return {
        "name": "Saroj OSINT API",
        "status": "online",
        "features": ["domain", "ip", "username", "telegram bot"]
    }


@app.get("/domain")
def domain_lookup(name: str):
    name = name.strip().lower().rstrip(".")
    pattern = r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"

    if not re.fullmatch(pattern, name):
        raise HTTPException(400, "Invalid domain format")

    return {
        "domain": name,
        "format_valid": True,
        "note": "Format check only; DNS not checked."
    }


@app.get("/ip")
def ip_lookup(address: str):
    try:
        ip = ipaddress.ip_address(address.strip())
    except ValueError:
        raise HTTPException(400, "Invalid IP address")

    return {
        "ip": str(ip),
        "version": ip.version,
        "is_global": ip.is_global
    }


@app.get("/username")
def username_lookup(name: str):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,30}", name):
        raise HTTPException(400, "Invalid username format")

    from urllib.parse import quote
    q = quote(name)

    return {
        "username": name,
        "note": "Search links only; identity is not verified.",
        "links": {
            "Google": f"https://www.google.com/search?q={q}",
            "GitHub": f"https://github.com/{q}",
            "Reddit": f"https://www.reddit.com/search/?q={q}"
        }
    }


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    message = update.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return {"ok": True}

    parts = text.split(maxsplit=1)
    command = parts[0].split("@")[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if command == "/start":
        reply = (
            "Welcome to Saroj OSINT Bot!\n\n"
            "Commands:\n"
            "/domain example.com\n"
            "/ip 8.8.8.8\n"
            "/username example\n\n"
            "Use public information responsibly."
        )

    elif command == "/domain":
        try:
            result = domain_lookup(arg)
            reply = (
                f"Domain: {result['domain']}\n"
                "Format: Valid\n"
                "Note: Live DNS is not checked."
            )
        except HTTPException:
            reply = "Usage: /domain example.com"

    elif command == "/ip":
        try:
            result = ip_lookup(arg)
            reply = (
                f"IP: {result['ip']}\n"
                f"Version: IPv{result['version']}\n"
                f"Public/global: {result['is_global']}"
            )
        except HTTPException:
            reply = "Usage: /ip 8.8.8.8"

    elif command == "/username":
        try:
            result = username_lookup(arg)
            reply = (
                f"Username: {result['username']}\n"
                "Search links:\n"
                f"Google: {result['links']['Google']}\n"
                f"GitHub: {result['links']['GitHub']}\n"
                f"Reddit: {result['links']['Reddit']}\n\n"
                "These links do not verify identity."
            )
        except HTTPException:
            reply = "Usage: /username example"

    else:
        reply = "Unknown command. Send /start for help."

    send_message(chat_id, reply)
    return {"ok": True}
    
