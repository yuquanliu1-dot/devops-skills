#!/usr/bin/env python3
"""
Email Header Analyzer - Analyze email headers for security issues

Usage:
    python analyze_email.py --header "paste-headers-here"
    python analyze_email.py --file headers.txt
"""

import argparse
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from email.utils import parseaddr, parsedate_to_datetime


@dataclass
class AuthResult:
    """Authentication check result"""
    check: str
    result: str
    details: str
    passed: bool


@dataclass
class AuditResult:
    """Complete audit result"""
    spf: Optional[AuthResult] = None
    dkim: Optional[AuthResult] = None
    dmarc: Optional[AuthResult] = None
    warnings: List[str] = None
    risk_level: str = "Unknown"

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def parse_headers(raw_headers: str) -> Dict[str, List[str]]:
    """Parse raw email headers into a dictionary"""
    headers = {}
    current_header = None
    current_value = []

    for line in raw_headers.split('\n'):
        line = line.rstrip()
        if not line:
            continue

        # Check if this is a continuation line (starts with whitespace)
        if line[0] in ' \t':
            if current_header:
                current_value.append(line.strip())
        else:
            # Save previous header
            if current_header:
                if current_header not in headers:
                    headers[current_header] = []
                headers[current_header].append(' '.join(current_value))

            # Parse new header
            if ':' in line:
                current_header, value = line.split(':', 1)
                current_header = current_header.strip().lower()
                current_value = [value.strip()]
            else:
                current_header = None
                current_value = []

    # Save last header
    if current_header:
        if current_header not in headers:
            headers[current_header] = []
        headers[current_header].append(' '.join(current_value))

    return headers


def check_spf(headers: Dict[str, List[str]]) -> AuthResult:
    """Check SPF authentication result"""
    # Look for Received-SPF header
    spf_headers = headers.get('received-spf', [])
    authentication_results = headers.get('authentication-results', [])

    # Check Received-SPF
    for spf in spf_headers:
        spf_lower = spf.lower()
        if 'pass' in spf_lower:
            return AuthResult(
                check="SPF",
                result="Pass",
                details=spf[:200],
                passed=True
            )
        elif 'fail' in spf_lower:
            return AuthResult(
                check="SPF",
                result="Fail",
                details=spf[:200],
                passed=False
            )
        elif 'softfail' in spf_lower:
            return AuthResult(
                check="SPF",
                result="Softfail",
                details=spf[:200],
                passed=False
            )

    # Check Authentication-Results
    for auth in authentication_results:
        if 'spf=' in auth.lower():
            auth_lower = auth.lower()
            if 'spf=pass' in auth_lower:
                return AuthResult(
                    check="SPF",
                    result="Pass",
                    details=auth[:200],
                    passed=True
                )
            elif 'spf=fail' in auth_lower:
                return AuthResult(
                    check="SPF",
                    result="Fail",
                    details=auth[:200],
                    passed=False
                )

    return AuthResult(
        check="SPF",
        result="Not Found",
        details="No SPF result found in headers",
        passed=False
    )


def check_dkim(headers: Dict[str, List[str]]) -> AuthResult:
    """Check DKIM authentication result"""
    dkim_headers = headers.get('dkim-signature', [])
    authentication_results = headers.get('authentication-results', [])

    # Check for DKIM-Signature presence
    if not dkim_headers:
        return AuthResult(
            check="DKIM",
            result="Not Found",
            details="No DKIM signature in headers",
            passed=False
        )

    # Check Authentication-Results for DKIM verification
    for auth in authentication_results:
        auth_lower = auth.lower()
        if 'dkim=' in auth_lower:
            if 'dkim=pass' in auth_lower or 'dkim=ok' in auth_lower:
                # Extract signing domain
                domain_match = re.search(r'd=([^\s;]+)', ' '.join(dkim_headers))
                domain = domain_match.group(1) if domain_match else "unknown"
                return AuthResult(
                    check="DKIM",
                    result="Pass",
                    details=f"Signed by: {domain}",
                    passed=True
                )
            elif 'dkim=fail' in auth_lower or 'dkim=bad' in auth_lower:
                return AuthResult(
                    check="DKIM",
                    result="Fail",
                    details=auth[:200],
                    passed=False
                )

    # DKIM signature exists but no verification result
    domain_match = re.search(r'd=([^\s;]+)', ' '.join(dkim_headers))
    domain = domain_match.group(1) if domain_match else "unknown"
    return AuthResult(
        check="DKIM",
        result="Signature Present",
        details=f"Signed by: {domain} (verification result not found)",
        passed=True
    )


def check_dmarc(headers: Dict[str, List[str]]) -> AuthResult:
    """Check DMARC authentication result"""
    authentication_results = headers.get('authentication-results', [])

    for auth in authentication_results:
        auth_lower = auth.lower()
        if 'dmarc=' in auth_lower:
            if 'dmarc=pass' in auth_lower:
                return AuthResult(
                    check="DMARC",
                    result="Pass",
                    details=auth[:200],
                    passed=True
                )
            elif 'dmarc=fail' in auth_lower:
                return AuthResult(
                    check="DMARC",
                    result="Fail",
                    details=auth[:200],
                    passed=False
                )

    return AuthResult(
        check="DMARC",
        result="Not Found",
        details="No DMARC result found in headers",
        passed=False
    )


def detect_warnings(headers: Dict[str, List[str]]) -> List[str]:
    """Detect security warnings from headers"""
    warnings = []

    # Check From vs Reply-To mismatch
    from_addr = headers.get('from', [''])[0]
    reply_to = headers.get('reply-to', [''])[0]
    if from_addr and reply_to:
        from_domain = parseaddr(from_addr)[1].split('@')[-1] if '@' in parseaddr(from_addr)[1] else ''
        reply_domain = parseaddr(reply_to)[1].split('@')[-1] if '@' in parseaddr(reply_to)[1] else ''
        if from_domain and reply_domain and from_domain.lower() != reply_domain.lower():
            warnings.append(f"From domain ({from_domain}) != Reply-To domain ({reply_domain})")

    # Check From vs Return-Path mismatch
    return_path = headers.get('return-path', [''])[0]
    if from_addr and return_path:
        from_domain = parseaddr(from_addr)[1].split('@')[-1] if '@' in parseaddr(from_addr)[1] else ''
        return_domain = return_path.strip('<>').split('@')[-1] if '@' in return_path else ''
        if from_domain and return_domain and from_domain.lower() != return_domain.lower():
            warnings.append(f"From domain ({from_domain}) != Return-Path domain ({return_domain})")

    # Check X-Originating-IP
    originating_ip = headers.get('x-originating-ip', [])
    if originating_ip:
        warnings.append(f"Originating IP: {originating_ip[0]}")

    # Check for suspicious Received chain patterns
    received = headers.get('received', [])
    if len(received) > 10:
        warnings.append(f"Unusual number of Received hops: {len(received)}")

    # Check for suspicious header combinations
    if headers.get('x-priority') and 'urgent' in str(headers.get('subject', '')).lower():
        warnings.append("Email marked as urgent - common in phishing")

    # Check for mismatched Message-ID domain
    message_id = headers.get('message-id', [''])[0]
    if from_addr and message_id:
        from_domain = parseaddr(from_addr)[1].split('@')[-1] if '@' in parseaddr(from_addr)[1] else ''
        msg_id_domain = message_id.split('@')[-1].rstrip('>') if '@' in message_id else ''
        if from_domain and msg_id_domain and from_domain.lower() != msg_id_domain.lower():
            warnings.append(f"From domain ({from_domain}) != Message-ID domain ({msg_id_domain})")

    return warnings


def calculate_risk_level(result: AuditResult) -> str:
    """Calculate overall risk level"""
    score = 0

    # Authentication failures
    if result.spf and not result.spf.passed:
        score += 2
    if result.dkim and not result.dkim.passed:
        score += 1
    if result.dmarc and not result.dmarc.passed:
        score += 2

    # Warnings
    score += len(result.warnings)

    if score >= 5:
        return "Critical"
    elif score >= 3:
        return "High"
    elif score >= 1:
        return "Medium"
    else:
        return "Low"


def analyze_email(raw_headers: str) -> AuditResult:
    """Analyze email headers for security issues"""
    headers = parse_headers(raw_headers)

    result = AuditResult()
    result.spf = check_spf(headers)
    result.dkim = check_dkim(headers)
    result.dmarc = check_dmarc(headers)
    result.warnings = detect_warnings(headers)
    result.risk_level = calculate_risk_level(result)

    return result


def print_report(result: AuditResult):
    """Print analysis report"""
    print("\n" + "="*60)
    print("EMAIL SECURITY AUDIT REPORT")
    print("="*60)

    print(f"\n📊 Overall Risk Level: {result.risk_level}")

    print("\n🔐 Authentication Results:")
    print("-"*40)

    for auth in [result.spf, result.dkim, result.dmarc]:
        if auth:
            status = "✅" if auth.passed else "❌"
            print(f"{status} {auth.check}: {auth.result}")
            if auth.details:
                print(f"   └─ {auth.details[:100]}")

    if result.warnings:
        print("\n⚠️  Warnings:")
        print("-"*40)
        for warning in result.warnings:
            print(f"  • {warning}")

    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description='Analyze email headers for security issues')
    parser.add_argument('--header', type=str, help='Raw email headers as string')
    parser.add_argument('--file', type=str, help='File containing email headers')
    args = parser.parse_args()

    if not args.header and not args.file:
        parser.print_help()
        print("\nExample usage:")
        print('  python analyze_email.py --header "From: test@example.com\\nReceived-SPF: pass"')
        print("  python analyze_email.py --file headers.txt")
        sys.exit(1)

    if args.file:
        with open(args.file, 'r', encoding='utf-8', errors='ignore') as f:
            raw_headers = f.read()
    else:
        raw_headers = args.header

    result = analyze_email(raw_headers)
    print_report(result)

    # Exit with error code if high risk
    if result.risk_level in ["High", "Critical"]:
        sys.exit(1)


if __name__ == '__main__':
    main()
