
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import ipaddress

app = FastAPI(
    title="Saroj OSINT API",
    description="Public information lookup API",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "name": "Saroj OSINT API",
        "status": "online",
        "features": [
            "Domain format check",
            "IP address check",
            "Username search links"
        ]
    }

@app.get("/domain")
def domain_lookup(name: str):
    name = name.strip().lower().rstrip(".")

    if len(name) > 253 or not re.fullmatch(
        r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",
        name
    ):
        raise HTTPException(400, "Invalid domain format")

    return {
        "domain": name,
        "format_valid": True,
        "note": "This checks format only, not live DNS records."
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

    return {
        "username": name,
        "note": "Search links only; identity is not verified.",
        "links": {
            "Google": "https://www.google.com/search?q=" + name,
            "GitHub": "https://github.com/" + name,
            "Reddit": "https://www.reddit.com/search/?q=" + name
        }
    }
  
