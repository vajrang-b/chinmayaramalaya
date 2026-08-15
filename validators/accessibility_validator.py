"""
Accessibility Validator - Checks WCAG 2.1 Level AA compliance.
"""

import re
from bs4 import BeautifulSoup


class AccessibilityValidator:
    """Validates accessibility (WCAG 2.1 Level AA) compliance."""

    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    LANDMARK_ROLES = ['banner', 'navigation', 'main', 'contentinfo', 'complementary',
                      'search', 'form', 'region']

    def validate(self, url, html):
        """Run all accessibility validation checks."""
        issues = []
        soup = BeautifulSoup(html, 'html5lib')

        issues.extend(self._check_language(soup))
        issues.extend(self._check_page_title(soup))
        issues.extend(self._check_landmarks(soup))
        issues.extend(self._check_skip_navigation(soup))
        issues.extend(self._check_images(soup))
        issues.extend(self._check_links(soup))
        issues.extend(self._check_forms(soup))
        issues.extend(self._check_tables(soup))
        issues.extend(self._check_color_and_contrast(soup))
        issues.extend(self._check_keyboard_navigation(soup))
        issues.extend(self._check_aria(soup))
        issues.extend(self._check_media(soup))
        issues.extend(self._check_semantic_html(soup))
        issues.extend(self._check_focus_management(soup))

        return {
            "url": url,
            "category": "accessibility",
            "issues": issues,
            "score": self._calculate_score(issues),
            "wcag_level": "AA",
        }

    def _issue(self, severity, message, wcag_criteria=None, element=None):
        issue = {"severity": severity, "message": message}
        if wcag_criteria:
            issue["wcag"] = wcag_criteria
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

    def _check_language(self, soup):
        """WCAG 3.1.1 - Language of Page."""
        issues = []
        html_tag = soup.find('html')
        if html_tag:
            lang = html_tag.get('lang')
            if not lang:
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    "Page language not specified. Add lang attribute to <html> element.",
                    wcag_criteria="3.1.1 Language of Page (Level A)"
                ))
            dir_attr = html_tag.get('dir')
            if not dir_attr:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    "Text direction not specified. Consider adding dir='ltr' to <html>.",
                    wcag_criteria="1.3.2 Meaningful Sequence"
                ))
        return issues

    def _check_page_title(self, soup):
        """WCAG 2.4.2 - Page Titled."""
        issues = []
        title = soup.find('title')
        if not title or not title.get_text(strip=True):
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Page has no title. Every page must have a descriptive title.",
                wcag_criteria="2.4.2 Page Titled (Level A)"
            ))
        return issues

    def _check_landmarks(self, soup):
        """WCAG 1.3.1 - Landmarks and regions."""
        issues = []

        # Check for main landmark
        main = soup.find('main') or soup.find(True, attrs={'role': 'main'})
        if not main:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                "No <main> landmark found. Use <main> element or role='main' "
                "to identify the primary content area.",
                wcag_criteria="1.3.1 Info and Relationships (Level A)"
            ))

        # Check for nav landmark
        nav = soup.find('nav') or soup.find(True, attrs={'role': 'navigation'})
        if not nav:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                "No <nav> landmark found. Use <nav> element for navigation sections.",
                wcag_criteria="1.3.1 Info and Relationships (Level A)"
            ))

        # Check for banner (header) landmark
        header = soup.find('header') or soup.find(True, attrs={'role': 'banner'})
        if not header:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "No <header> (banner) landmark found.",
                wcag_criteria="1.3.1 Info and Relationships (Level A)"
            ))

        return issues

    def _check_skip_navigation(self, soup):
        """WCAG 2.4.1 - Bypass Blocks."""
        issues = []
        # Check for skip navigation link
        skip_link = soup.find('a', href='#main') or soup.find('a', href='#content')
        body = soup.find('body')
        if body:
            first_link = body.find('a')
            if first_link:
                href = first_link.get('href', '')
                text = first_link.get_text(strip=True).lower()
                if 'skip' in text or 'main' in text:
                    skip_link = first_link

        if not skip_link:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                "No skip navigation link found. Add a 'Skip to main content' link "
                "as the first focusable element for keyboard users.",
                wcag_criteria="2.4.1 Bypass Blocks (Level A)"
            ))
        return issues

    def _check_images(self, soup):
        """WCAG 1.1.1 - Non-text Content."""
        issues = []
        images = soup.find_all('img')

        for img in images:
            src = img.get('src', 'unknown')
            short_src = src.split('/')[-1][:50] if src else 'unknown'

            if not img.has_attr('alt'):
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"Image missing alt attribute: {short_src}",
                    wcag_criteria="1.1.1 Non-text Content (Level A)",
                    element=str(img)[:150]
                ))

            # Check for images used as buttons/links without alt
            parent = img.parent
            if parent and parent.name == 'a':
                alt = img.get('alt', '')
                link_text = parent.get_text(strip=True)
                if not alt and not link_text:
                    issues.append(self._issue(
                        self.SEVERITY_CRITICAL,
                        f"Linked image without alt text or link text: {short_src}. "
                        f"Screen readers cannot determine the link purpose.",
                        wcag_criteria="1.1.1 Non-text Content (Level A)"
                    ))

        # Check SVGs
        for svg in soup.find_all('svg'):
            title = svg.find('title')
            aria_label = svg.get('aria-label')
            aria_hidden = svg.get('aria-hidden')
            if not title and not aria_label and aria_hidden != 'true':
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    "SVG without accessible name. Add <title> inside SVG, "
                    "aria-label, or aria-hidden='true' if decorative.",
                    wcag_criteria="1.1.1 Non-text Content (Level A)"
                ))

        return issues

    def _check_links(self, soup):
        """WCAG 2.4.4 - Link Purpose."""
        issues = []
        links = soup.find_all('a')

        empty_links = 0
        generic_links = 0
        no_href_links = 0

        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            aria_label = link.get('aria-label', '')
            title = link.get('title', '')

            # Check for links without href
            if not href:
                no_href_links += 1

            # Check for links without text
            accessible_name = text or aria_label or title
            img = link.find('img')
            if img:
                accessible_name = accessible_name or img.get('alt', '')

            if not accessible_name:
                empty_links += 1

            # Check for ambiguous link text
            generic_texts = ['click here', 'here', 'read more', 'more', 'link', 'click']
            if text.lower().strip() in generic_texts:
                generic_links += 1

            # Check for new window warning
            target = link.get('target', '')
            if target == '_blank' and 'opens in' not in (aria_label + title).lower():
                rel = link.get('rel', [])
                if isinstance(rel, list):
                    rel = ' '.join(rel)
                if 'noopener' not in str(rel):
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Link opens in new window without noopener: "
                        f"{text[:40] or href[:40] if href else 'unknown'}",
                        wcag_criteria="3.2.5 Change on Request"
                    ))

        if empty_links > 0:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                f"{empty_links} link(s) without accessible text. "
                f"All links must have descriptive text or aria-label.",
                wcag_criteria="2.4.4 Link Purpose (Level A)"
            ))

        if no_href_links > 0:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"{no_href_links} <a> element(s) without href attribute. "
                f"Links without href are not keyboard accessible.",
                wcag_criteria="2.1.1 Keyboard (Level A)"
            ))

        if generic_links > 0:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"{generic_links} link(s) with generic text (e.g., 'click here', 'read more'). "
                f"Use descriptive link text that explains the destination.",
                wcag_criteria="2.4.4 Link Purpose (Level A)"
            ))

        return issues

    def _check_forms(self, soup):
        """WCAG 1.3.1 & 3.3.2 - Form accessibility."""
        issues = []
        
        inputs = soup.find_all(['input', 'select', 'textarea'])
        for inp in inputs:
            inp_type = inp.get('type', 'text')
            if inp_type in ['hidden', 'submit', 'button', 'reset']:
                continue

            inp_id = inp.get('id')
            has_label = False

            if inp_id:
                label = soup.find('label', attrs={'for': inp_id})
                if label:
                    has_label = True

            aria_label = inp.get('aria-label')
            aria_labelledby = inp.get('aria-labelledby')
            placeholder = inp.get('placeholder')

            if not has_label and not aria_label and not aria_labelledby:
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"Form control <{inp.name} type='{inp_type}'> without label. "
                    f"{'Has placeholder but placeholder is not a substitute for a label. ' if placeholder else ''}"
                    f"Add <label for='id'> or aria-label.",
                    wcag_criteria="3.3.2 Labels or Instructions (Level A)",
                    element=str(inp)[:150]
                ))

        # Check for form submit buttons
        for form in soup.find_all('form'):
            submit = form.find('input', type='submit') or form.find('button', type='submit') or form.find('button')
            if not submit:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    "Form without a visible submit button.",
                    wcag_criteria="3.2.2 On Input (Level A)"
                ))

        return issues

    def _check_tables(self, soup):
        """WCAG 1.3.1 - Table accessibility."""
        issues = []
        tables = soup.find_all('table')

        for table in tables:
            # Check for table headers
            th_elements = table.find_all('th')
            if not th_elements:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    "Data table without header cells (<th>). "
                    "Add <th> elements for screen reader users.",
                    wcag_criteria="1.3.1 Info and Relationships (Level A)"
                ))

            # Check for scope on th
            for th in th_elements:
                if not th.get('scope'):
                    issues.append(self._issue(
                        self.SEVERITY_INFO,
                        "Table header <th> without scope attribute. "
                        "Add scope='col' or scope='row'.",
                        wcag_criteria="1.3.1 Info and Relationships (Level A)"
                    ))

        return issues

    def _check_color_and_contrast(self, soup):
        """WCAG 1.4.3 - Contrast and color usage notes."""
        issues = []

        # Check for color-only information indicators
        # This is a heuristic check - full contrast analysis requires rendered styles
        style_tags = soup.find_all('style')
        inline_styles = soup.find_all(True, style=True)

        color_only_patterns = [
            r'color\s*:\s*red',
            r'color\s*:\s*green',
            r'border-color\s*:\s*red',
        ]

        for style in style_tags:
            text = style.get_text()
            for pattern in color_only_patterns:
                if re.search(pattern, text, re.I):
                    issues.append(self._issue(
                        self.SEVERITY_INFO,
                        "Possible use of color alone to convey information. "
                        "Ensure color is not the only visual means of conveying information.",
                        wcag_criteria="1.4.1 Use of Color (Level A)"
                    ))
                    break

        issues.append(self._issue(
            self.SEVERITY_INFO,
            "Manual color contrast check recommended. Use a tool like "
            "WebAIM Contrast Checker to verify all text meets WCAG AA ratio (4.5:1 for normal text).",
            wcag_criteria="1.4.3 Contrast (Minimum) (Level AA)"
        ))

        return issues

    def _check_keyboard_navigation(self, soup):
        """WCAG 2.1.1 - Keyboard accessibility."""
        issues = []

        # Check for positive tabindex (disrupts natural tab order)
        positive_tabindex = soup.find_all(True, attrs={'tabindex': True})
        for elem in positive_tabindex:
            try:
                tabindex = int(elem.get('tabindex', 0))
                if tabindex > 0:
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Positive tabindex={tabindex} on <{elem.name}>. "
                        f"Avoid positive tabindex values as they disrupt natural tab order.",
                        wcag_criteria="2.4.3 Focus Order (Level A)",
                        element=str(elem)[:150]
                    ))
            except ValueError:
                pass

        # Check for mouse-only event handlers
        mouse_events = ['onclick', 'onmouseover', 'onmouseout', 'onmousedown', 'onmouseup']
        keyboard_events = ['onkeypress', 'onkeydown', 'onkeyup', 'onfocus', 'onblur']

        for event in mouse_events:
            elements = soup.find_all(True, attrs={event: True})
            for elem in elements:
                has_keyboard = any(elem.get(ke) for ke in keyboard_events)
                if not has_keyboard and elem.name not in ['a', 'button', 'input', 'select', 'textarea']:
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Element <{elem.name}> has {event} but no keyboard equivalent. "
                        f"Ensure all functionality is keyboard accessible.",
                        wcag_criteria="2.1.1 Keyboard (Level A)"
                    ))

        return issues

    def _check_aria(self, soup):
        """Check ARIA usage."""
        issues = []

        # Check for aria-hidden on focusable elements
        aria_hidden = soup.find_all(True, attrs={'aria-hidden': 'true'})
        for elem in aria_hidden:
            focusable = elem.find(['a', 'button', 'input', 'select', 'textarea'])
            if focusable and focusable.get('tabindex') != '-1':
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"aria-hidden='true' on element containing focusable child <{focusable.name}>. "
                    f"This creates a confusing experience for screen reader users.",
                    wcag_criteria="4.1.2 Name, Role, Value (Level A)"
                ))

        return issues

    def _check_media(self, soup):
        """WCAG 1.2 - Time-based Media."""
        issues = []

        videos = soup.find_all(['video', 'iframe'])
        for video in videos:
            src = video.get('src', '') or video.get('data-src', '')
            if 'youtube' in src or 'vimeo' in src or video.name == 'video':
                track = video.find('track', kind='captions')
                if not track and video.name == 'video':
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        "Video without captions track. Add <track kind='captions'>.",
                        wcag_criteria="1.2.2 Captions (Level A)"
                    ))

        audios = soup.find_all('audio')
        for audio in audios:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "Audio content found. Ensure a text transcript is available.",
                wcag_criteria="1.2.1 Audio-only (Level A)"
            ))

        return issues

    def _check_semantic_html(self, soup):
        """Check for proper semantic HTML usage."""
        issues = []

        # Check for div/span used for clickable behavior without proper roles
        divs_with_onclick = soup.find_all('div', attrs={'onclick': True})
        spans_with_onclick = soup.find_all('span', attrs={'onclick': True})

        for elem in divs_with_onclick + spans_with_onclick:
            role = elem.get('role')
            if role not in ['button', 'link', 'tab', 'menuitem']:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"<{elem.name}> with onclick but no ARIA role. "
                    f"Use a <button> or add role='button' with keyboard support.",
                    wcag_criteria="4.1.2 Name, Role, Value (Level A)"
                ))

        return issues

    def _check_focus_management(self, soup):
        """Check for visible focus indicators."""
        issues = []

        # Check if CSS removes focus outlines
        styles = soup.find_all('style')
        for style in styles:
            text = style.get_text()
            if re.search(r'outline\s*:\s*(none|0)', text):
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    "CSS rule 'outline: none' or 'outline: 0' detected. "
                    "Never remove focus indicators without providing visible alternatives.",
                    wcag_criteria="2.4.7 Focus Visible (Level AA)"
                ))

        return issues
