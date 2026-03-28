#!/usr/bin/env python3
"""
DNS Security Records Checker - Check email security DNS records for a domain

Usage:
    python check_dns_records.py --domain example.com
    python check_dns_records.py --domain example.com --verbose
"""

import argparse
import subprocess
import sys
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RecordCheck:
    """DNS record check result"""
    record_type: str
    found: bool
    value: Optional[str]
    status: str  # 'good', 'warning', 'error', 'missing'
    recommendation: str


def run_dig(domain: str, record_type: str, prefix: str = "") -> Tuple[bool, str]:
    """Run dig command and return result"""
    if prefix:
        fqdn = f"{prefix}.{domain}"
    else:
        fqdn = domain

    try:
        result = subprocess.run(
            ['dig', record_type, fqdn, '+short'],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout.strip()
        return bool(output), output
    except FileNotFoundError:
        # dig not available, try nslookup
        try:
            result = subprocess.run(
                ['nslookup', '-type=' + record_type, fqdn],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout
            # Parse nslookup output
            if 'text =' in output.lower() or record_type.upper() + ' record' in output.upper():
                lines = output.split('\n')
                text_lines = [l for l in lines if 'text =' in l.lower() or 'txt' in l.lower()]
                return bool(text_lines), '\n'.join(text_lines)
            return False, ""
        except Exception as e:
            return False, f"Error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_spf(domain: str) -> RecordCheck:
    """Check SPF record"""
    found, value = run_dig(domain, 'TXT')

    if not found:
        return RecordCheck(
            record_type="SPF",
            found=False,
            value=None,
            status="error",
            recommendation="Add SPF record to authorize sending servers"
        )

    # Look for SPF record in TXT responses
    spf_record = None
    for line in value.split('\n'):
        if 'v=spf1' in line.lower():
            spf_record = line.strip('"')
            break

    if not spf_record:
        return RecordCheck(
            record_type="SPF",
            found=False,
            value=None,
            status="error",
            recommendation="No SPF record found. Add v=spf1 TXT record"
        )

    # Analyze SPF record
    status = "good"
    recommendation = ""

    if '+all' in spf_record:
        status = "error"
        recommendation = "CRITICAL: '+all' allows ANY server to send. Use '-all' instead"
    elif '?all' in spf_record:
        status = "warning"
        recommendation = "'?all' provides no enforcement. Consider using '~all' or '-all'"
    elif '~all' in spf_record:
        status = "warning"
        recommendation = "SPF soft fail. Consider moving to '-all' for full enforcement"
    elif '-all' in spf_record:
        status = "good"
        recommendation = "SPF properly configured with hard fail"

    return RecordCheck(
        record_type="SPF",
        found=True,
        value=spf_record,
        status=status,
        recommendation=recommendation
    )


def check_dkim(domain: str, selectors: List[str] = None) -> RecordCheck:
    """Check DKIM record"""
    if selectors is None:
        selectors = ['default', 'selector1', 'selector2', 'k1', 'k2', 'google', 'mail']

    for selector in selectors:
        found, value = run_dig(domain, 'TXT', f"{selector}._domainkey")

        if found and 'v=DKIM' in value.upper():
            return RecordCheck(
                record_type="DKIM",
                found=True,
                value=f"Selector '{selector}': {value[:100]}...",
                status="good",
                recommendation="DKIM record found. Verify signature is being used for outgoing mail"
            )

    return RecordCheck(
        record_type="DKIM",
        found=False,
        value=None,
        status="warning",
        recommendation="No DKIM record found with common selectors. Verify your DKIM selector name"
    )


def check_dmarc(domain: str) -> RecordCheck:
    """Check DMARC record"""
    found, value = run_dig(domain, 'TXT', '_dmarc')

    if not found:
        return RecordCheck(
            record_type="DMARC",
            found=False,
            value=None,
            status="error",
            recommendation="Add DMARC record at _dmarc.{domain}"
        )

    # Parse DMARC record
    dmarc_record = None
    for line in value.split('\n'):
        if 'v=DMARC1' in line.upper():
            dmarc_record = line.strip('"')
            break

    if not dmarc_record:
        return RecordCheck(
            record_type="DMARC",
            found=False,
            value=None,
            status="error",
            recommendation="No valid DMARC record found"
        )

    # Analyze DMARC policy
    status = "good"
    recommendation = ""

    if 'p=none' in dmarc_record.lower():
        status = "warning"
        recommendation = "DMARC in monitoring mode (p=none). Move to p=quarantine, then p=reject"
    elif 'p=quarantine' in dmarc_record.lower():
        status = "warning"
        recommendation = "DMARC quarantine policy. Consider moving to p=reject for full enforcement"
    elif 'p=reject' in dmarc_record.lower():
        status = "good"
        recommendation = "DMARC properly configured with reject policy"

    return RecordCheck(
        record_type="DMARC",
        found=True,
        value=dmarc_record,
        status=status,
        recommendation=recommendation
    )


def check_mta_sts(domain: str) -> RecordCheck:
    """Check MTA-STS record"""
    found, value = run_dig(domain, 'TXT', '_mta-sts')

    if not found or 'v=STSv1' not in value.upper():
        return RecordCheck(
            record_type="MTA-STS",
            found=False,
            value=None,
            status="warning",
            recommendation="Consider adding MTA-STS to enforce TLS for incoming mail"
        )

    return RecordCheck(
        record_type="MTA-STS",
        found=True,
        value=value.strip('"'),
        status="good",
        recommendation="MTA-STS record configured"
    )


def check_tls_rpt(domain: str) -> RecordCheck:
    """Check TLS Reporting record"""
    found, value = run_dig(domain, 'TXT', '_smtp._tls')

    if not found or 'v=TLSRPTv1' not in value.upper():
        return RecordCheck(
            record_type="TLS-RPT",
            found=False,
            value=None,
            status="info",
            recommendation="Consider adding TLS-RPT for TLS failure reporting"
        )

    return RecordCheck(
        record_type="TLS-RPT",
        found=True,
        value=value.strip('"'),
        status="good",
        recommendation="TLS-RPT configured for reporting"
    )


def print_status_icon(status: str) -> str:
    """Return status icon"""
    icons = {
        'good': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️',
        'missing': '❓'
    }
    return icons.get(status, '❓')


def print_report(domain: str, checks: List[RecordCheck], verbose: bool = False):
    """Print security audit report"""
    print("\n" + "="*60)
    print(f"EMAIL SECURITY DNS AUDIT: {domain}")
    print("="*60)

    # Summary
    good = sum(1 for c in checks if c.status == 'good')
    warnings = sum(1 for c in checks if c.status == 'warning')
    errors = sum(1 for c in checks if c.status == 'error')

    print(f"\n📊 Summary: {good} ✅ | {warnings} ⚠️ | {errors} ❌")

    print("\n📋 Record Details:")
    print("-"*60)

    for check in checks:
        icon = print_status_icon(check.status)
        print(f"\n{icon} {check.record_type}")
        print(f"   Status: {check.status.upper()}")

        if check.found and verbose:
            print(f"   Value: {check.value[:80]}..." if len(str(check.value)) > 80 else f"   Value: {check.value}")

        if check.recommendation:
            print(f"   📝 {check.recommendation}")

    print("\n" + "="*60)

    # Security maturity
    if errors == 0 and warnings <= 1:
        print("🎯 Security Maturity: HIGH")
    elif errors <= 1:
        print("🎯 Security Maturity: MEDIUM")
    else:
        print("🎯 Security Maturity: LOW - Immediate action recommended")

    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Check email security DNS records')
    parser.add_argument('--domain', type=str, required=True, help='Domain to check')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show record values')
    parser.add_argument('--selectors', type=str, help='Comma-separated DKIM selectors to check')
    args = parser.parse_args()

    print(f"\n🔍 Scanning DNS records for: {args.domain}")

    selectors = None
    if args.selectors:
        selectors = [s.strip() for s in args.selectors.split(',')]

    # Run all checks
    checks = [
        check_spf(args.domain),
        check_dkim(args.domain, selectors),
        check_dmarc(args.domain),
        check_mta_sts(args.domain),
        check_tls_rpt(args.domain),
    ]

    print_report(args.domain, checks, args.verbose)

    # Exit with error if critical issues
    if any(c.status == 'error' for c in checks):
        sys.exit(1)


if __name__ == '__main__':
    main()
