"""
SEO Validator - Checks search engine optimization best practices.
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests


class SEOValidator:
    """Validates SEO best practices for web pages."""

    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    TITLE_MIN_LENGTH = 30
    TITLE_MAX_LENGTH = 60
    META_DESC_MIN_LENGTH = 50
    META_DESC_MAX_LENGTH = 160

    def validate(self, url, html, all_pages_data=None):
        """Run all SEO validation checks."""
        issues = []
        soup = BeautifulSoup(html, 'html5lib')

        issues.extend(self._check_title(soup, url, all_pages_data))
        issues.extend(self._check_meta_description(soup, url, all_pages_data))
        issues.extend(self._check_headings(soup))
        issues.extend(self._check_images_alt(soup))
        issues.extend(self._check_canonical(soup, url))
        issues.extend(self._check_og_tags(soup))
        issues.extend(self._check_twitter_tags(soup))
        issues.extend(self._check_structured_data(soup, html))
        issues.extend(self._check_favicon(soup))
        issues.extend(self._check_sitemap_robots(url))
        issues.extend(self._check_url_structure(url))
        issues.extend(self._check_internal_linking(soup, url))

        return {
            "url": url,
            "category": "seo",
            "issues": issues,
            "score": self._calculate_score(issues),
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

    def _check_title(self, soup, url, all_pages_data):
        """Check title tag presence, length, and uniqueness."""
        issues = []
        title_tag = soup.find('title')

        if not title_tag:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Missing <title> tag. Every page must have a unique, descriptive title."
            ))
            return issues

        title_text = title_tag.get_text(strip=True)

        if not title_text:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Empty <title> tag. Add a descriptive page title.",
                element=str(title_tag)
            ))
            return issues

        if len(title_text) < self.TITLE_MIN_LENGTH:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Title too short ({len(title_text)} chars). "
                f"Recommended: {self.TITLE_MIN_LENGTH}-{self.TITLE_MAX_LENGTH} characters. "
                f"Current: \"{title_text}\"",
                element=str(title_tag)
            ))

        if len(title_text) > self.TITLE_MAX_LENGTH:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Title too long ({len(title_text)} chars, max {self.TITLE_MAX_LENGTH}). "
                f"It may be truncated in search results. Current: \"{title_text}\"",
                element=str(title_tag)
            ))

        # Check for duplicate titles across pages
        if all_pages_data:
            for other_url, other_data in all_pages_data.items():
                if other_url != url:
                    other_soup = BeautifulSoup(other_data.get('html', ''), 'html5lib')
                    other_title = other_soup.find('title')
                    if other_title and other_title.get_text(strip=True) == title_text:
                        issues.append(self._issue(
                            self.SEVERITY_CRITICAL,
                            f"Duplicate title found on another page ({other_url}). "
                            f"Each page should have a unique title. Current: \"{title_text}\""
                        ))
                        break

        return issues

    def _check_meta_description(self, soup, url, all_pages_data):
        """Check meta description presence, length, and uniqueness."""
        issues = []
        meta_desc = soup.find('meta', attrs={'name': re.compile(r'description', re.I)})

        if not meta_desc:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Missing meta description. Add <meta name='description' content='...'> "
                "for better search engine snippets."
            ))
            return issues

        content = meta_desc.get('content', '').strip()
        if not content:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Empty meta description. Add compelling content.",
                element=str(meta_desc)
            ))
            return issues

        if len(content) < self.META_DESC_MIN_LENGTH:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Meta description too short ({len(content)} chars). "
                f"Recommended: {self.META_DESC_MIN_LENGTH}-{self.META_DESC_MAX_LENGTH} characters."
            ))

        if len(content) > self.META_DESC_MAX_LENGTH:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Meta description too long ({len(content)} chars, max {self.META_DESC_MAX_LENGTH}). "
                f"It may be truncated in search results."
            ))

        return issues

    def _check_headings(self, soup):
        """Check heading structure and hierarchy."""
        issues = []

        # Check for H1
        h1_tags = soup.find_all('h1')
        if len(h1_tags) == 0:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "No <h1> tag found. Every page should have exactly one <h1>."
            ))
        elif len(h1_tags) > 1:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Multiple <h1> tags found ({len(h1_tags)}). "
                f"Best practice is to have exactly one <h1> per page."
            ))

        # Check heading hierarchy (no skipping levels)
        headings = soup.find_all(re.compile(r'^h[1-6]$'))
        if headings:
            prev_level = 0
            for h in headings:
                level = int(h.name[1])
                if prev_level > 0 and level > prev_level + 1:
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Heading level skipped: <h{prev_level}> to <h{level}>. "
                        f"Don't skip heading levels (e.g., h2 → h4).",
                        element=f"<{h.name}>{h.get_text(strip=True)[:50]}</{h.name}>"
                    ))
                prev_level = level

        # Check for empty headings
        for h in soup.find_all(re.compile(r'^h[1-6]$')):
            if not h.get_text(strip=True):
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"Empty <{h.name}> tag found. Headings should have descriptive content."
                ))

        return issues

    def _check_images_alt(self, soup):
        """Check if all images have alt attributes."""
        issues = []
        images = soup.find_all('img')

        missing_alt = 0
        empty_alt = 0
        for img in images:
            if not img.has_attr('alt'):
                missing_alt += 1
            elif not img['alt'].strip():
                # Empty alt is OK for decorative images but flag it
                empty_alt += 1

        if missing_alt > 0:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                f"{missing_alt} image(s) missing 'alt' attribute. "
                f"All images must have alt text for SEO and accessibility."
            ))

        if empty_alt > 0:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                f"{empty_alt} image(s) have empty alt text. "
                f"Empty alt is OK for decorative images but informative images need descriptive alt text."
            ))

        return issues

    def _check_canonical(self, soup, url):
        """Check for canonical URL tag."""
        issues = []
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if not canonical:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                "Missing canonical URL tag. Add <link rel='canonical' href='...'> "
                "to prevent duplicate content issues."
            ))
        return issues

    def _check_og_tags(self, soup):
        """Check Open Graph meta tags."""
        issues = []
        required_og = ['og:title', 'og:description', 'og:image', 'og:url', 'og:type']

        missing = []
        for prop in required_og:
            if not soup.find('meta', attrs={'property': prop}):
                missing.append(prop)

        if missing:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Missing Open Graph tags: {', '.join(missing)}. "
                f"These improve how your pages appear when shared on social media."
            ))
        return issues

    def _check_twitter_tags(self, soup):
        """Check Twitter Card meta tags."""
        issues = []
        twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
        if not twitter_card:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "Missing Twitter Card meta tags. Add <meta name='twitter:card' content='summary_large_image'> "
                "for better Twitter/X sharing."
            ))
        return issues

    def _check_structured_data(self, soup, html):
        """Check for structured data (schema.org)."""
        issues = []
        has_json_ld = bool(soup.find('script', type='application/ld+json'))
        has_microdata = bool(soup.find(True, attrs={'itemscope': True}))
        has_rdfa = bool(soup.find(True, attrs={'typeof': True}))

        if not has_json_ld and not has_microdata and not has_rdfa:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "No structured data (schema.org) found. "
                "Adding JSON-LD structured data can improve search result appearance (rich snippets)."
            ))
        return issues

    def _check_favicon(self, soup):
        """Check for favicon."""
        issues = []
        favicon = soup.find('link', attrs={'rel': re.compile(r'icon', re.I)})
        if not favicon:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                "No favicon declared. Add <link rel='icon' href='favicon.ico'> "
                "for brand recognition in browser tabs and bookmarks."
            ))
        return issues

    def _check_sitemap_robots(self, url):
        """Check for sitemap.xml and robots.txt."""
        issues = []
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Check robots.txt
        try:
            resp = requests.get(f"{base}/robots.txt", timeout=10)
            if resp.status_code != 200:
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"robots.txt not found (HTTP {resp.status_code}). "
                    f"Create a robots.txt file to guide search engine crawlers."
                ))
        except Exception:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Unable to access robots.txt. Ensure it exists at the site root."
            ))

        # Check sitemap.xml
        try:
            resp = requests.get(f"{base}/sitemap.xml", timeout=10)
            if resp.status_code != 200:
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"sitemap.xml not found (HTTP {resp.status_code}). "
                    f"Create a sitemap.xml to help search engines discover all your pages."
                ))
        except Exception:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Unable to access sitemap.xml. Ensure it exists at the site root."
            ))

        return issues

    def _check_url_structure(self, url):
        """Check URL structure for SEO best practices."""
        issues = []
        parsed = urlparse(url)
        path = parsed.path

        if path != path.lower() and path != '/':
            issues.append(self._issue(
                self.SEVERITY_INFO,
                f"URL contains uppercase characters: {path}. "
                f"Lowercase URLs are preferred for consistency."
            ))

        if ' ' in path or '%20' in path:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"URL contains spaces: {path}. Use hyphens instead."
            ))

        if '_' in path:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                f"URL contains underscores: {path}. Google recommends hyphens over underscores."
            ))

        return issues

    def _check_internal_linking(self, soup, url):
        """Check internal linking quality."""
        issues = []
        links = soup.find_all('a', href=True)
        
        generic_texts = ['click here', 'read more', 'learn more', 'here', 'link', 'more']
        for link in links:
            text = link.get_text(strip=True).lower()
            if text in generic_texts:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    f"Generic link text '{text}' found. Use descriptive anchor text for better SEO.",
                    element=str(link)[:150]
                ))

        return issues
