# Death2Data Search

> **Search privately. No tracking. No logs. Verify it yourself.**

Death2Data is a privacy-first search engine that aggregates results from 70+ search engines through SearXNG. Your queries are never logged. Your searches can't be linked to you. The code is open - audit it yourself.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Code Size](https://img.shields.io/github/languages/code-size/deathtodata/search)](https://github.com/deathtodata/search)

---

## The Problem

Every search you make is tracked, profiled, and sold:
- Google knows everything you search
- Your ISP sees every query
- Ad networks build profiles on you
- Your search history never truly disappears

## The Solution

```
You → Death2Data → SearXNG → 70+ Search Engines
           ↓
      tokens.db (hashes only, no queries)
      logins.db (WHO logged in, not WHAT they searched)
```

**What we know:** You have access (token hash), when you logged in
**What we DON'T know:** What you search, what results you click, anything about your queries

This isn't a privacy policy promise. It's architectural - **there's no code to log your queries.**

---

## Quick Start

### Run Locally (5 minutes)

```bash
# 1. Start SearXNG (the meta-search engine)
docker run -d -p 8080:8080 --name searxng searxng/searxng

# 2. Run Death2Data gateway
python3 gateway.py

# 3. Generate your token
python3 gateway.py --generate-token
# Output: Token: d2d_abc123...

# 4. Search
open "http://localhost:3000/?token=d2d_abc123..."
```

That's it. You're searching privately.

---

## Features

### Zero Query Logging
Your searches aren't stored. Not hashed. Not encrypted. **Not collected.**

Verify it yourself:
```bash
# Check the code - no query logging
grep -r "query" gateway.py | grep -i "log\|store\|save"
# Returns nothing

# Check the database schema
sqlite3 data/d2d.db ".schema"
# No queries table exists
```

### Token-Based Access
No accounts. No passwords. No email. Just tokens.

```python
# How tokens work:
token = "d2d_abc123..."           # You have this
token_hash = sha256(token)        # We store this

# If someone steals our database:
#   They get: hashes
#   They can't get: original tokens
#   Useless to attackers
```

### What We Collect

| Data | Collected | Why |
|------|-----------|-----|
| Search queries | ❌ Never | Privacy is the point |
| Search results | ❌ Never | Not our business |
| Token (plaintext) | ❌ Never | Only hashed |
| Token hash | ✅ Yes | Verify access |
| Login IP/time | ✅ Yes | Abuse prevention |

See [PRIVACY.md](PRIVACY.md) for full details.

---

## How It Works

### Architecture

```
┌─────────────┐
│     YOU     │
└──────┬──────┘
       │ token=d2d_abc123
       ▼
┌────────────────────┐
│  Death2Data Server │
│  (gateway.py)      │
├────────────────────┤
│ 1. Hash token      │
│ 2. Check DB        │
│ 3. Log login       │─────► logins.db (IP, time)
│ 4. Forward query   │─────► ✗ NO query logging
└────────┬───────────┘
         │
         ▼
┌─────────────────────┐
│     SearXNG         │
│  (Meta-searcher)    │
├─────────────────────┤
│ Queries 70+ engines │
│ - Google            │
│ - Bing              │
│ - DuckDuckGo        │
│ - Wikipedia         │
│ - ...               │
└────────┬────────────┘
         │
         ▼
┌────────────────────┐
│     Results        │
│  (back to you)     │
└────────────────────┘
```

### What Gets Logged

**Login event (one-time per session):**
```
{
  "token_hash": "a1b2c3...",
  "ip": "203.0.113.42",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2026-01-24T12:00:00Z"
}
```

**Search query:**
```
Nothing. Passes through. Not stored.
```

---

## Self-Hosting

### Option 1: Docker Compose (Easiest)

```bash
git clone https://github.com/deathtodata/search.git
cd search
docker-compose up -d
```

Access at `http://localhost:3000`

### Option 2: Manual Setup

```bash
# 1. Install SearXNG
docker run -d -p 8080:8080 searxng/searxng

# 2. Run gateway
python3 gateway.py

# 3. Generate tokens
python3 gateway.py --generate-token
```

### Option 3: VPS Deployment

See [DEPLOY.md](DEPLOY.md) for detailed production deployment guide.

---

## Verification

Don't trust us. Verify the privacy claims yourself.

### 1. Check the Code

```bash
git clone https://github.com/deathtodata/search.git
cd search
wc -l gateway.py
# 406 lines - audit the entire backend in minutes
```

### 2. Check for Query Logging

```bash
grep -n "query" gateway.py
# Look for any log/store/save operations
# You won't find any
```

### 3. Check the Database Schema

```bash
python3 gateway.py  # Start server
sqlite3 data/d2d.db ".schema"
```

Output:
```sql
CREATE TABLE tokens (hash TEXT PRIMARY KEY, created_at TEXT, expires_at TEXT);
CREATE TABLE logins (id INTEGER PRIMARY KEY, token_hash TEXT, ip_address TEXT, user_agent TEXT, timestamp TEXT);
-- Note: NO queries table
```

### 4. Run and Monitor

```bash
# Start with logging
docker-compose up

# Do searches, then:
docker logs searxng | grep "your search term"
# Returns nothing
```

See [VERIFY.md](VERIFY.md) for comprehensive audit guide.

---

## Documentation

- **[PRIVACY.md](PRIVACY.md)** - What we collect and why (short version: almost nothing)
- **[DEPLOY.md](DEPLOY.md)** - Self-hosting and production deployment
- **[VERIFY.md](VERIFY.md)** - How to audit the privacy claims
- **[SECURITY.md](SECURITY.md)** - Security disclosures and hardening
- **[SPECIFICATION.txt](SPECIFICATION.txt)** - RFC-style technical specification

---

## Token Management

### Generate Token

```bash
python3 gateway.py --generate-token
```

Output:
```
Token: d2d_abc123...
Hash: a1b2c3d4e5...
Expires: 2026-02-21
```

**Save the token!** It's only shown once.

### Invite Users

Send them:
1. The URL: `https://search.yourdomain.com`
2. Their token: `d2d_abc123...`
3. Instructions: Add `?token=d2d_abc123...` to URL

### Revoke Token

```bash
# Connect to database
sqlite3 data/d2d.db

# Find token hash
SELECT * FROM tokens WHERE hash LIKE 'a1b2%';

# Delete it
DELETE FROM tokens WHERE hash = 'a1b2c3...';
```

---

## FAQ

**Q: Why do you log logins if privacy is the goal?**
A: Abuse prevention. We need to know if one token is making 10,000 searches/minute. We log WHO (token hash, IP), not WHAT (queries).

**Q: Can you see my searches?**
A: No. They pass through our server to SearXNG without being logged. Check the code.

**Q: What if you're lying?**
A: Audit the code. It's 406 lines. Run it locally. Check the database. See for yourself.

**Q: Why not just use DuckDuckGo?**
A: DDG says they don't log. Death2Data proves it (open source, auditable).

**Q: Why MIT license instead of AGPL?**
A: Freedom. Fork it, modify it, host it commercially. We trust you to give credit.

**Q: Can I use this commercially?**
A: Yes (MIT license). Just include the copyright notice.

**Q: How do you make money?**
A: Hosted service ($5/month), enterprise support ($100/month). Code is free.

---

## Contributing

We accept contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

Areas we need help:
- Security audits
- Documentation improvements
- UI/UX enhancements
- Translation (multi-language support)
- Performance optimization

---

## Security

Found a security issue? Email security@death2data.com or see [SECURITY.md](SECURITY.md).

We take security seriously:
- Responsible disclosure (90 days)
- Public acknowledgment (with permission)
- Rapid patching (24-48 hours)

---

## License

MIT License - see [LICENSE](LICENSE)

You're free to:
- Use commercially
- Modify and distribute
- Host your own instance
- Fork and rebrand

Just include the copyright notice.

---

## Links

- **Website:** https://death2data.com
- **GitHub:** https://github.com/deathtodata/search
- **Docs:** https://docs.death2data.com
- **Status:** https://status.death2data.com

---

## Comparison

| Feature | Death2Data | Google | DuckDuckGo |
|---------|-----------|--------|-----------|
| Open source code | ✅ Yes | ❌ No | ❌ No |
| Zero query logging | ✅ Yes | ❌ No | ⚠️ Claims yes |
| Auditable | ✅ 406 lines | ❌ Proprietary | ❌ Proprietary |
| Self-hostable | ✅ Yes | ❌ No | ❌ No |
| No accounts | ✅ Yes | ❌ Requires account | ✅ Yes |
| Ad-free | ✅ Yes | ❌ No | ⚠️ Affiliate links |

---

## Philosophy

Inspired by:
- **Signal** - Privacy through architecture, not policy
- **Tor** - Anonymity through routing
- **SearXNG** - Meta-search aggregation

Core principle: **Can't leak what we don't have.**

If we don't collect your queries, we can't:
- Leak them in a breach
- Sell them to advertisers
- Hand them to governments
- Lose them in a hack

Privacy by design, not by promise.

---

**Search privately. Verify independently. Host yourself.**
