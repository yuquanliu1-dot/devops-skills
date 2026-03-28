# Email Security Standards Reference

## RFC Specifications

### SPF - RFC 7208
- **Purpose**: Sender Policy Framework for Sender Authorization
- **Record Type**: TXT
- **Location**: Domain root (e.g., `example.com`)
- **Format**: `v=spf1 [mechanisms] [qualifier]`

**Mechanisms:**
| Mechanism | Description | Example |
|-----------|-------------|---------|
| `ip4` | IPv4 address/block | `ip4:192.168.1.0/24` |
| `ip6` | IPv6 address/block | `ip6:2001:db8::/32` |
| `a` | A record of domain | `a` or `a:example.com` |
| `mx` | MX records of domain | `mx` |
| `include` | Include another domain's SPF | `include:_spf.google.com` |
| `exists` | Check if domain exists | `exists:%{ir}.spf.example.com` |

**Qualifiers:**
| Qualifier | Meaning | Result |
|-----------|---------|--------|
| `+` | Pass | Allow (default) |
| `-` | Fail | Reject |
| `~` | Soft Fail | Mark but accept |
| `?` | Neutral | No policy |

### DKIM - RFC 6376
- **Purpose**: DomainKeys Identified Mail for Message Signing
- **Record Type**: TXT
- **Location**: `selector._domainkey.domain.com`
- **Format**: `v=DKIM1; k=rsa; p=[public-key]`

**Key Tags:**
| Tag | Description | Example |
|-----|-------------|---------|
| `v` | Version | `v=DKIM1` |
| `k` | Key type | `k=rsa` |
| `p` | Public key | `p=MIGfMA0GCS...` |
| `h` | Hash algorithms | `h=sha256` |
| `s` | Service type | `s=email` |
| `t` | Flags | `t=y` (testing) |

**Signature Header Fields:**
| Tag | Description |
|-----|-------------|
| `d=` | Signing domain |
| `s=` | Selector |
| `a=` | Algorithm (rsa-sha256) |
| `b=` | Signature |
| `bh=` | Body hash |
| `h=` | Signed headers |
| `c=` | Canonicalization |

### DMARC - RFC 7489
- **Purpose**: Domain-based Message Authentication, Reporting, and Conformance
- **Record Type**: TXT
- **Location**: `_dmarc.domain.com`
- **Format**: `v=DMARC1; p=[policy]; [options]`

**Policy Tags:**
| Tag | Description | Values |
|-----|-------------|--------|
| `p` | Policy for domain | `none`, `quarantine`, `reject` |
| `sp` | Policy for subdomains | `none`, `quarantine`, `reject` |
| `pct` | Percentage to apply | `0-100` |
| `adkim` | DKIM alignment | `r` (relaxed), `s` (strict) |
| `aspf` | SPF alignment | `r` (relaxed), `s` (strict) |
| `rua` | Aggregate reports | `mailto:reports@example.com` |
| `ruf` | Forensic reports | `mailto:forensic@example.com` |

## Additional Security Standards

### MTA-STS - RFC 8461
- **Purpose**: SMTP MTA Strict Transport Security
- **Record Type**: TXT
- **Location**: `_mta-sts.domain.com`
- **Format**: `v=STSv1; id=[version]`

**Policy File** (at `https://mta-sts.domain.com/.well-known/mta-sts.txt`):
```
version: STSv1
mode: enforce
mx: mail1.example.com
mx: mail2.example.com
max_age: 604800
```

### TLS-RPT - RFC 8460
- **Purpose**: TLS Reporting
- **Record Type**: TXT
- **Location**: `_smtp._tls.domain.com`
- **Format**: `v=TLSRPTv1; rua=mailto:reports@example.com`

### BIMI - Brand Indicators for Message Identification
- **Purpose**: Display brand logo in email clients
- **Record Type**: TXT
- **Location**: `default._bimi.domain.com`
- **Format**: `v=BIMI1; l=[logo-url]; a=[vmc-url]`

## Best Practices

### SPF Best Practices
1. Use `-all` (hard fail) for production
2. Limit to necessary IP ranges only
3. Avoid `+all` (allows everything) at all costs
4. Use `include:` carefully - trust included domains
5. Keep DNS lookups under 10 (RFC limit)

### DKIM Best Practices
1. Use 2048-bit or larger RSA keys
2. Rotate keys periodically (annually recommended)
3. Use sha256 (not sha1)
4. Sign critical headers (From, Subject, Date)
5. Use relaxed canonicalization for compatibility

### DMARC Best Practices
1. Start with `p=none` to collect data
2. Monitor reports via `rua`
3. Gradually increase to `p=quarantine`
4. Eventually move to `p=reject`
5. Set `pct=100` when confident
6. Use strict alignment (`adkim=s`, `aspf=s`)

### Enterprise Deployment Order
1. **Phase 1**: Deploy SPF with `-all`
2. **Phase 2**: Deploy DKIM signing
3. **Phase 3**: Deploy DMARC with `p=none`
4. **Phase 4**: Monitor reports for 2-4 weeks
5. **Phase 5**: Move to `p=quarantine`
6. **Phase 6**: After validation, move to `p=reject`
7. **Phase 7**: Add MTA-STS and TLS-RPT
8. **Phase 8**: Consider BIMI for brand protection
