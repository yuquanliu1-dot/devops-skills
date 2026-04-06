---
name: email-audit
description: 
  Email Security Audit Skill - Analyzes .eml email files for security threats including phishing, malicious links, suspicious attachments, and social engineering attempts. Use this skill whenever the user mentions email audit, phishing detection, email security analysis, analyzing suspicious emails, checking email for malware, or auditing .eml files. Also trigger when users ask to analyze email headers, detect email spoofing, or generate email security reports.
tags: [security]
---

# Email Security Audit Skill (邮件安全审计)

This skill provides a systematic workflow for analyzing email files (.eml format) to detect security threats and generate comprehensive audit reports.

## When to Use This Skill

- Analyzing suspicious emails for phishing indicators
- Security audits of email communications
- Investigating potential email-based attacks
- Generating email security reports for compliance
- Checking emails for malicious content

## Audit Workflow

### Step 1: Parse the EML File

Read and parse the .eml file to extract all components:

```python
# Use the email library to parse EML files
import email
from email import policy
from email.parser import BytesParser
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib
import base64

def parse_eml_file(file_path: str) -> Dict[str, Any]:
    """Parse an EML file and extract all components."""
    with open(file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)

    result = {
        'headers': {},
        'body': {'text': '', 'html': ''},
        'attachments': [],
        'links': [],
        'images': []
    }

    # Extract headers
    for header in ['From', 'To', 'Cc', 'Bcc', 'Subject', 'Date',
                   'Reply-To', 'Return-Path', 'Message-ID',
                   'X-Sender-IP', 'Received', 'Authentication-Results',
                   'DKIM-Signature', 'SPF', 'DMARC']:
        if header in msg:
            result['headers'][header] = str(msg[header])

    # Extract body and attachments
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))

            if 'attachment' in content_disposition:
                # Handle attachment
                filename = part.get_filename()
                if filename:
                    payload = part.get_payload(decode=True)
                    result['attachments'].append({
                        'filename': filename,
                        'content_type': content_type,
                        'size': len(payload) if payload else 0,
                        'hash': hashlib.sha256(payload).hexdigest() if payload else None
                    })
            elif content_type == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    result['body']['text'] = payload.decode('utf-8', errors='ignore')
            elif content_type == 'text/html':
                payload = part.get_payload(decode=True)
                if payload:
                    result['body']['html'] = payload.decode('utf-8', errors='ignore')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            result['body']['text'] = payload.decode('utf-8', errors='ignore')

    # Extract links from HTML body
    if result['body']['html']:
        links = re.findall(r'href=["\']([^"\']+)["\']', result['body']['html'])
        result['links'] = list(set(links))

    return result
```

### Step 2: Analyze Email Headers

Check headers for security issues:

```python
def analyze_headers(headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Analyze email headers for security issues."""
    findings = []

    # Check for spoofing indicators
    from_addr = headers.get('From', '')
    reply_to = headers.get('Reply-To', '')
    return_path = headers.get('Return-Path', '')

    if reply_to and from_addr:
        from_domain = re.search(r'@([\w.-]+)', from_addr)
        reply_domain = re.search(r'@([\w.-]+)', reply_to)
        if from_domain and reply_domain and from_domain.group(1) != reply_domain.group(1):
            findings.append({
                'severity': 'HIGH',
                'category': 'Header Spoofing',
                'description': f'Reply-To domain ({reply_domain.group(1)}) differs from From domain ({from_domain.group(1)})',
                'indicator': 'Possible spoofing attempt'
            })

    # Check authentication results
    auth_results = headers.get('Authentication-Results', '')
    if auth_results:
        if 'spf=fail' in auth_results.lower():
            findings.append({
                'severity': 'HIGH',
                'category': 'SPF Failure',
                'description': 'SPF authentication failed',
                'indicator': 'Email may be forged'
            })
        if 'dkim=fail' in auth_results.lower():
            findings.append({
                'severity': 'MEDIUM',
                'category': 'DKIM Failure',
                'description': 'DKIM signature verification failed',
                'indicator': 'Email integrity cannot be verified'
            })
        if 'dmarc=fail' in auth_results.lower():
            findings.append({
                'severity': 'HIGH',
                'category': 'DMARC Failure',
                'description': 'DMARC policy check failed',
                'indicator': 'Email fails domain authentication'
            })

    # Check for missing authentication headers
    if not auth_results and 'Received' in headers:
        findings.append({
            'severity': 'MEDIUM',
            'category': 'Missing Authentication',
            'description': 'No authentication results header found',
            'indicator': 'Unable to verify email authenticity'
        })

    return findings
```

### Step 3: Detect Phishing Indicators

Analyze the email body for phishing signals:

```python
# Phishing indicator patterns
PHISHING_PATTERNS = {
    'urgency': [
        r'urgent',
        r'immediate',
        r'expires?\s+(today|soon|in\s+\d+\s+hours?)',
        r'act\s+now',
        r'limited\s+time',
        r'your\s+account\s+will\s+be\s+(closed|suspended|locked)',
        r'verify\s+(your\s+)?account',
        r'confirm\s+(your\s+)?(identity|information)',
        r'紧急',
        r'立即',
        r'账号将被冻结',
        r'验证您的账户'
    ],
    'credential_request': [
        r'password',
        r'username',
        r'login',
        r'credential',
        r'social\s+security',
        r'credit\s+card',
        r'bank\s+account',
        r'密码',
        r'银行卡',
        r'身份证'
    ],
    'suspicious_phrases': [
        r'dear\s+(customer|user|member|client)',
        r'dear\s+valued',
        r'we\s+(detected|noticed)\s+(unusual|suspicious)',
        r'security\s+(alert|warning|breach)',
        r'update\s+your\s+(payment|billing)',
        r'click\s+(here|below)\s+to',
        r'尊敬的客户',
        r'检测到异常',
        r'安全警告',
        r'点击此处'
    ]
}

SUSPICIOUS_DOMAINS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly',
    'is.gd', 'buff.ly', 'shorturl.at', 'rb.gy'
]

def detect_phishing(body_text: str, links: List[str]) -> List[Dict[str, Any]]:
    """Detect phishing indicators in email content."""
    findings = []
    text_lower = body_text.lower()

    # Check urgency patterns
    urgency_matches = []
    for pattern in PHISHING_PATTERNS['urgency']:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            urgency_matches.extend(matches)

    if len(urgency_matches) >= 2:
        findings.append({
            'severity': 'HIGH',
            'category': 'Urgency Tactics',
            'description': f'Multiple urgency indicators found: {", ".join(urgency_matches[:3])}',
            'indicator': 'Common phishing tactic to create pressure'
        })

    # Check credential request patterns
    cred_matches = []
    for pattern in PHISHING_PATTERNS['credential_request']:
        if re.search(pattern, text_lower, re.IGNORECASE):
            cred_matches.append(pattern)

    if cred_matches:
        findings.append({
            'severity': 'HIGH',
            'category': 'Credential Harvesting',
            'description': 'Email requests sensitive information',
            'indicator': 'Potential credential theft attempt'
        })

    # Check suspicious phrases
    phrase_matches = []
    for pattern in PHISHING_PATTERNS['suspicious_phrases']:
        if re.search(pattern, text_lower, re.IGNORECASE):
            phrase_matches.append(pattern)

    if len(phrase_matches) >= 2:
        findings.append({
            'severity': 'MEDIUM',
            'category': 'Generic Greeting/Phrasing',
            'description': 'Generic greetings and suspicious phrases detected',
            'indicator': 'Common in mass phishing campaigns'
        })

    # Check for shortened URLs
    for link in links:
        for domain in SUSPICIOUS_DOMAINS:
            if domain in link:
                findings.append({
                    'severity': 'MEDIUM',
                    'category': 'Shortened URL',
                    'description': f'Shortened URL detected: {link}',
                    'indicator': 'Destination URL is hidden'
                })
                break

    # Check for mismatched display text and actual URL
    url_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    mismatches = re.findall(url_pattern, body_text)
    for display, actual_url in mismatches:
        display_domain = re.search(r'@?([\w.-]+\.\w+)', display)
        actual_domain = re.search(r'@?([\w.-]+\.\w+)', actual_url)
        if display_domain and actual_domain:
            if display_domain.group(1) != actual_domain.group(1):
                findings.append({
                    'severity': 'HIGH',
                    'category': 'URL Mismatch',
                    'description': f'Display text suggests {display_domain.group(1)} but links to {actual_domain.group(1)}',
                    'indicator': 'Deceptive link technique'
                })

    return findings
```

### Step 4: Analyze Links

Extract and analyze all URLs in the email:

```python
def analyze_links(links: List[str], body_text: str) -> List[Dict[str, Any]]:
    """Analyze links for security risks."""
    findings = []

    for link in links:
        # Check for IP address instead of domain
        if re.match(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', link):
            findings.append({
                'severity': 'HIGH',
                'category': 'IP Address URL',
                'description': f'Link uses IP address instead of domain: {link}',
                'indicator': 'Common in phishing attacks'
            })

        # Check for suspicious TLDs
        suspicious_tlds = ['.xyz', '.top', '.club', '.online', '.site', '.work',
                          '.click', '.link', '.tk', '.ml', '.ga', '.cf']
        for tld in suspicious_tlds:
            if tld in link.lower():
                findings.append({
                    'severity': 'MEDIUM',
                    'category': 'Suspicious TLD',
                    'description': f'Link uses suspicious TLD: {link}',
                    'indicator': 'TLD commonly used in phishing'
                })
                break

        # Check for homograph attacks (lookalike domains)
        homograph_chars = {'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c',
                          'у': 'y', 'х': 'x', 'і': 'i', 'ј': 'j', 'ѕ': 's'}
        for cyrillic, latin in homograph_chars.items():
            if cyrillic in link:
                findings.append({
                    'severity': 'HIGH',
                    'category': 'Homograph Attack',
                    'description': f'Possible Cyrillic character spoofing in: {link}',
                    'indicator': 'Domain impersonation attempt'
                })
                break

        # Check for credential embedding in URL
        if '@' in link and '://' in link:
            findings.append({
                'severity': 'HIGH',
                'category': 'Credentials in URL',
                'description': f'URL contains embedded credentials: {link[:50]}...',
                'indicator': 'Attempt to steal credentials via URL'
            })

    return findings
```

### Step 5: Analyze Attachments

Check attachments for potential threats:

```python
DANGEROUS_EXTENSIONS = [
    '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js',
    '.jar', '.msi', '.ps1', '.sh', '.deb', '.rpm', '.dmg', '.app',
    '.hta', '.wsf', '.vb', '.jse', '.wsh', '.psc1', '.msh'
]

SUSPICIOUS_EXTENSIONS = [
    '.zip', '.rar', '.7z', '.docm', '.xlsm', '.pptm', '.ppsm',
    '.swf', '.iso', '.img'
]

DOUBLE_EXTENSION_PATTERNS = [
    r'\.pdf\.exe$', r'\.doc\.exe$', r'\.xls\.exe$',
    r'\.jpg\.exe$', r'\.png\.exe$', r'\.txt\.exe$'
]

def analyze_attachments(attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze attachments for potential threats."""
    findings = []

    for att in attachments:
        filename = att['filename'].lower()
        ext = '.' + filename.rsplit('.', 1)[-1] if '.' in filename else ''

        # Check for dangerous extensions
        if ext in DANGEROUS_EXTENSIONS:
            findings.append({
                'severity': 'CRITICAL',
                'category': 'Dangerous File Type',
                'description': f'Attachment {att["filename"]} has dangerous extension {ext}',
                'indicator': 'Executable file that could contain malware'
            })

        # Check for suspicious extensions
        if ext in SUSPICIOUS_EXTENSIONS:
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Suspicious File Type',
                'description': f'Attachment {att["filename"]} has suspicious extension {ext}',
                'indicator': 'File type that may contain malicious macros or scripts'
            })

        # Check for double extensions
        for pattern in DOUBLE_EXTENSION_PATTERNS:
            if re.search(pattern, filename):
                findings.append({
                    'severity': 'CRITICAL',
                    'category': 'Double Extension',
                    'description': f'Attachment {att["filename"]} uses deceptive double extension',
                    'indicator': 'Attempt to disguise executable as document'
                })
                break

        # Check for large unexpected attachments
        if att['size'] > 10 * 1024 * 1024:  # > 10MB
            findings.append({
                'severity': 'LOW',
                'category': 'Large Attachment',
                'description': f'Attachment {att["filename"]} is unusually large ({att["size"] // (1024*1024)}MB)',
                'indicator': 'May contain embedded payload'
            })

        # Check for password-protected archives (common in phishing)
        if ext in ['.zip', '.rar', '.7z'] and att['size'] < 100 * 1024:  # Small archive
            findings.append({
                'severity': 'MEDIUM',
                'category': 'Small Archive',
                'description': f'Small compressed archive: {att["filename"]}',
                'indicator': 'Often password-protected to evade scanning'
            })

    return findings
```

### Step 6: Generate Audit Report

Create a structured audit report in Word or PDF format:

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from datetime import datetime
import json

def calculate_risk_score(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate overall risk score based on findings."""
    severity_weights = {
        'CRITICAL': 10,
        'HIGH': 7,
        'MEDIUM': 4,
        'LOW': 1
    }

    total_score = 0
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

    for finding in findings:
        severity = finding.get('severity', 'LOW')
        total_score += severity_weights.get(severity, 1)
        severity_counts[severity] += 1

    # Normalize to 0-100 scale
    max_possible = 100
    normalized_score = min(100, (total_score / max_possible) * 100)

    if normalized_score >= 70:
        risk_level = 'CRITICAL'
    elif normalized_score >= 50:
        risk_level = 'HIGH'
    elif normalized_score >= 30:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'

    return {
        'score': round(normalized_score, 1),
        'level': risk_level,
        'counts': severity_counts
    }

def generate_audit_report(eml_path: str, findings: List[Dict[str, Any]],
                         email_data: Dict[str, Any], output_format: str = 'docx') -> str:
    """Generate a comprehensive audit report."""

    risk = calculate_risk_score(findings)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if output_format == 'docx':
        doc = Document()

        # Title
        title = doc.add_heading('Email Security Audit Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Subtitle
        subtitle = doc.add_paragraph(f'邮件安全审计报告')
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()

        # Executive Summary
        doc.add_heading('Executive Summary / 执行摘要', level=1)

        # Risk Score Table
        risk_table = doc.add_table(rows=4, cols=2)
        risk_table.style = 'Table Grid'

        cells = risk_table.rows[0].cells
        cells[0].text = 'Risk Level / 风险等级'
        cells[1].text = risk['level']

        cells = risk_table.rows[1].cells
        cells[0].text = 'Risk Score / 风险分数'
        cells[1].text = f"{risk['score']}/100"

        cells = risk_table.rows[2].cells
        cells[0].text = 'Total Findings / 发现问题数'
        cells[1].text = str(len(findings))

        cells = risk_table.rows[3].cells
        cells[0].text = 'Audit Time / 审计时间'
        cells[1].text = timestamp

        doc.add_paragraph()

        # Severity Breakdown
        doc.add_heading('Severity Breakdown / 严重程度分布', level=2)
        severity_para = doc.add_paragraph()
        severity_para.add_run(f"Critical / 严重: {risk['counts']['CRITICAL']}\n")
        severity_para.add_run(f"High / 高: {risk['counts']['HIGH']}\n")
        severity_para.add_run(f"Medium / 中: {risk['counts']['MEDIUM']}\n")
        severity_para.add_run(f"Low / 低: {risk['counts']['LOW']}")

        doc.add_paragraph()

        # Email Metadata
        doc.add_heading('Email Information / 邮件信息', level=1)
        meta_table = doc.add_table(rows=5, cols=2)
        meta_table.style = 'Table Grid'

        headers = email_data.get('headers', {})
        meta_rows = [
            ('From / 发件人', headers.get('From', 'N/A')),
            ('To / 收件人', headers.get('To', 'N/A')),
            ('Subject / 主题', headers.get('Subject', 'N/A')),
            ('Date / 日期', headers.get('Date', 'N/A')),
            ('Message-ID', headers.get('Message-ID', 'N/A'))
        ]

        for i, (label, value) in enumerate(meta_rows):
            cells = meta_table.rows[i].cells
            cells[0].text = label
            cells[1].text = str(value)[:100]  # Truncate long values

        doc.add_paragraph()

        # Detailed Findings
        doc.add_heading('Detailed Findings / 详细发现', level=1)

        # Group findings by severity
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            severity_findings = [f for f in findings if f.get('severity') == severity]
            if severity_findings:
                doc.add_heading(f'{severity} Severity / {severity}级别', level=2)

                for i, finding in enumerate(severity_findings, 1):
                    doc.add_heading(f'Finding {i}: {finding["category"]}', level=3)

                    finding_table = doc.add_table(rows=3, cols=2)
                    finding_table.style = 'Table Grid'

                    cells = finding_table.rows[0].cells
                    cells[0].text = 'Description / 描述'
                    cells[1].text = finding['description']

                    cells = finding_table.rows[1].cells
                    cells[0].text = 'Indicator / 指标'
                    cells[1].text = finding['indicator']

                    cells = finding_table.rows[2].cells
                    cells[0].text = 'Severity / 严重程度'
                    cells[1].text = finding['severity']

                    doc.add_paragraph()

        # Recommendations
        doc.add_heading('Recommendations / 建议', level=1)
        recommendations = generate_recommendations(findings)
        for rec in recommendations:
            doc.add_paragraph(rec, style='List Bullet')

        # Appendix: Links Found
        if email_data.get('links'):
            doc.add_heading('Appendix: Links Found / 附录: 发现的链接', level=1)
            for link in email_data['links']:
                doc.add_paragraph(link, style='List Bullet')

        # Appendix: Attachments
        if email_data.get('attachments'):
            doc.add_heading('Appendix: Attachments / 附录: 附件信息', level=1)
            att_table = doc.add_table(rows=len(email_data['attachments']) + 1, cols=4)
            att_table.style = 'Table Grid'

            headers = ['Filename', 'Type', 'Size (bytes)', 'SHA256']
            for i, header in enumerate(headers):
                att_table.rows[0].cells[i].text = header

            for i, att in enumerate(email_data['attachments'], 1):
                att_table.rows[i].cells[0].text = att['filename']
                att_table.rows[i].cells[1].text = att['content_type']
                att_table.rows[i].cells[2].text = str(att['size'])
                att_table.rows[i].cells[3].text = att['hash'][:32] + '...' if att['hash'] else 'N/A'

        # Save
        output_path = eml_path.replace('.eml', '_audit_report.docx')
        doc.save(output_path)
        return output_path

    return None

def generate_recommendations(findings: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations based on findings."""
    recommendations = []

    categories = set(f['category'] for f in findings)

    if 'Dangerous File Type' in categories or 'Double Extension' in categories:
        recommendations.append('⚠️ Do not open any executable attachments. Delete the email immediately.')

    if 'Header Spoofing' in categories:
        recommendations.append('🔍 Verify the sender through a separate communication channel before responding.')

    if 'SPF Failure' in categories or 'DMARC Failure' in categories:
        recommendations.append('📧 This email failed authentication checks. Treat as potentially fraudulent.')

    if 'Urgency Tactics' in categories:
        recommendations.append('⏰ Be cautious of emails creating artificial urgency. Verify claims independently.')

    if 'Credential Harvesting' in categories:
        recommendations.append('🔑 Never provide passwords or sensitive information via email.')

    if 'Shortened URL' in categories or 'URL Mismatch' in categories:
        recommendations.append('🔗 Do not click on shortened or suspicious links. Verify URLs before visiting.')

    if 'Homograph Attack' in categories:
        recommendations.append('🌐 Domain spoofing detected. Verify the actual domain carefully.')

    if not recommendations:
        recommendations.append('✅ No critical security issues detected. Continue with normal email handling practices.')

    recommendations.append('📋 Report suspicious emails to your security team.')
    recommendations.append('📚 Regularly update your security awareness training.')

    return recommendations
```

## Complete Audit Script

Here's the main function that orchestrates the entire audit:

```python
def audit_email(eml_path: str, output_format: str = 'docx') -> Dict[str, Any]:
    """
    Perform a complete security audit of an email file.

    Args:
        eml_path: Path to the .eml file
        output_format: 'docx' or 'pdf' for the report format

    Returns:
        Dictionary with audit results and report path
    """
    print(f"Starting email security audit for: {eml_path}")

    # Step 1: Parse the email
    print("Parsing email file...")
    email_data = parse_eml_file(eml_path)

    # Step 2: Analyze headers
    print("Analyzing email headers...")
    header_findings = analyze_headers(email_data['headers'])

    # Step 3: Detect phishing
    print("Detecting phishing indicators...")
    body_text = email_data['body']['text'] + ' ' + email_data['body']['html']
    phishing_findings = detect_phishing(body_text, email_data['links'])

    # Step 4: Analyze links
    print("Analyzing links...")
    link_findings = analyze_links(email_data['links'], body_text)

    # Step 5: Analyze attachments
    print("Analyzing attachments...")
    attachment_findings = analyze_attachments(email_data['attachments'])

    # Combine all findings
    all_findings = header_findings + phishing_findings + link_findings + attachment_findings

    # Step 6: Generate report
    print(f"Generating {output_format.upper()} report...")
    report_path = generate_audit_report(eml_path, all_findings, email_data, output_format)

    result = {
        'email_path': eml_path,
        'findings_count': len(all_findings),
        'risk_score': calculate_risk_score(all_findings),
        'findings': all_findings,
        'report_path': report_path
    }

    print(f"\nAudit complete!")
    print(f"Total findings: {len(all_findings)}")
    print(f"Risk level: {result['risk_score']['level']}")
    print(f"Report saved to: {report_path}")

    return result
```

## Usage Example

```python
# Audit a single email
result = audit_email('/path/to/suspicious_email.eml', output_format='docx')

# Print summary
print(f"Risk Level: {result['risk_score']['level']}")
print(f"Findings: {result['findings_count']}")
for finding in result['findings']:
    print(f"  [{finding['severity']}] {finding['category']}: {finding['description']}")
```

## Report Structure

The generated audit report includes:

1. **Executive Summary (执行摘要)**
   - Overall risk level and score
   - Total findings count
   - Severity breakdown

2. **Email Information (邮件信息)**
   - Sender, recipient, subject, date
   - Message-ID and headers

3. **Detailed Findings (详细发现)**
   - Organized by severity (CRITICAL → LOW)
   - Category, description, and indicators

4. **Recommendations (建议)**
   - Actionable security guidance
   - Based on detected threats

5. **Appendices (附录)**
   - All links found in the email
   - Attachment details with hashes

## Supported Threat Categories

| Category | Severity | Description |
|----------|----------|-------------|
| Dangerous File Type | CRITICAL | Executable attachments (.exe, .scr, etc.) |
| Double Extension | CRITICAL | Disguised executables (e.g., .pdf.exe) |
| Header Spoofing | HIGH | Mismatched From/Reply-To domains |
| SPF/DMARC Failure | HIGH | Email authentication failures |
| URL Mismatch | HIGH | Deceptive link techniques |
| Homograph Attack | HIGH | Cyrillic character spoofing |
| Credential Harvesting | HIGH | Requests for sensitive data |
| Urgency Tactics | HIGH | Pressure tactics in content |
| IP Address URL | HIGH | Direct IP address links |
| DKIM Failure | MEDIUM | Signature verification failure |
| Suspicious TLD | MEDIUM | Links to high-risk TLDs |
| Shortened URL | MEDIUM | URL shortener services |
| Suspicious File Type | MEDIUM | Macro-enabled documents |
| Missing Authentication | MEDIUM | No auth headers present |
| Large Attachment | LOW | Unusually large files |

## Dependencies

```bash
pip install python-docx email
```

For PDF output:
```bash
pip install reportlab
```
