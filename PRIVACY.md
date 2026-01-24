# Privacy Policy

*Last updated: January 24, 2025*

This is a real privacy policy, not a legal document designed to confuse you.

## The Short Version

- We know you have access (token hash)
- We know when you log in (IP, device, time)
- We don't know what you search (by design, not policy)

## What We Collect

### When You Purchase Access

**We receive from Stripe:**
- Confirmation that payment was successful
- That's it

**We generate:**
- A random access token (shown to you once)
- A SHA-256 hash of that token (stored in our database)

**We do NOT receive:**
- Your email (Stripe has it, we don't)
- Your payment details (Stripe handles this)
- Your name (we don't ask for it)

### When You Log In

**We record:**
- Token hash (so we know which token was used)
- IP address (where the request came from)
- User agent (what browser/device)
- Timestamp (when you logged in)

**We do NOT record:**
- What you're about to search
- What you searched before
- How long you spent searching

### When You Search

**We collect:** Nothing.

This isn't a policy choice. Our code doesn't have the capability to log queries. There's no database table for them. No log file. No analytics.

Verify this yourself:
```bash
docker logs searxng 2>&1 | grep "your search"
sqlite3 data/*.db ".tables"
```

## What We Don't Collect

| Data | Collected? | Why Not? |
|------|------------|----------|
| Search queries | No | Privacy is the point |
| Search results | No | Not our business |
| Email address | No | Stripe has it |
| Name | No | Never asked |
| Location | No | Don't need it |
| Cookies | No | Don't use them |
| Browser fingerprint | No | Don't want it |
| Click behavior | No | Not tracking you |

## How Long We Keep Data

| Data | Retention |
|------|-----------|
| Token hashes | Until access expires |
| Login records | 90 days |
| Search queries | N/A (not collected) |

## Third Parties

### Stripe

Processes payments. They have:
- Your email
- Your payment method
- Your billing address

Their privacy policy: https://stripe.com/privacy

We have: A webhook saying "payment successful."

### Search Engines

SearXNG queries Google, Bing, DuckDuckGo, etc. on your behalf.

They see: Our server's IP address
They don't see: Your IP address, your identity

### Nobody Else

No analytics. No advertising. No social media. No CDNs. No third-party scripts.

Load this page with JavaScript disabled. It works fine.

## Your Rights

### See Your Data

Email privacy@death2data.com with your token. We'll send you:
- Your token hash
- Your login records

We can't send search history because it doesn't exist.

### Delete Your Data

Email privacy@death2data.com with your token. We'll delete:
- Your token hash (you'll lose access)
- All login records for that token

### Export Your Data

Same as "see your data." That's all we have.

## Law Enforcement

If we receive a valid legal request, we can provide:
- Token hash (useless without the token)
- Login records (IP, device, timestamps)

We cannot provide search history because we don't have it.

We will:
- Require valid legal process
- Notify users if legally permitted
- Challenge overly broad requests
- Publish a transparency report annually

## Changes to This Policy

We'll announce changes via:
- This page (date at top will update)
- GitHub commits (full history available)

Major changes will be announced before taking effect.

## Contact

Privacy questions: privacy@death2data.com
General: hello@death2data.com

## Verification

Don't trust this document. Verify the code:

```bash
git clone https://github.com/death2data/search
grep -r "query" --include="*.py" | grep -i "log\|store\|save"
# Should return nothing related to search queries
```
