#!/usr/bin/env python3
"""
URL Security Checker - Analyze URLs for potential phishing/security issues

Usage:
    python check_url.py --url "https://example.com"
    python check_url.py --urls urls.txt
"""

import argparse
import re
import sys
from urllib.parse import urlparse
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class URLAnalysis:
    """URL analysis result"""
    url: str
    domain: str
    warnings: List[str]
    risk_level: str


# Known URL shorteners
URL_SHORTENERS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly',
    't.co', 'bl.ink', 'shorturl.at', 'rebrand.ly', 'cutt.ly',
    'rb.gy', 'tiny.cc', 'lnkd.in', 'db.tt', 'qr.ae', 'adf.ly',
    'bit.do', 'mcaf.ee', 'su.pr', 'surl.im', 'ity.im', 'q.gs',
    'vzturl.com', 'tr.im', 'wp.me', 'j.mp', 'b.gy', 'ow.ly'
]

# Suspicious TLDs often used in phishing
SUSPICIOUS_TLDS = [
    '.tk', '.ml', '.ga', '.cf', '.gq',  # Free TLDs
    '.xyz', '.top', '.club', '.online', '.site', '.live',
    '.info', '.biz', '.click', '.link', '.work'
]

# Common typosquatting patterns
TYPOSQUATTING_PATTERNS = [
    (r'g[o0]{2}gle', 'google'),
    (r'micr[o0]s[o0]ft', 'microsoft'),
    (r'amaz[o0]n', 'amazon'),
    (r'faceb[o0]{2}k', 'facebook'),
    (r'tw[i1]tter', 'twitter'),
    (r'l[i1]nked[i1]n', 'linkedin'),
    (r'app[l1]e', 'apple'),
    (r'payp[a@]l', 'paypal'),
    (r'netfl[i1]x', 'netflix'),
    (r'bank[o0]famerica', 'bankofamerica'),
    (r'ch[a@]se', 'chase'),
    (r'w[e3]llsf[a@]rgo', 'wellsfargo'),
]


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url if '://' in url else f'https://{url}')
        return parsed.netloc.lower()
    except:
        return ''


def check_https(url: str) -> Optional[str]:
    """Check if URL uses HTTPS"""
    if not url.startswith('https://'):
        return "URL does not use HTTPS"
    return None


def check_url_shortener(domain: str) -> Optional[str]:
    """Check if domain is a known URL shortener"""
    domain_base = domain.split(':')[0]  # Remove port
    if domain_base in URL_SHORTENERS:
        return f"URL shortener detected: {domain_base}"
    return None


def check_suspicious_tld(domain: str) -> Optional[str]:
    """Check if domain uses suspicious TLD"""
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            return f"Suspicious TLD: {tld}"
    return None


def check_typosquatting(domain: str) -> Optional[str]:
    """Check for typosquatting patterns"""
    domain_lower = domain.lower()
    for pattern, brand in TYPOSQUATTING_PATTERNS:
        if re.search(pattern, domain_lower):
            return f"Possible typosquatting of '{brand}' detected"
    return None


def check_suspicious_characters(domain: str) -> List[str]:
    """Check for suspicious characters in domain"""
    warnings = []

    # Check for IDN homograph attacks (non-ASCII characters)
    if any(ord(c) > 127 for c in domain):
        warnings.append("Domain contains non-ASCII characters (possible IDN homograph attack)")

    # Check for excessive hyphens
    if domain.count('-') > 3:
        warnings.append("Domain contains many hyphens (common in phishing)")

    # Check for numbers mixed with letters (l33t speak)
    if re.search(r'[a-z][0-9]|[0-9][a-z]', domain):
        warnings.append("Domain mixes letters and numbers")

    return warnings


def check_suspicious_path(url: str) -> Optional[str]:
    """Check for suspicious path patterns"""
    try:
        parsed = urlparse(url if '://' in url else f'https://{url}')
        path = parsed.path.lower() + parsed.query.lower()

        suspicious_patterns = [
            (r'login', 'login page reference'),
            (r'verify', 'verification page reference'),
            (r'account', 'account page reference'),
            (r'secure', 'secure page reference'),
            (r'update', 'update page reference'),
            (r'confirm', 'confirmation page reference'),
            (r'suspend', 'suspension warning'),
            (r'password', 'password page reference'),
            (r'credential', 'credential page reference'),
            (r'webscr', 'PayPal webscr pattern'),
            (r'cmd=_login', 'PayPal login pattern'),
        ]

        for pattern, desc in suspicious_patterns:
            if re.search(pattern, path):
                return f"Suspicious path pattern: {desc}"
    except:
        pass

    return None


def calculate_risk(warnings: List[str]) -> str:
    """Calculate risk level based on warnings"""
    count = len(warnings)
    if count >= 4:
        return "Critical"
    elif count >= 3:
        return "High"
    elif count >= 1:
        return "Medium"
    return "Low"


def analyze_url(url: str) -> URLAnalysis:
    """Analyze a URL for security issues"""
    domain = extract_domain(url)
    warnings = []

    # Run all checks
    https_warning = check_https(url)
    if https_warning:
        warnings.append(https_warning)

    shortener_warning = check_url_shortener(domain)
    if shortener_warning:
        warnings.append(shortener_warning)

    tld_warning = check_suspicious_tld(domain)
    if tld_warning:
        warnings.append(tld_warning)

    typo_warning = check_typosquatting(domain)
    if typo_warning:
        warnings.append(typo_warning)

    char_warnings = check_suspicious_characters(domain)
    warnings.extend(char_warnings)

    path_warning = check_suspicious_path(url)
    if path_warning:
        warnings.append(path_warning)

    # Check for IP address instead of domain
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain):
        warnings.append("URL uses IP address instead of domain name")

    risk = calculate_risk(warnings)

    return URLAnalysis(
        url=url,
        domain=domain,
        warnings=warnings,
        risk_level=risk
    )


def print_analysis(analysis: URLAnalysis):
    """Print URL analysis result"""
    print(f"\n🔍 URL Analysis: {analysis.url}")
    print(f"   Domain: {analysis.domain}")
    print(f"   Risk Level: {analysis.risk_level}")

    if analysis.warnings:
        print("   Warnings:")
        for warning in analysis.warnings:
            print(f"     ⚠️  {warning}")
    else:
        print("   ✅ No obvious security issues detected")

    print()


def main():
    parser = argparse.ArgumentParser(description='Analyze URLs for security issues')
    parser.add_argument('--url', type=str, help='URL to analyze')
    parser.add_argument('--urls', type=str, help='File containing URLs (one per line)')
    args = parser.parse_args()

    if not args.url and not args.urls:
        parser.print_help()
        print("\nExample usage:")
        print('  python check_url.py --url "https://suspicious-domain.com/login"')
        print("  python check_url.py --urls urls.txt")
        sys.exit(1)

    if args.urls:
        with open(args.urls, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        urls = [args.url]

    high_risk_count = 0

    for url in urls:
        analysis = analyze_url(url)
        print_analysis(analysis)
        if analysis.risk_level in ["High", "Critical"]:
            high_risk_count += 1

    if high_risk_count > 0:
        print(f"\n⚠️  {high_risk_count} URL(s) flagged as high/critical risk")
        sys.exit(1)


if __name__ == '__main__':
    main()
