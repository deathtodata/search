# Security Policy

## Reporting a Vulnerability

**Do not open a public issue.**

Email security@death2data.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes

We will respond within 48 hours.

## PGP Key

For sensitive reports, encrypt your email:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
[Key will be published here]
-----END PGP PUBLIC KEY BLOCK-----
```

## Scope

### In Scope

- Authentication bypass
- Token leakage
- Query logging (this would be a critical bug)
- Data exfiltration
- Server compromise vectors

### Out of Scope

- Social engineering
- Physical attacks
- Attacks requiring compromised user devices
- Issues in upstream dependencies (report to them directly)

## Safe Harbor

We consider security research conducted in good faith to be:
- Authorized
- Exempt from legal action
- Helpful to users

We will not pursue legal action against researchers who:
- Act in good faith
- Avoid privacy violations
- Don't destroy data
- Report issues responsibly

## Security Design

### What We Don't Have

The best security is not having sensitive data in the first place.

| Data | We Have It? | Can Be Stolen? |
|------|------------|----------------|
| Search queries | No | No |
| Search results | No | No |
| User emails | No | No |
| Payment info | No | No |
| Token plaintext | No | No |

### What We Have

| Data | Protection |
|------|------------|
| Token hashes | SHA-256, irreversible |
| Login records | Limited retention (90 days) |

### If We're Breached

An attacker who gains full database access obtains:
- Token hashes (cannot reverse to usable tokens)
- Login timestamps, IPs, user agents (limited value)
- **Zero search history** (it doesn't exist)

## Updates

Security updates are announced via:
- GitHub Security Advisories
- Email to security-announce@death2data.com (subscribe: send empty email)

## Bug Bounty

We don't currently offer a paid bug bounty, but we will:
- Credit you publicly (if desired)
- Send you a t-shirt or stickers
- Provide a reference letter

For critical vulnerabilities (e.g., query logging discovered), we will discuss appropriate compensation.
