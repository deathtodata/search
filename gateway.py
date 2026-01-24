#!/usr/bin/env python3
"""
Death2Data Gateway

This is the ENTIRE backend. One file. Easy to audit.

What it does:
- Verifies tokens (hash check)
- Logs logins (IP, device, time)
- Forwards searches to SearXNG

What it does NOT do:
- Log queries (there's no code for it)
- Store results (they pass through)
- Track users (no profiles)

Audit this file. Verify the claims.
"""

import hashlib
import secrets
import sqlite3
import os
import json
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import urllib.request

# Configuration
SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://localhost:8888")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "./data/d2d.db")
PORT = int(os.environ.get("PORT", "3000"))
LOGIN_RETENTION_DAYS = 90

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def init_database():
    """Initialize the database. Note: NO QUERIES TABLE."""
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    
    # Tokens table - stores ONLY hashes
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            hash TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)
    
    # Logins table - WHO logged in, not WHAT they searched
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    
    # NOTE: There is NO queries table.
    # This is intentional. We do not log queries.
    
    conn.commit()
    conn.close()

def hash_token(token: str) -> str:
    """SHA-256 hash of token. One-way function."""
    return hashlib.sha256(token.encode()).hexdigest()

def generate_token() -> tuple[str, str]:
    """Generate a new token. Returns (plaintext, hash)."""
    # 24 random bytes = 192 bits of entropy
    random_bytes = secrets.token_urlsafe(24)
    token = f"d2d_{random_bytes}"
    token_hash = hash_token(token)
    
    # Store only the hash
    conn = sqlite3.connect(DATABASE_PATH)
    now = datetime.utcnow()
    expires = now + timedelta(days=28)
    conn.execute(
        "INSERT INTO tokens (hash, created_at, expires_at) VALUES (?, ?, ?)",
        [token_hash, now.isoformat(), expires.isoformat()]
    )
    conn.commit()
    conn.close()
    
    # Return plaintext (shown once) and hash
    return token, token_hash

def verify_token(token: str) -> bool:
    """Check if token hash exists and is not expired."""
    if not token or not token.startswith("d2d_"):
        return False
    
    token_hash = hash_token(token)
    conn = sqlite3.connect(DATABASE_PATH)
    row = conn.execute(
        "SELECT expires_at FROM tokens WHERE hash = ?",
        [token_hash]
    ).fetchone()
    conn.close()
    
    if not row:
        return False
    
    expires = datetime.fromisoformat(row[0])
    return datetime.utcnow() < expires

def log_login(token: str, ip: str, user_agent: str):
    """Log that a login occurred. Does NOT log what they searched."""
    token_hash = hash_token(token)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        "INSERT INTO logins (token_hash, ip_address, user_agent, timestamp) VALUES (?, ?, ?, ?)",
        [token_hash, ip, (user_agent or "")[:200], datetime.utcnow().isoformat()]
    )
    conn.commit()
    conn.close()

def cleanup_old_logins():
    """Remove login records older than retention period."""
    conn = sqlite3.connect(DATABASE_PATH)
    cutoff = (datetime.utcnow() - timedelta(days=LOGIN_RETENTION_DAYS)).isoformat()
    conn.execute("DELETE FROM logins WHERE timestamp < ?", [cutoff])
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
# HTTP SERVER
# ═══════════════════════════════════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):
    """HTTP request handler. Audit this code."""
    
    def log_message(self, format, *args):
        """Override to prevent default logging."""
        # We log logins to database, not to stdout
        # We do NOT log queries anywhere
        pass
    
    def send_html(self, status: int, html: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_client_ip(self) -> str:
        """Get client IP, respecting X-Forwarded-For if behind proxy."""
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0]
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path
        
        # Get token from query param or header
        token = params.get("token", [None])[0]
        if not token:
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:]
        
        # ─────────────────────────────────────────────────────────────
        # HOME - show login or search
        # ─────────────────────────────────────────────────────────────
        if path == "/":
            if token and verify_token(token):
                # Log the login (NOT the query - there isn't one yet)
                log_login(token, self.get_client_ip(), self.headers.get("User-Agent"))
                self.send_html(200, self.search_page(token))
            else:
                self.send_html(200, self.landing_page())
            return
        
        # ─────────────────────────────────────────────────────────────
        # SEARCH - the core functionality
        # ─────────────────────────────────────────────────────────────
        if path == "/search":
            query = params.get("q", [""])[0]
            
            # Verify token
            if not verify_token(token):
                self.send_html(401, self.unauthorized_page())
                return
            
            # Log the login (WHO searched, not WHAT)
            # NOTE: We do NOT log `query` anywhere
            log_login(token, self.get_client_ip(), self.headers.get("User-Agent"))
            
            if not query:
                self.send_html(200, self.search_page(token))
                return
            
            # Forward to SearXNG
            # The query goes to SearXNG, which has logging disabled
            # The query is NOT stored anywhere by us
            try:
                url = f"{SEARXNG_URL}/search?q={quote(query)}&format=json"
                with urllib.request.urlopen(url, timeout=15) as response:
                    results = json.loads(response.read())
                
                self.send_html(200, self.results_page(token, query, results))
            except Exception as e:
                self.send_html(500, f"Search error: {e}")
            return
        
        # ─────────────────────────────────────────────────────────────
        # HEALTH CHECK
        # ─────────────────────────────────────────────────────────────
        if path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        
        # ─────────────────────────────────────────────────────────────
        # 404
        # ─────────────────────────────────────────────────────────────
        self.send_html(404, "Not found")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HTML TEMPLATES (inline, no external dependencies)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def landing_page(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Death2Data - Private Search</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        h1 { font-weight: normal; }
        input { padding: 10px; font-size: 16px; width: 100%; margin: 10px 0; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
        .muted { color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <h1>Death2Data</h1>
    <p>Private search. We know who you are. We don't know what you search.</p>
    <form action="/" method="GET">
        <input type="text" name="token" placeholder="Enter your access token">
        <button type="submit">Access Search</button>
    </form>
    <p class="muted">No token? <a href="https://buy.stripe.com/XXXXX">Get access for $1</a></p>
</body>
</html>"""
    
    def search_page(self, token: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search - Death2Data</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        input {{ padding: 15px; font-size: 18px; width: 100%; border: 1px solid #ccc; }}
        input:focus {{ outline: 2px solid #005a9c; }}
    </style>
</head>
<body>
    <form action="/search" method="GET">
        <input type="hidden" name="token" value="{token}">
        <input type="text" name="q" placeholder="Search privately..." autofocus>
    </form>
</body>
</html>"""
    
    def results_page(self, token: str, query: str, results: dict) -> str:
        items = results.get("results", [])[:20]
        results_html = ""
        for item in items:
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("content", "")[:200]
            results_html += f"""
            <div style="margin-bottom: 20px;">
                <a href="{url}" style="font-size: 18px;">{title}</a>
                <div style="color: #006621; font-size: 13px;">{url[:60]}</div>
                <p style="color: #666; margin: 5px 0;">{content}</p>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{query} - Death2Data</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 700px; margin: 20px auto; padding: 20px; }}
        input {{ padding: 10px; font-size: 16px; width: 100%; margin-bottom: 20px; }}
        a {{ color: #1a0dab; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <form action="/search" method="GET">
        <input type="hidden" name="token" value="{token}">
        <input type="text" name="q" value="{query}">
    </form>
    {results_html}
</body>
</html>"""
    
    def unauthorized_page(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Unauthorized - Death2Data</title>
</head>
<body>
    <h1>Unauthorized</h1>
    <p>Invalid or expired token. <a href="/">Go back</a></p>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    init_database()
    cleanup_old_logins()
    
    # CLI commands
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--generate-token":
            token, token_hash = generate_token()
            print(f"\nToken: {token}")
            print(f"Hash:  {token_hash}")
            print(f"\nGive the token to the user. We only stored the hash.\n")
            sys.exit(0)
        
        elif cmd == "--show-logins":
            conn = sqlite3.connect(DATABASE_PATH)
            rows = conn.execute(
                "SELECT token_hash, ip_address, user_agent, timestamp FROM logins ORDER BY id DESC LIMIT 50"
            ).fetchall()
            conn.close()
            print("\nRecent logins (WHO, not WHAT):\n")
            for row in rows:
                print(f"  {row[3]} | {row[1]} | {row[0][:16]}... | {row[2][:40]}")
            print()
            sys.exit(0)
        
        elif cmd == "--help":
            print("""
Death2Data Gateway

Usage:
    python gateway.py                    Start the server
    python gateway.py --generate-token   Generate a new access token
    python gateway.py --show-logins      Show recent login records
    python gateway.py --help             Show this help

Environment variables:
    SEARXNG_URL     URL of SearXNG instance (default: http://localhost:8888)
    DATABASE_PATH   Path to SQLite database (default: ./data/d2d.db)
    PORT            Port to listen on (default: 3000)
""")
            sys.exit(0)
    
    # Start server
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║  Death2Data Gateway                                           ║
╠═══════════════════════════════════════════════════════════════╣
║  Server:    http://localhost:{PORT:<37}║
║  SearXNG:   {SEARXNG_URL:<48}║
║  Database:  {DATABASE_PATH:<48}║
╠═══════════════════════════════════════════════════════════════╣
║  What we log:     Logins (token hash, IP, device, time)       ║
║  What we DON'T:   Search queries (NEVER)                      ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutdown.")
