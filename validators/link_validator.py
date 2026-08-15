"""
Link Validator - Checks for broken links, orphan pages, and link quality.
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


class LinkValidator:
    """Validates all links across the website."""

    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    def __init__(self, timeout=15):
        self.timeout = timeout
        self.checked_urls = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ChinmayaRamalayaValidator/1.0 (Link Checker)'
        })

    def validate_all(self, crawl_results):
        """Validate all links across all crawled pages."""
        issues = []
        all_internal_links = set()
        all_external_links = {}
        all_pages = set(crawl_results.keys())
        linked_pages = set()
        placeholder_links = []

        # Collect all links
        for url, result in crawl_results.items():
            for link in result.internal_links:
                link_url = link['url'].split('#')[0].split('?')[0]
                all_internal_links.add(link_url)
                linked_pages.add(link_url)

            for link in result.external_links:
                link_url = link['url']
                if link_url not in all_external_links:
                    all_external_links[link_url] = []
                all_external_links[link_url].append({
                    'source': url,
                    'text': link.get('text', ''),
                })

            # Check for placeholder/empty links
            for link in result.internal_links + result.external_links:
                href = link.get('url', '')
                text = link.get('text', '')
                if href.endswith('#') or href == '#':
                    placeholder_links.append({
                        'source': url,
                        'text': text,
                        'href': href,
                    })

        # Check broken internal links
        issues.extend(self._check_broken_internal(all_internal_links, all_pages, crawl_results))

        # Check broken external links
        issues.extend(self._check_broken_external(all_external_links))

        # Check orphan pages
        issues.extend(self._check_orphan_pages(all_pages, linked_pages))

        # Check placeholder links
        issues.extend(self._check_placeholder_links(placeholder_links))

        # Check mailto/tel links
        issues.extend(self._check_special_links(crawl_results))

        return {
            "category": "links",
            "issues": issues,
            "score": self._calculate_score(issues),
            "summary": {
                "total_internal_links": len(all_internal_links),
                "total_external_links": len(all_external_links),
                "total_placeholder_links": len(placeholder_links),
                "total_pages": len(all_pages),
            }
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
                score -= 10
            elif issue["severity"] == self.SEVERITY_WARNING:
                score -= 5
            elif issue["severity"] == self.SEVERITY_INFO:
                score -= 2
        return max(0, score)

    def _check_broken_internal(self, all_internal_links, all_pages, crawl_results):
        """Check for broken internal links."""
        issues = []

        for link_url in all_internal_links:
            # Normalize the URL for comparison
            normalized = link_url.rstrip('/')
            if normalized.endswith('/index.html'):
                normalized = normalized.replace('/index.html', '')

            found = False
            for page_url in all_pages:
                page_normalized = page_url.rstrip('/')
                if page_normalized.endswith('/index.html'):
                    page_normalized = page_normalized.replace('/index.html', '')
                if normalized == page_normalized:
                    found = True
                    break

            if not found:
                # Check if it's a non-page resource (PDF, image, etc.)
                parsed = urlparse(link_url)
                ext = parsed.path.split('.')[-1].lower() if '.' in parsed.path else ''
                if ext in ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'mp3', 'mp4']:
                    # Verify resource exists
                    try:
                        resp = self.session.head(link_url, timeout=self.timeout, allow_redirects=True)
                        if resp.status_code >= 400:
                            issues.append(self._issue(
                                self.SEVERITY_CRITICAL,
                                f"Broken internal resource (HTTP {resp.status_code}): {link_url}"
                            ))
                    except Exception as e:
                        issues.append(self._issue(
                            self.SEVERITY_WARNING,
                            f"Cannot verify internal resource: {link_url} ({str(e)[:50]})"
                        ))
                else:
                    # Try to actually fetch the page
                    try:
                        resp = self.session.head(link_url, timeout=self.timeout, allow_redirects=True)
                        if resp.status_code >= 400:
                            issues.append(self._issue(
                                self.SEVERITY_CRITICAL,
                                f"Broken internal link (HTTP {resp.status_code}): {link_url}"
                            ))
                    except Exception:
                        pass

        return issues

    def _check_broken_external(self, all_external_links):
        """Check for broken external links using concurrent requests."""
        issues = []
        broken = []

        def check_url(url, sources):
            try:
                resp = self.session.head(
                    url, timeout=self.timeout, allow_redirects=True
                )
                if resp.status_code >= 400:
                    # Try GET as some servers don't support HEAD
                    resp = self.session.get(
                        url, timeout=self.timeout, allow_redirects=True,
                        stream=True
                    )
                    resp.close()
                return url, resp.status_code, sources
            except requests.exceptions.SSLError:
                return url, 'SSL_ERROR', sources
            except requests.exceptions.ConnectionError:
                return url, 'CONNECTION_ERROR', sources
            except requests.exceptions.Timeout:
                return url, 'TIMEOUT', sources
            except Exception as e:
                return url, f'ERROR: {str(e)[:30]}', sources

        # Check external links concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(check_url, url, sources): url
                for url, sources in all_external_links.items()
            }

            for future in as_completed(futures):
                url, status, sources = future.result()
                source_text = sources[0]['text'][:40] if sources else ''

                if isinstance(status, int):
                    if status >= 400:
                        issues.append(self._issue(
                            self.SEVERITY_CRITICAL,
                            f"Broken external link (HTTP {status}): {url} "
                            f"[Link text: \"{source_text}\"]"
                        ))
                    elif status in [301, 302, 307, 308]:
                        issues.append(self._issue(
                            self.SEVERITY_INFO,
                            f"External link redirects (HTTP {status}): {url}. "
                            f"Consider updating to the final URL."
                        ))
                elif status == 'SSL_ERROR':
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"SSL error on external link: {url}. Certificate may be invalid."
                    ))
                elif status == 'CONNECTION_ERROR':
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Cannot connect to external link: {url}"
                    ))
                elif status == 'TIMEOUT':
                    issues.append(self._issue(
                        self.SEVERITY_INFO,
                        f"External link timeout: {url}. Site may be slow or blocking bots."
                    ))

        return issues

    def _check_orphan_pages(self, all_pages, linked_pages):
        """Check for pages not linked from any other page."""
        issues = []

        for page in all_pages:
            # Skip the homepage
            parsed = urlparse(page)
            if parsed.path in ['/', '/index.html', '']:
                continue

            is_linked = False
            page_normalized = page.rstrip('/').split('#')[0].split('?')[0]

            for linked in linked_pages:
                linked_normalized = linked.rstrip('/').split('#')[0].split('?')[0]
                if page_normalized == linked_normalized:
                    is_linked = True
                    break

            if not is_linked:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"Orphan page (not linked from any other page): {page}"
                ))

        return issues

    def _check_placeholder_links(self, placeholder_links):
        """Check for links pointing to '#' (placeholder)."""
        issues = []

        if placeholder_links:
            unique_texts = set()
            for link in placeholder_links:
                text = link.get('text', 'unknown')[:60]
                if text not in unique_texts:
                    unique_texts.add(text)

            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"{len(placeholder_links)} placeholder link(s) pointing to '#'. "
                f"Link texts: {', '.join(list(unique_texts)[:5])}"
            ))

        return issues

    def _check_special_links(self, crawl_results):
        """Check mailto and tel links."""
        issues = []

        for url, result in crawl_results.items():
            soup = BeautifulSoup(result.html, 'html5lib')
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')

                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').split('?')[0]
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                        issues.append(self._issue(
                            self.SEVERITY_WARNING,
                            f"Invalid email in mailto link: {email}",
                        ))

                elif href.startswith('tel:'):
                    phone = href.replace('tel:', '')
                    if not re.match(r'^[\+\d\-\(\)\s\.]+$', phone):
                        issues.append(self._issue(
                            self.SEVERITY_WARNING,
                            f"Invalid phone number in tel link: {phone}",
                        ))

        return issues
