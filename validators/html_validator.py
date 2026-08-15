"""
HTML Validator - Checks HTML structure, validity, and best practices.
"""

import re
from bs4 import BeautifulSoup


class HTMLValidator:
    """Validates HTML structure and standards compliance."""

    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    # Block-level elements that cannot be inside inline elements
    BLOCK_ELEMENTS = {
        'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'table', 'form', 'section', 'article',
        'aside', 'nav', 'header', 'footer', 'main', 'figure',
        'blockquote', 'pre', 'address', 'fieldset', 'details',
    }

    INLINE_ELEMENTS = {
        'a', 'span', 'strong', 'em', 'b', 'i', 'u', 'small',
        'sub', 'sup', 'abbr', 'cite', 'code', 'label',
    }

    DEPRECATED_TAGS = {
        'font', 'center', 'big', 'strike', 'tt', 'marquee',
        'blink', 'frame', 'frameset', 'noframes', 'applet',
        'basefont', 'dir', 'isindex', 'menu', 'plaintext',
        's', 'u',
    }

    DEPRECATED_ATTRIBUTES = {
        'align', 'bgcolor', 'border', 'cellpadding', 'cellspacing',
        'color', 'face', 'height', 'hspace', 'nowrap', 'size',
        'valign', 'vspace', 'width',
    }

    # Attributes that are OK on specific elements
    ATTRIBUTE_EXCEPTIONS = {
        'width': ['img', 'video', 'canvas', 'table', 'col', 'colgroup', 'iframe', 'svg'],
        'height': ['img', 'video', 'canvas', 'table', 'iframe', 'svg'],
        'border': ['table'],
        'size': ['input', 'select'],
        'color': ['input'],  # type=color
    }

    def validate(self, url, html):
        """Run all HTML validation checks."""
        issues = []
        soup = BeautifulSoup(html, 'html5lib')

        issues.extend(self._check_doctype(html))
        issues.extend(self._check_html_lang(soup))
        issues.extend(self._check_charset(soup))
        issues.extend(self._check_viewport(soup))
        issues.extend(self._check_nesting(soup))
        issues.extend(self._check_deprecated_tags(soup))
        issues.extend(self._check_deprecated_attributes(soup))
        issues.extend(self._check_duplicate_ids(soup))
        issues.extend(self._check_empty_tags(soup))
        issues.extend(self._check_inline_styles(soup))
        issues.extend(self._check_table_structure(soup))
        issues.extend(self._check_form_structure(soup))
        issues.extend(self._check_script_placement(soup, html))
        issues.extend(self._check_unclosed_tags(html))

        return {
            "url": url,
            "category": "html",
            "issues": issues,
            "score": self._calculate_score(issues),
        }

    def _issue(self, severity, message, element=None, line=None):
        issue = {
            "severity": severity,
            "message": message,
        }
        if element:
            issue["element"] = str(element)[:200]
        if line:
            issue["line"] = line
        return issue

    def _calculate_score(self, issues):
        """Calculate score out of 100 based on issues found."""
        score = 100
        for issue in issues:
            if issue["severity"] == self.SEVERITY_CRITICAL:
                score -= 10
            elif issue["severity"] == self.SEVERITY_WARNING:
                score -= 5
            elif issue["severity"] == self.SEVERITY_INFO:
                score -= 1
        return max(0, score)

    def _check_doctype(self, html):
        """Check for proper DOCTYPE declaration."""
        issues = []
        html_stripped = html.strip()
        if not html_stripped.lower().startswith('<!doctype'):
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Missing DOCTYPE declaration. Add <!DOCTYPE html> at the top."
            ))
        elif '<!doctype html>' not in html_stripped[:100].lower():
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                "Non-standard DOCTYPE. Use <!DOCTYPE html> for HTML5."
            ))
        return issues

    def _check_html_lang(self, soup):
        """Check for language attribute on <html> element."""
        issues = []
        html_tag = soup.find('html')
        if html_tag:
            lang = html_tag.get('lang')
            if not lang:
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    "Missing 'lang' attribute on <html> element. Required for accessibility.",
                    element="<html>"
                ))
            elif len(lang) < 2:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"Invalid language code '{lang}' on <html> element.",
                    element=f'<html lang="{lang}">'
                ))
        return issues

    def _check_charset(self, soup):
        """Check for character encoding declaration."""
        issues = []
        meta_charset = soup.find('meta', attrs={'charset': True})
        meta_content_type = soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})

        if not meta_charset and not meta_content_type:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Missing character encoding declaration. Add <meta charset='utf-8'>."
            ))
        elif meta_content_type and not meta_charset:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "Using http-equiv for charset. Consider using <meta charset='utf-8'> instead.",
                element=str(meta_content_type)
            ))
        return issues

    def _check_viewport(self, soup):
        """Check for viewport meta tag."""
        issues = []
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                "Missing viewport meta tag. Required for responsive design."
            ))
        else:
            content = viewport.get('content', '')
            if 'width=device-width' not in content:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    "Viewport meta tag missing 'width=device-width'.",
                    element=str(viewport)
                ))
        return issues

    def _check_nesting(self, soup):
        """Check for invalid HTML nesting."""
        issues = []

        # Check for block elements inside inline elements
        for inline_tag in soup.find_all(list(self.INLINE_ELEMENTS)):
            for child in inline_tag.find_all(list(self.BLOCK_ELEMENTS)):
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"Block element <{child.name}> found inside inline element <{inline_tag.name}>. "
                    f"This is invalid HTML nesting.",
                    element=f"<{inline_tag.name}>...<{child.name}>...</{child.name}>...</{inline_tag.name}>"
                ))

        # Check for <h*> tags inside <ul>/<ol> (common mistake)
        for list_tag in soup.find_all(['ul', 'ol']):
            for child in list_tag.children:
                if hasattr(child, 'name') and child.name and child.name not in ['li', 'script', 'template']:
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Invalid child <{child.name}> inside <{list_tag.name}>. "
                        f"Only <li> elements should be direct children of <{list_tag.name}>.",
                        element=f"<{list_tag.name}>...<{child.name}>...</{list_tag.name}>"
                    ))

        # Check for <p> inside <p>
        for p_tag in soup.find_all('p'):
            if p_tag.find('p'):
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    "Nested <p> elements found. Paragraphs cannot contain other paragraphs.",
                    element="<p>...<p>...</p>...</p>"
                ))

        # Check for interactive elements inside interactive elements
        for a_tag in soup.find_all('a'):
            nested_interactive = a_tag.find(['a', 'button', 'input', 'select', 'textarea'])
            if nested_interactive:
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"Interactive element <{nested_interactive.name}> nested inside <a>. "
                    f"This causes accessibility and UX issues.",
                    element=f"<a>...<{nested_interactive.name}>...</a>"
                ))

        return issues

    def _check_deprecated_tags(self, soup):
        """Check for deprecated HTML tags."""
        issues = []
        for tag_name in self.DEPRECATED_TAGS:
            tags = soup.find_all(tag_name)
            if tags:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"Deprecated tag <{tag_name}> found {len(tags)} time(s). Use CSS instead.",
                    element=f"<{tag_name}>"
                ))
        return issues

    def _check_deprecated_attributes(self, soup):
        """Check for deprecated HTML attributes."""
        issues = []
        for tag in soup.find_all(True):
            for attr in self.DEPRECATED_ATTRIBUTES:
                if tag.has_attr(attr):
                    # Check exceptions
                    exceptions = self.ATTRIBUTE_EXCEPTIONS.get(attr, [])
                    if tag.name not in exceptions:
                        issues.append(self._issue(
                            self.SEVERITY_INFO,
                            f"Deprecated attribute '{attr}' on <{tag.name}>. Use CSS instead.",
                            element=str(tag)[:150]
                        ))
        return issues

    def _check_duplicate_ids(self, soup):
        """Check for duplicate element IDs."""
        issues = []
        ids = {}
        for tag in soup.find_all(True, id=True):
            id_val = tag['id']
            if id_val in ids:
                issues.append(self._issue(
                    self.SEVERITY_CRITICAL,
                    f"Duplicate ID '{id_val}' found. IDs must be unique within a page.",
                    element=f'<{tag.name} id="{id_val}">'
                ))
            else:
                ids[id_val] = tag
        return issues

    def _check_empty_tags(self, soup):
        """Check for potentially problematic empty tags."""
        issues = []
        check_tags = ['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'td', 'th', 'li']
        for tag_name in check_tags:
            for tag in soup.find_all(tag_name):
                if not tag.get_text(strip=True) and not tag.find(['img', 'input', 'br', 'hr', 'iframe', 'video', 'audio', 'svg', 'canvas']):
                    # Skip if it has children with content
                    if not tag.find_all(True):
                        issues.append(self._issue(
                            self.SEVERITY_INFO,
                            f"Empty <{tag_name}> element found. Consider removing or adding content.",
                            element=str(tag)[:150]
                        ))
        return issues

    def _check_inline_styles(self, soup):
        """Check for excessive inline styles."""
        issues = []
        inline_styled = soup.find_all(True, style=True)
        if len(inline_styled) > 10:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Found {len(inline_styled)} elements with inline styles. "
                f"Consider moving styles to an external stylesheet for better maintainability."
            ))
        return issues

    def _check_table_structure(self, soup):
        """Check table structure for accessibility."""
        issues = []
        for table in soup.find_all('table'):
            if not table.find('thead') and not table.find('th'):
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    "Table found without <thead> or <th> elements. "
                    "Add table headers for accessibility.",
                    element=str(table)[:200]
                ))
            caption = table.find('caption')
            if not caption:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    "Table without <caption>. Consider adding a caption for accessibility.",
                    element=str(table)[:150]
                ))
        return issues

    def _check_form_structure(self, soup):
        """Check form elements have proper labels."""
        issues = []
        for form in soup.find_all('form'):
            inputs = form.find_all(['input', 'select', 'textarea'])
            for inp in inputs:
                inp_type = inp.get('type', 'text')
                if inp_type in ['hidden', 'submit', 'button', 'reset', 'image']:
                    continue
                inp_id = inp.get('id')
                has_label = False
                if inp_id:
                    has_label = bool(form.find('label', attrs={'for': inp_id}))
                if not has_label and not inp.get('aria-label') and not inp.get('aria-labelledby'):
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Form input <{inp.name} type='{inp_type}'> missing associated <label>.",
                        element=str(inp)[:150]
                    ))
        return issues

    def _check_script_placement(self, soup, html):
        """Check for render-blocking scripts in <head>."""
        issues = []
        head = soup.find('head')
        if head:
            scripts = head.find_all('script', src=True)
            for script in scripts:
                if not script.get('async') and not script.get('defer'):
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Render-blocking script in <head>: {script.get('src', '')[:100]}. "
                        f"Add 'async' or 'defer' attribute, or move to bottom of <body>.",
                        element=str(script)[:200]
                    ))
        return issues

    def _check_unclosed_tags(self, html):
        """Basic check for commonly unclosed tags using regex."""
        issues = []
        # Check for mismatched common tags
        void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                         'link', 'meta', 'param', 'source', 'track', 'wbr'}

        # Simple tag counting (not a full parser)
        tag_pattern = re.compile(r'<(/?)(\w+)[^>]*?(/?)>', re.IGNORECASE)
        tag_counts = {}
        for match in tag_pattern.finditer(html):
            is_closing = match.group(1) == '/'
            tag_name = match.group(2).lower()
            is_self_closing = match.group(3) == '/'

            if tag_name in void_elements or is_self_closing:
                continue

            if tag_name not in tag_counts:
                tag_counts[tag_name] = {'open': 0, 'close': 0}

            if is_closing:
                tag_counts[tag_name]['close'] += 1
            else:
                tag_counts[tag_name]['open'] += 1

        for tag, counts in tag_counts.items():
            diff = abs(counts['open'] - counts['close'])
            if diff > 0 and tag in ['div', 'span', 'p', 'section', 'article']:
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    f"Potential unclosed <{tag}> elements: {counts['open']} opening vs {counts['close']} closing tags.",
                ))

        return issues
