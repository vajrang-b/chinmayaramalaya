"""
Content Validator - Checks content quality, freshness, and common issues.
"""

import re
from datetime import datetime
from bs4 import BeautifulSoup


class ContentValidator:
    """Validates content quality and common issues."""

    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    COMMON_TYPOS = {
        'actvities': 'activities',
        'recieve': 'receive',
        'seperate': 'separate',
        'occured': 'occurred',
        'definately': 'definitely',
        'neccessary': 'necessary',
        'accomodate': 'accommodate',
        'acheive': 'achieve',
        'beleive': 'believe',
        'calender': 'calendar',
        'collegue': 'colleague',
        'comittee': 'committee',
        'concensus': 'consensus',
        'embarass': 'embarrass',
        'enviroment': 'environment',
        'flourescent': 'fluorescent',
        'goverment': 'government',
        'harrass': 'harass',
        'independant': 'independent',
        'liason': 'liaison',
        'maintainance': 'maintenance',
        'millenium': 'millennium',
        'noticable': 'noticeable',
        'occurence': 'occurrence',
        'priviledge': 'privilege',
        'publically': 'publicly',
        'recomend': 'recommend',
        'refered': 'referred',
        'succesful': 'successful',
        'supercede': 'supersede',
        'threshhold': 'threshold',
        'tommorow': 'tomorrow',
        'untill': 'until',
        'wierd': 'weird',
        'writting': 'writing',
    }

    PLACEHOLDER_PATTERNS = [
        r'lorem ipsum',
        r'dolor sit amet',
        r'consectetur adipiscing',
        r'example\.com',
        r'your\s+(?:name|email|phone|address)\s+here',
        r'placeholder',
        r'coming\s+soon',
        r'under\s+construction',
        r'todo:?\s',
        r'fixme:?\s',
        r'xxx+',
    ]

    def validate(self, url, html):
        """Run all content validation checks."""
        issues = []
        soup = BeautifulSoup(html, 'html5lib')

        issues.extend(self._check_typos(soup))
        issues.extend(self._check_copyright_year(soup))
        issues.extend(self._check_placeholder_content(soup))
        issues.extend(self._check_content_length(soup, url))
        issues.extend(self._check_mobile_responsiveness(soup, html))
        issues.extend(self._check_broken_media(soup))
        issues.extend(self._check_contact_info(soup))
        issues.extend(self._check_social_media(soup))
        issues.extend(self._check_text_readability(soup))
        issues.extend(self._check_navigation_consistency(soup))

        return {
            "url": url,
            "category": "content",
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

    def _check_typos(self, soup):
        """Check for common spelling errors."""
        issues = []
        text = soup.get_text().lower()

        found_typos = []
        for typo, correction in self.COMMON_TYPOS.items():
            # Use word boundary matching
            pattern = r'\b' + re.escape(typo) + r'\b'
            matches = re.findall(pattern, text)
            if matches:
                found_typos.append(f"'{typo}' → '{correction}' ({len(matches)}x)")

        if found_typos:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Spelling errors found: {'; '.join(found_typos)}"
            ))

        return issues

    def _check_copyright_year(self, soup):
        """Check if copyright year is current."""
        issues = []
        current_year = datetime.now().year
        text = soup.get_text()

        copyright_patterns = [
            r'©\s*(\d{4})',
            r'copyright\s*©?\s*(\d{4})',
            r'copyrights\s*©?\s*(\d{4})',
            r'all\s+rights\s+reserved.*?(\d{4})',
        ]

        for pattern in copyright_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for year_str in matches:
                year = int(year_str)
                if year < current_year - 1:
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Outdated copyright year: {year}. "
                        f"Update to {current_year} or use dynamic year."
                    ))
                elif year > current_year:
                    issues.append(self._issue(
                        self.SEVERITY_INFO,
                        f"Copyright year is in the future: {year}."
                    ))

        return issues

    def _check_placeholder_content(self, soup):
        """Check for placeholder/dummy content."""
        issues = []
        text = soup.get_text().lower()

        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"Placeholder content detected matching pattern: '{pattern}'. "
                    f"Replace with actual content before going live."
                ))

        # Check for empty sections
        for section in soup.find_all(['section', 'article', 'aside']):
            content = section.get_text(strip=True)
            if len(content) < 10 and not section.find(['img', 'video', 'iframe', 'form', 'canvas']):
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    f"Nearly empty <{section.name}> section found.",
                    element=str(section)[:150]
                ))

        return issues

    def _check_content_length(self, soup, url):
        """Check if page has sufficient content."""
        issues = []

        # Get main text content (excluding navigation, header, footer)
        body = soup.find('body')
        if not body:
            return issues

        # Remove nav, header, footer for word count
        for tag in body.find_all(['nav', 'header', 'footer', 'script', 'style']):
            tag.decompose()

        text = body.get_text(strip=True)
        word_count = len(text.split())

        if word_count < 50:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Very thin content ({word_count} words). "
                f"Pages with less than 300 words may rank poorly in search engines."
            ))
        elif word_count < 200:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                f"Light content ({word_count} words). "
                f"Consider adding more substantive content (300+ words recommended)."
            ))

        return issues

    def _check_mobile_responsiveness(self, soup, html):
        """Check for mobile responsiveness indicators."""
        issues = []

        # Check viewport meta tag
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Missing viewport meta tag. Site won't display properly on mobile devices. "
                "Add: <meta name='viewport' content='width=device-width, initial-scale=1'>"
            ))

        # Check for fixed widths in inline styles
        fixed_width_elements = soup.find_all(True, style=re.compile(r'width\s*:\s*\d{4,}px'))
        if fixed_width_elements:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"{len(fixed_width_elements)} element(s) with fixed pixel widths > 999px. "
                f"Use percentage or max-width for responsive design."
            ))

        # Check for media queries in inline styles
        styles = soup.find_all('style')
        has_media_queries = False
        for style in styles:
            if '@media' in style.get_text():
                has_media_queries = True
                break

        # Also check linked stylesheets content
        if not has_media_queries:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "No CSS media queries detected in inline styles. "
                "Ensure your external CSS includes responsive breakpoints."
            ))

        return issues

    def _check_broken_media(self, soup):
        """Check for potential broken media references."""
        issues = []

        # Check images with suspicious srcs
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    "Image element without src attribute.",
                    element=str(img)[:150]
                ))
            elif src.startswith('data:') and len(src) < 50:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    "Possibly invalid base64 image (very short data URI).",
                    element=str(img)[:150]
                ))

        return issues

    def _check_contact_info(self, soup):
        """Check for proper contact information."""
        issues = []
        text = soup.get_text().lower()

        # Check for email address
        has_email = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))

        # Check for phone number
        has_phone = bool(re.search(r'[\+\(]?\d{1,3}[\-\.\s]?\(?\d{1,4}\)?[\-\.\s]?\d{1,4}[\-\.\s]?\d{1,9}', text))

        # Check for physical address
        has_address = bool(soup.find('address')) or bool(re.search(r'\b\d+\s+\w+\s+(?:street|st|road|rd|avenue|ave|drive|dr|lane|ln|way|blvd|boulevard)\b', text, re.I))

        if not has_email and not has_phone:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "No contact information (email or phone) found on this page."
            ))

        return issues

    def _check_social_media(self, soup):
        """Check for social media links."""
        issues = []
        social_platforms = ['facebook', 'twitter', 'x.com', 'instagram', 'youtube',
                          'linkedin', 'pinterest', 'tiktok']

        links = soup.find_all('a', href=True)
        found_social = set()
        for link in links:
            href = link.get('href', '').lower()
            for platform in social_platforms:
                if platform in href:
                    found_social.add(platform)

        if not found_social:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "No social media links found. "
                "Adding social media links improves discoverability and engagement."
            ))

        return issues

    def _check_text_readability(self, soup):
        """Basic readability checks."""
        issues = []

        # Check for very long paragraphs
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            word_count = len(text.split())
            if word_count > 200:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    f"Very long paragraph ({word_count} words). "
                    f"Break into shorter paragraphs for better readability.",
                    element=text[:100] + '...'
                ))

        # Check for text in ALL CAPS
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'span']):
            text = tag.get_text(strip=True)
            if len(text) > 20 and text == text.upper() and text != text.lower():
                # Check if it's not CSS text-transform
                style = tag.get('style', '')
                if 'text-transform' not in style:
                    issues.append(self._issue(
                        self.SEVERITY_INFO,
                        f"Text in ALL CAPS detected: \"{text[:50]}...\". "
                        f"Use CSS text-transform: uppercase instead.",
                    ))

        return issues

    def _check_navigation_consistency(self, soup):
        """Check navigation structure."""
        issues = []

        nav = soup.find('nav') or soup.find(True, class_=re.compile(r'nav|menu', re.I))
        if nav:
            links = nav.find_all('a')
            empty_nav_links = 0
            for link in links:
                href = link.get('href')
                if not href:
                    empty_nav_links += 1

            if empty_nav_links > 0:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"{empty_nav_links} navigation link(s) without href attribute. "
                    f"These are not clickable and not keyboard accessible."
                ))

        return issues
