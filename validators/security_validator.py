"""
Security Validator - Checks HTTP security headers and security best practices.
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests


class SecurityValidator:
    """Validates security headers and practices."""

    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    REQUIRED_HEADERS = {
        'strict-transport-security': {
            'name': 'Strict-Transport-Security (HSTS)',
            'severity': 'critical',
            'description': 'Enforces HTTPS connections. Add: Strict-Transport-Security: max-age=31536000; includeSubDomains',
        },
        'x-content-type-options': {
            'name': 'X-Content-Type-Options',
            'severity': 'critical',
            'description': 'Prevents MIME type sniffing. Add: X-Content-Type-Options: nosniff',
        },
        'x-frame-options': {
            'name': 'X-Frame-Options',
            'severity': 'warning',
            'description': 'Prevents clickjacking attacks. Add: X-Frame-Options: DENY or SAMEORIGIN',
        },
        'content-security-policy': {
            'name': 'Content-Security-Policy (CSP)',
            'severity': 'warning',
            'description': 'Mitigates XSS and injection attacks. Configure a CSP header appropriate for your site.',
        },
        'referrer-policy': {
            'name': 'Referrer-Policy',
            'severity': 'info',
            'description': 'Controls referrer information. Add: Referrer-Policy: strict-origin-when-cross-origin',
        },
        'permissions-policy': {
            'name': 'Permissions-Policy',
            'severity': 'info',
            'description': 'Controls browser features. Add: Permissions-Policy: camera=(), microphone=(), geolocation=()',
        },
    }

    def validate(self, url, html, crawl_result=None):
        """Run all security validation checks."""
        issues = []
        soup = BeautifulSoup(html, 'html5lib')

        headers = {}
        if crawl_result and crawl_result.response_headers:
            headers = crawl_result.response_headers

        issues.extend(self._check_security_headers(headers))
        issues.extend(self._check_https(url))
        issues.extend(self._check_mixed_content(soup, url))
        issues.extend(self._check_external_links(soup))
        issues.extend(self._check_form_security(soup))
        issues.extend(self._check_sensitive_info(html))
        issues.extend(self._check_cookie_security(headers))
        issues.extend(self._check_server_info(headers))
        issues.extend(self._check_subresource_integrity(soup))

        return {
            "url": url,
            "category": "security",
            "issues": issues,
            "score": self._calculate_score(issues),
            "headers_present": list(headers.keys()),
        }

    def _issue(self, severity, message, element=None):
        issue = {"severity": severity, "message": message}
        if element:
            issue["element"] = str(element)[:200]
        return issue

    def _calculate_score(self, issues):
        score = 100
        for issue in issues:
            if issue["severity"] == self.SEVERITY_CRITICAL:
                score -= 12
            elif issue["severity"] == self.SEVERITY_WARNING:
                score -= 6
            elif issue["severity"] == self.SEVERITY_INFO:
                score -= 2
        return max(0, score)

    def _check_security_headers(self, headers):
        """Check for required security headers."""
        issues = []
        headers_lower = {k.lower(): v for k, v in headers.items()}

        for header_key, info in self.REQUIRED_HEADERS.items():
            if header_key not in headers_lower:
                severity = getattr(self, f"SEVERITY_{info['severity'].upper()}")
                issues.append(self._issue(
                    severity,
                    f"Missing {info['name']} header. {info['description']}"
                ))

        # Check HSTS value if present
        hsts = headers_lower.get('strict-transport-security', '')
        if hsts:
            max_age_match = re.search(r'max-age=(\d+)', hsts)
            if max_age_match:
                max_age = int(max_age_match.group(1))
                if max_age < 31536000:
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"HSTS max-age is {max_age} seconds ({max_age//86400} days). "
                        f"Recommended minimum is 31536000 (1 year)."
                    ))

        return issues

    def _check_https(self, url):
        """Check HTTPS enforcement."""
        issues = []
        parsed = urlparse(url)

        if parsed.scheme != 'https':
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Site not served over HTTPS. HTTPS is essential for security and SEO."
            ))
            return issues

        # Check HTTP to HTTPS redirect
        try:
            http_url = url.replace('https://', 'http://')
            resp = requests.get(http_url, timeout=10, allow_redirects=False)
            if resp.status_code not in [301, 302, 307, 308]:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"HTTP does not redirect to HTTPS (got HTTP {resp.status_code}). "
                    f"Configure a 301 redirect from HTTP to HTTPS."
                ))
            elif resp.status_code == 302:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    "HTTP redirects to HTTPS with 302 (temporary). "
                    "Use 301 (permanent) redirect instead for SEO benefit."
                ))
        except Exception:
            pass

        return issues

    def _check_mixed_content(self, soup, url):
        """Check for mixed content (HTTP resources on HTTPS page)."""
        issues = []
        if not url.startswith('https://'):
            return issues

        mixed_resources = []

        # Check all resource URLs
        for tag, attr in [('img', 'src'), ('script', 'src'), ('link', 'href'),
                          ('iframe', 'src'), ('audio', 'src'), ('video', 'src'),
                          ('source', 'src'), ('embed', 'src'), ('object', 'data')]:
            for elem in soup.find_all(tag):
                resource_url = elem.get(attr, '')
                if resource_url.startswith('http://'):
                    mixed_resources.append({
                        'tag': tag,
                        'url': resource_url[:80],
                    })

        if mixed_resources:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                f"Mixed content detected: {len(mixed_resources)} HTTP resource(s) on HTTPS page. "
                f"Examples: {', '.join(r['url'] for r in mixed_resources[:3])}"
            ))

        return issues

    def _check_external_links(self, soup):
        """Check external links for security attributes."""
        issues = []
        external_links = []

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith('http') and not self._is_same_domain(href, soup):
                target = link.get('target', '')
                rel = link.get('rel', [])
                if isinstance(rel, list):
                    rel = ' '.join(rel)

                if target == '_blank':
                    missing_attrs = []
                    if 'noopener' not in str(rel):
                        missing_attrs.append('noopener')
                    if 'noreferrer' not in str(rel):
                        missing_attrs.append('noreferrer')

                    if missing_attrs:
                        text = link.get_text(strip=True)[:40]
                        external_links.append({
                            'text': text,
                            'href': href[:60],
                            'missing': missing_attrs,
                        })

        if external_links:
            count = len(external_links)
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"{count} external link(s) with target='_blank' missing rel='noopener noreferrer'. "
                f"This can expose your site to reverse tabnabbing attacks. "
                f"Examples: {', '.join(l['text'] or l['href'] for l in external_links[:3])}"
            ))

        return issues

    def _is_same_domain(self, url, soup):
        """Check if URL is same domain."""
        try:
            parsed = urlparse(url)
            html_tag = soup.find('html')
            # Simple check - can be improved
            return False
        except Exception:
            return False

    def _check_form_security(self, soup):
        """Check form security practices."""
        issues = []
        forms = soup.find_all('form')

        for form in forms:
            action = form.get('action', '')
            method = form.get('method', 'get').lower()

            # Check for HTTP form action on HTTPS page
            if action.startswith('http://'):
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"Form submits to HTTP URL: {action[:60]}. "
                    f"Form data will be sent unencrypted.",
                    element=str(form)[:150]
                ))

            # Check for password fields in GET forms
            if method == 'get' and form.find('input', type='password'):
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    "Password field in GET form. Passwords will appear in URL. Use POST method.",
                    element=str(form)[:150]
                ))

            # Check for autocomplete on sensitive fields
            password_fields = form.find_all('input', type='password')
            for pf in password_fields:
                if pf.get('autocomplete') not in ['off', 'new-password', 'current-password']:
                    issues.append(self._issue(
                        self.SEVERITY_INFO,
                        "Password field without explicit autocomplete attribute.",
                    ))

        return issues

    def _check_sensitive_info(self, html):
        """Check for exposed sensitive information in HTML."""
        issues = []

        # Check for API keys or tokens in HTML
        patterns = {
            'API Key': r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9]{20,})["\']',
            'AWS Key': r'AKIA[0-9A-Z]{16}',
            'Private Key': r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',
            'Google Maps Key': r'AIza[0-9A-Za-z\-_]{35}',
        }

        for name, pattern in patterns.items():
            if re.search(pattern, html):
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"Possible {name} exposed in HTML source code. "
                    f"Move sensitive credentials to server-side configuration."
                ))

        # Check for HTML comments with sensitive info
        comments = re.findall(r'<!--(.*?)-->', html, re.DOTALL)
        sensitive_keywords = ['password', 'secret', 'todo', 'fixme', 'hack', 'temp', 'debug']
        for comment in comments:
            comment_lower = comment.lower()
            for keyword in sensitive_keywords:
                if keyword in comment_lower:
                    issues.append(self._issue(
                        self.SEVERITY_INFO,
                        f"HTML comment contains '{keyword}': '{comment.strip()[:80]}...'. "
                        f"Remove development comments before production."
                    ))
                    break

        return issues

    def _check_cookie_security(self, headers):
        """Check cookie security flags."""
        issues = []
        set_cookie = headers.get('set-cookie', '')

        if set_cookie:
            if 'Secure' not in set_cookie:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    "Cookie missing 'Secure' flag. Cookies should only be sent over HTTPS."
                ))
            if 'HttpOnly' not in set_cookie:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    "Cookie missing 'HttpOnly' flag. This prevents JavaScript access to cookies."
                ))
            if 'SameSite' not in set_cookie:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    "Cookie missing 'SameSite' attribute. Add SameSite=Strict or SameSite=Lax."
                ))

        return issues

    def _check_server_info(self, headers):
        """Check for server information disclosure."""
        issues = []

        server = headers.get('server', '')
        if server and any(v in server.lower() for v in ['apache/', 'nginx/', 'iis/', 'litespeed/']):
            issues.append(self._issue(
                self.SEVERITY_INFO,
                f"Server header reveals software: '{server}'. "
                f"Consider removing version information to reduce attack surface."
            ))

        x_powered = headers.get('x-powered-by', '')
        if x_powered:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"X-Powered-By header reveals technology: '{x_powered}'. "
                f"Remove this header to avoid exposing your tech stack."
            ))

        return issues

    def _check_subresource_integrity(self, soup):
        """Check for Subresource Integrity (SRI) on CDN resources."""
        issues = []
        
        cdn_domains = ['cdn', 'cdnjs', 'jsdelivr', 'unpkg', 'cloudflare', 'googleapis', 
                       'bootstrapcdn', 'code.jquery']

        for tag in soup.find_all(['script', 'link']):
            src = tag.get('src') or tag.get('href', '')
            if any(cdn in src.lower() for cdn in cdn_domains):
                if not tag.get('integrity'):
                    filename = src.split('/')[-1][:50]
                    issues.append(self._issue(
                        self.SEVERITY_INFO,
                        f"CDN resource without SRI hash: {filename}. "
                        f"Add integrity='sha384-...' to protect against CDN compromise.",
                        element=str(tag)[:200]
                    ))

        return issues
