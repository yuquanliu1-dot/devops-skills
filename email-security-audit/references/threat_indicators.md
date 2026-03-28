# Email Threat Indicators Database

## Header-Based Indicators

### Authentication Failures
| Indicator | Risk | Description |
|-----------|------|-------------|
| SPF fail | High | Sending IP not authorized |
| DKIM fail | High | Signature verification failed |
| DMARC fail | High | Authentication policy violation |
| No SPF record | Medium | Domain has no SPF policy |
| No DKIM signature | Medium | Message not signed |
| `p=none` DMARC | Low | Domain not enforcing policy |

### Domain Mismatches
| Indicator | Risk | Description |
|-----------|------|-------------|
| From ≠ Reply-To | High | Reply goes to different domain |
| From ≠ Return-Path | Medium | Bounce address differs |
| From ≠ Message-ID domain | Medium | Inconsistent message origin |
| From display name ≠ email | Medium | Display name deception |

### Routing Anomalies
| Indicator | Risk | Description |
|-----------|------|-------------|
| >10 Received hops | Medium | Unusual routing complexity |
| Unexpected country in path | Medium | Mail routed through suspicious region |
| X-Originating-IP mismatch | High | IP doesn't match expected location |
| Missing Received headers | Medium | Headers stripped (unusual) |
| TLS not used | Medium | Unencrypted transmission |

### Header Formatting Issues
| Indicator | Risk | Description |
|-----------|------|-------------|
| Malformed Message-ID | Medium | Non-standard format |
| Future/old Date | Medium | Timestamp manipulation |
| Missing required headers | Medium | Incomplete message |
| Duplicate headers | Low | Possible tampering |

## Content-Based Indicators

### Social Engineering Keywords
**Urgency/Pressure:**
- "立即", "urgent", "immediate", "act now"
- "24 hours", "限时", "today only", "expires"
- "最后机会", "last chance", "final notice"

**Threats:**
- "账户将被关闭", "account suspended", "locked"
- "法律行动", "legal action", "lawsuit"
- "罚款", "penalty", "fine"

**Authority:**
- "CEO要求", "executive request"
- "IT部门", "IT department", "helpdesk"
- "法务部", "legal department", "HR"

**Secrecy:**
- "保密", "confidential", "do not share"
- "不要告诉其他人", "keep this private"
- "内部消息", "internal only"

### Request Patterns
| Pattern | Risk | Example |
|---------|------|---------|
| Wire transfer request | Critical | "Please wire $50,000 to..." |
| Gift card purchase | Critical | "Buy Amazon gift cards..." |
| Credential request | High | "Verify your password" |
| Personal info request | High | "Confirm your SSN" |
| Invoice/payment urgency | High | "OVERDUE: Pay immediately" |
| Unusual request from exec | Critical | "I need you to do this ASAP" |

### Link Indicators
| Indicator | Risk | Description |
|-----------|------|-------------|
| URL ≠ display text | High | Hidden destination |
| URL shortener | Medium | bit.ly, tinyurl, etc. |
| IP address URL | High | Direct IP instead of domain |
| Newly registered domain | High | Domain < 30 days old |
| Typosquatting | High | Similar to known brand |
| Suspicious TLD | Medium | .tk, .ml, .xyz, etc. |
| No HTTPS | Medium | Unencrypted connection |
| Redirect parameters | Medium | ?redirect=, &url=, &next= |
| Brand in subdomain | High | login.microsoft.evil.com |
| @ in URL | High | credential@host attack |

### Attachment Indicators
| Extension | Risk | Description |
|-----------|------|-------------|
| .exe, .scr | Critical | Executable files |
| .js, .vbs, .hta | Critical | Script files |
| .bat, .cmd, .ps1 | Critical | Command/batch scripts |
| .zip with .exe inside | Critical | Hidden executable |
| .doc with macros | High | Macro malware |
| .xlsm, .docm | High | Macro-enabled Office |
| .iso, .img | High | Disk image (bypasses filters) |
| .html, .htm attachments | Medium | Local phishing pages |
| .pdf with links | Medium | Embedded malicious links |
| Double extension | Critical | file.pdf.exe pattern |
| Password-protected archive | High | Evades security scanning |

## Known Attack Patterns

### Business Email Compromise (BEC)
```
Characteristics:
- No malware/links (pure social engineering)
- Spoofed or compromised executive email
- Request for wire transfer/gift cards
- Urgency and confidentiality
- "Are you available?" opening
- "Keep this between us"
```

### Credential Harvesting
```
Characteristics:
- Mimics login page (Microsoft 365, Google, banks)
- "Verify your account"
- "Password expiring"
- "Unusual sign-in detected"
- Slight URL variations
- HTTPS with valid cert (doesn't mean safe!)
```

### Invoice/Fraud Scams
```
Characteristics:
- Fake invoice attachment
- "Update our payment details"
- Vendor impersonation
- Urgency to pay
- Slight changes to real invoices
```

### Tech Support Scams
```
Characteristics:
- "Your computer is infected"
- Fake error messages
- Phone number to call
- Remote access request
- Payment for "support"
```

### Sextortion Scams
```
Characteristics:
- Claims of compromising video
- Uses leaked password for "proof"
- Bitcoin payment demand
- Generic, no specific details
- Usually empty threats
```

## Brand Impersonation Targets

### Most Impersonated Brands
1. Microsoft / Microsoft 365
2. Google
3. Amazon
4. PayPal
5. Apple
6. Facebook/Meta
7. Banks (Chase, Bank of America, Wells Fargo)
8. LinkedIn
9. Netflix
10. IRS / Tax authorities

### Impersonation Techniques
- Typosquatting: `micr0soft.com`, `g00gle.com`
- Homograph attacks: Cyrillic characters
- Subdomain deception: `microsoft.com.phishing.com`
- Display name only: "Microsoft Support" <evil@bad.com>

## Red Flags Checklist

```
□ SPF/DKIM/DMARC failed or missing
□ From/Reply-To domain mismatch
□ Urgent/threatening language
□ Request for credentials/payment
□ Suspicious links (hover to check)
□ Unexpected attachments
□ Sender you don't normally communicate with
□ Request seems unusual for sender's role
□ Pressure to act immediately
□ Poor grammar/spelling (though AI phishing is improving)
□ Generic greeting ("Dear Customer")
□ Email signature doesn't match company branding
□ Request bypasses normal procedures
```
