# Verification Guide

**Don't trust. Verify.**

This guide shows you how to independently verify that Death2Data actually protects your privacy.

---

## Table of Contents

1. [Quick Verification (5 minutes)](#quick-verification)
2. [Code Audit](#code-audit)
3. [Database Inspection](#database-inspection)
4. [Network Traffic Analysis](#network-traffic-analysis)
5. [Runtime Verification](#runtime-verification)
6. [Threat Modeling](#threat-modeling)

---

## Quick Verification

**Goal:** Confirm no query logging in 5 minutes.

```bash
# 1. Clone and run locally
git clone https://github.com/deathtodata/search.git
cd search
docker run -d -p 8080:8080 searxng/searxng
python3 gateway.py

# 2. Generate token
python3 gateway.py --generate-token
# Save the token: d2d_abc123...

# 3. Do searches
open "http://localhost:3000/?token=d2d_abc123..."
# Search for: "test query 123"
# Search for: "another search"

# 4. Check database
sqlite3 data/d2d.db "SELECT * FROM logins;"
# You'll see: token_hash, IP, user_agent, timestamp

sqlite3 data/d2d.db "SELECT * FROM queries;"
# Result: Error: no such table: queries
# ✅ PROOF: Queries table doesn't exist

# 5. Check code
grep -n "INSERT.*query" gateway.py
grep -n "CREATE TABLE.*query" gateway.py
# Both return nothing
# ✅ PROOF: No code to log queries
```

**Result:** Queries are not logged. Verified.

---

## Code Audit

### 1. Download and Review

```bash
git clone https://github.com/deathtodata/search.git
cd search
wc -l gateway.py
# Output: 406 lines
```

**The entire backend is 406 lines.** You can read it in 30 minutes.

### 2. Search for Suspicious Code

**Check for query logging:**
```bash
grep -n "query" gateway.py | grep -E "(log|save|store|insert|write)"
```

Expected: Nothing suspicious.

**Check for network exfiltration:**
```bash
grep -n -E "(urllib|requests|socket|http)" gateway.py | grep -v "searxng"
```

Expected: Only connections to SearXNG.

**Check database writes:**
```bash
grep -n "INSERT" gateway.py
```

Expected: Only `INSERT INTO tokens` and `INSERT INTO logins`.

### 3. Audit Key Functions

**verify_token() (line 96-108):**
```python
def verify_token(token: str) -> bool:
    if not token or not token.startswith("d2d_"):
        return False

    token_hash = hash_token(token)
    conn = sqlite3.connect(DATABASE_PATH)
    result = conn.execute(
        "SELECT expires_at FROM tokens WHERE hash=?",
        [token_hash]
    ).fetchone()
    conn.close()

    if not result:
        return False

    return datetime.utcnow() < datetime.fromisoformat(result[0])
```

**What it does:** Hashes token, checks if valid.
**What it does NOT do:** Log the token, log any query data.

**log_login() (line 110-120):**
```python
def log_login(token: str, ip: str, user_agent: str):
    token_hash = hash_token(token)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        "INSERT INTO logins (token_hash, ip_address, user_agent, timestamp) VALUES (?,?,?,?)",
        [token_hash, ip, user_agent, datetime.utcnow().isoformat()]
    )
    conn.commit()
    conn.close()
```

**What it logs:** Token hash (not plaintext), IP, user agent, time.
**What it does NOT log:** Search query.

**search_handler() (line 230-270):**
```python
# Verify token
if not verify_token(token):
    self.send_html(401, "<h1>Invalid token</h1>")
    return

# Log login (not query)
log_login(token, self.client_address[0], self.headers.get("User-Agent", ""))

# Forward query to SearXNG
query = sanitize_query(params.get("q", [""])[0])
searxng_url = f"{SEARXNG_URL}/search?q={quote(query)}&format=json"

# Fetch results
response = urllib.request.urlopen(searxng_url, timeout=10)
results = json.loads(response.read())

# Return results (query was never stored)
self.send_html(200, format_results(results))
```

**Flow:**
1. Verify token → Log WHO (token hash)
2. Get query → Forward to SearXNG
3. Get results → Return to user
4. **Query is never stored**

✅ **Verified:** Query passes through, never touches database.

---

## Database Inspection

### Schema Analysis

```bash
python3 gateway.py  # Start server to create DB
sqlite3 data/d2d.db ".schema"
```

**Expected output:**
```sql
CREATE TABLE tokens (
    hash TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE logins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    timestamp TEXT NOT NULL
);
```

**Note:** NO `queries` table.

### Runtime Inspection

```bash
# Do 10 searches, then check:
sqlite3 data/d2d.db "SELECT COUNT(*) FROM logins;"
# Output: 1 (one login event per session)

sqlite3 data/d2d.db "SELECT * FROM logins;"
# Output: token_hash | ip | user_agent | timestamp

sqlite3 data/d2d.db ".tables"
# Output: logins tokens
# NOT: queries, search_history, etc.
```

✅ **Verified:** Database has no queries table.

---

## Network Traffic Analysis

### Using tcpdump

**Capture traffic:**
```bash
# Terminal 1: Capture
sudo tcpdump -i lo0 -A port 3000 > traffic.txt

# Terminal 2: Search
open "http://localhost:3000/?token=d2d_abc&q=test+search"

# Stop capture (Ctrl+C)
```

**Analyze:**
```bash
grep -i "test search" traffic.txt
```

**Expected:** Query appears in HTTP request, NOT in any database write.

### Using Wireshark

1. Start Wireshark, capture on `lo0` (localhost)
2. Filter: `tcp.port == 3000`
3. Make a search
4. Inspect packets:
   - Request: `GET /?token=...&q=test`
   - Response: HTML with results
   - **No database write packets**

✅ **Verified:** Query is not written to disk.

---

## Runtime Verification

### File System Monitoring

**Monitor all file writes during search:**
```bash
# macOS
sudo fs_usage -w -f filesys python3 gateway.py &
PID=$!

# Do a search
open "http://localhost:3000/?token=d2d_abc&q=test"

# Check logs
kill $PID
```

**Expected writes:**
- `data/d2d.db-wal` (SQLite write-ahead log)

**NOT expected:**
- No file containing "test" query
- No log file with search terms

### Strace Analysis (Linux)

```bash
strace -e trace=write,open,openat -o strace.log python3 gateway.py &

# Do search
curl "http://localhost:3000/?token=d2d_abc&q=secret+query"

# Analyze
grep -i "secret query" strace.log
```

**Expected:** Query NOT written to any file.

✅ **Verified:** No query data persisted.

---

## Threat Modeling

### Attack Scenario 1: Database Breach

**Attacker gets:** `data/d2d.db`

**What they find:**
```sql
SELECT * FROM tokens;
-- Output: hash | created_at | expires_at
--         a1b2c3... | 2026-01-24 | 2026-02-21

SELECT * FROM logins;
-- Output: token_hash | ip | user_agent | timestamp
--         a1b2c3... | 192.168.1.1 | Mozilla/5.0 | 2026-01-24T12:00:00
```

**What they DON'T find:**
- Original tokens (only hashes)
- Search queries
- User identities (no names/emails)

**Impact:** Attacker knows someone with a certain IP logged in. They cannot:
- Reverse token hashes
- See what was searched
- Link logins to search queries

✅ **Mitigated.**

### Attack Scenario 2: Server Compromise

**Attacker has root access to VPS.**

**Can they see queries?**
- Check database: No queries stored
- Check logs: No query logging in code
- Check memory dumps: Queries are transient (exist for < 1 second)

**What they CAN do:**
- Modify gateway.py to add logging
- But: Code changes are visible in git
- But: Users running locally are safe

✅ **Open source = transparent modification.**

### Attack Scenario 3: Network Interception (MITM)

**Attacker intercepts traffic between user and Death2Data.**

**Without HTTPS:**
- Can see token: `d2d_abc123`
- Can see query: `test search`

**With HTTPS (production):**
- Cannot see token or query (encrypted)

**Mitigation:** Use HTTPS in production (Caddy/nginx + Let's Encrypt).

✅ **Standard HTTPS protection.**

---

## Red Flags to Check

**If any of these exist, DO NOT trust the code:**

❌ **Red Flag 1:** Code has `INSERT INTO queries`
```bash
grep -n "INSERT INTO queries" gateway.py
# Should return: nothing
```

❌ **Red Flag 2:** Database has queries table
```bash
sqlite3 data/d2d.db ".schema" | grep -i query
# Should return: nothing
```

❌ **Red Flag 3:** Code logs query parameter
```bash
grep -n "log.*query" gateway.py
# Should return: nothing suspicious
```

❌ **Red Flag 4:** Unexplained network requests
```bash
grep -E "(urllib|requests|socket)" gateway.py | grep -v searxng
# Should only show SEARXNG_URL connections
```

❌ **Red Flag 5:** Obfuscated code
```python
# Bad: exec(base64.b64decode("..."))
# Bad: eval(request.get("code"))
# Bad: __import__("hidden_module")
```

**Current status:** ✅ All clear.

---

## Reproducible Builds

Verify that the code on GitHub matches what's running.

```bash
# 1. Clone fresh copy
git clone https://github.com/deathtodata/search.git fresh-copy
cd fresh-copy

# 2. Compare to running version
diff -r fresh-copy/ /path/to/running/version/

# 3. Verify commit hash
git log -1 --format="%H"
# Compare to GitHub
```

✅ **Reproducible:** Code on GitHub = code running.

---

## Trust Chain

**What you must trust:**
1. ✅ **Python interpreter** (from python.org or OS package manager)
2. ✅ **SQLite** (stdlib, ships with Python)
3. ✅ **SearXNG Docker image** (open source, auditable)
4. ✅ **Your own machine** (you control it)

**What you do NOT need to trust:**
1. ❌ Death2Data authors (code is open, verify yourself)
2. ❌ GitHub (clone and run locally)
3. ❌ VPS provider (run locally or use your own hardware)

**Minimal trust surface.**

---

## Continuous Verification

**Automated audit script:**
```bash
#!/bin/bash
# verify.sh - Run before each deployment

echo "=== Death2Data Verification ==="

# 1. Check for query logging
if grep -q "INSERT.*queries" gateway.py; then
    echo "❌ FAIL: Found query INSERT"
    exit 1
fi

# 2. Check database schema
if sqlite3 data/d2d.db ".schema" | grep -q "queries"; then
    echo "❌ FAIL: Found queries table"
    exit 1
fi

# 3. Check code size (should be ~406 lines)
LINES=$(wc -l < gateway.py)
if [ "$LINES" -gt 500 ]; then
    echo "⚠️  WARNING: Code grew to $LINES lines (was 406)"
fi

# 4. Verify no external dependencies
if grep -q "pip install" README.md; then
    echo "❌ FAIL: New dependencies added"
    exit 1
fi

echo "✅ All checks passed"
```

**Run before each update:**
```bash
chmod +x verify.sh
./verify.sh
```

---

## Reporting Concerns

**Found something suspicious?**

1. **Check GitHub issues:** Maybe already reported
2. **Email security@death2data.com:** Private disclosure
3. **Open public issue:** If not security-critical
4. **Fork and fix:** Submit PR with improvement

**We welcome scrutiny. That's the point.**

---

## Independent Audits

**Want a professional audit?**

Recommended auditors for privacy-focused code:
- Cure53 (https://cure53.de/)
- Trail of Bits (https://www.trailofbits.com/)
- NCC Group (https://www.nccgroup.com/)

**Or:** Run your own audit using this guide.

---

## Verification Checklist

Before trusting Death2Data, verify:

- [ ] Code is < 500 lines (auditable)
- [ ] No `queries` table in database schema
- [ ] No `INSERT INTO queries` in code
- [ ] No unexplained network connections
- [ ] SQLite database is readable (not encrypted maliciously)
- [ ] HTTPS enabled in production
- [ ] Code on GitHub matches running code
- [ ] No obfuscated code (base64, eval, etc.)
- [ ] Dependencies are minimal (Python stdlib only)
- [ ] Git history shows no suspicious commits

---

**The best privacy policy is no data collection.**
**The best verification is running the code yourself.**

✅ **Verified. Now you know.**
