"""
Performance Validator - Checks page load performance and optimization opportunities.
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class PerformanceValidator:
    """Validates page performance and optimization."""

    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    # Thresholds
    MAX_PAGE_SIZE_KB = 3000  # 3MB
    MAX_IMAGE_SIZE_KB = 500  # 500KB per image
    MAX_CSS_FILES = 8
    MAX_JS_FILES = 8
    MAX_RESOURCES = 50
    GOOD_LOAD_TIME_MS = 3000
    ACCEPTABLE_LOAD_TIME_MS = 5000

    def validate(self, url, html, crawl_result=None):
        """Run all performance validation checks."""
        issues = []
        soup = BeautifulSoup(html, 'html5lib')

        issues.extend(self._check_page_size(crawl_result))
        issues.extend(self._check_load_time(crawl_result))
        issues.extend(self._check_resource_count(crawl_result))
        issues.extend(self._check_images(soup, crawl_result))
        issues.extend(self._check_css(soup, crawl_result))
        issues.extend(self._check_javascript(soup, html))
        issues.extend(self._check_fonts(soup, html))
        issues.extend(self._check_caching_hints(crawl_result))
        issues.extend(self._check_compression(crawl_result))
        issues.extend(self._check_render_blocking(soup))
        issues.extend(self._check_lazy_loading(soup))

        return {
            "url": url,
            "category": "performance",
            "issues": issues,
            "score": self._calculate_score(issues),
            "metrics": self._get_metrics(crawl_result),
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

    def _get_metrics(self, crawl_result):
        """Extract key performance metrics."""
        if not crawl_result:
            return {}
        return {
            "load_time_ms": crawl_result.load_time_ms,
            "ttfb_ms": crawl_result.ttfb_ms,
            "dom_content_loaded_ms": crawl_result.dom_content_loaded_ms,
            "total_resources": crawl_result.resource_count,
            "total_bytes": crawl_result.total_bytes,
            "total_kb": round(crawl_result.total_bytes / 1024, 1) if crawl_result.total_bytes else 0,
        }

    def _check_page_size(self, crawl_result):
        """Check total page size."""
        issues = []
        if not crawl_result:
            return issues

        total_kb = crawl_result.total_bytes / 1024 if crawl_result.total_bytes else 0
        html_kb = len(crawl_result.html) / 1024

        if total_kb > self.MAX_PAGE_SIZE_KB:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                f"Page total size is {total_kb:.0f}KB ({total_kb/1024:.1f}MB). "
                f"Target under {self.MAX_PAGE_SIZE_KB}KB for good performance."
            ))
        elif total_kb > self.MAX_PAGE_SIZE_KB / 2:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Page total size is {total_kb:.0f}KB. Consider optimizing."
            ))

        if html_kb > 100:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"HTML document is {html_kb:.0f}KB. Consider reducing HTML size."
            ))

        return issues

    def _check_load_time(self, crawl_result):
        """Check page load timing."""
        issues = []
        if not crawl_result or not crawl_result.load_time_ms:
            return issues

        load_time = crawl_result.load_time_ms

        if load_time > self.ACCEPTABLE_LOAD_TIME_MS:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                f"Page load time is {load_time:.0f}ms ({load_time/1000:.1f}s). "
                f"Target under {self.GOOD_LOAD_TIME_MS/1000:.0f}s for good UX."
            ))
        elif load_time > self.GOOD_LOAD_TIME_MS:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Page load time is {load_time:.0f}ms. "
                f"Good target is under {self.GOOD_LOAD_TIME_MS/1000:.0f}s."
            ))

        # TTFB check
        ttfb = crawl_result.ttfb_ms
        if ttfb and ttfb > 800:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Time to First Byte (TTFB) is {ttfb:.0f}ms. "
                f"Target under 600ms. This may indicate slow server response."
            ))

        return issues

    def _check_resource_count(self, crawl_result):
        """Check number of resources loaded."""
        issues = []
        if not crawl_result:
            return issues

        count = crawl_result.resource_count
        if count > self.MAX_RESOURCES:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Page loads {count} resources. Consider reducing to under {self.MAX_RESOURCES} "
                f"by combining/minifying CSS and JS files."
            ))

        return issues

    def _check_images(self, soup, crawl_result):
        """Check image optimization."""
        issues = []
        images = soup.find_all('img')

        # Check image formats
        non_modern = 0
        for img in images:
            src = img.get('src', '')
            if src:
                ext = src.split('.')[-1].lower().split('?')[0]
                if ext in ['bmp', 'tiff', 'tif']:
                    issues.append(self._issue(
                        self.SEVERITY_CRITICAL,
                        f"Image using unoptimized format ({ext}): {src.split('/')[-1][:50]}. "
                        f"Convert to WebP, AVIF, or at minimum JPEG/PNG.",
                        element=str(img)[:150]
                    ))
                elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                    non_modern += 1

        if non_modern > 3:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                f"{non_modern} images use traditional formats (JPEG/PNG). "
                f"Consider converting to WebP for 25-35% smaller file sizes."
            ))

        # Check for missing width/height (causes layout shift)
        for img in images:
            if not img.get('width') and not img.get('height'):
                style = img.get('style', '')
                if 'width' not in style and 'height' not in style:
                    src = img.get('src', 'unknown')
                    short_src = src.split('/')[-1][:50]
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Image without width/height: {short_src}. "
                        f"Set dimensions to prevent Cumulative Layout Shift (CLS).",
                        element=str(img)[:150]
                    ))

        return issues

    def _check_css(self, soup, crawl_result):
        """Check CSS optimization."""
        issues = []
        stylesheets = soup.find_all('link', rel='stylesheet')

        if len(stylesheets) > self.MAX_CSS_FILES:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Page loads {len(stylesheets)} CSS files. "
                f"Consider combining into fewer files to reduce HTTP requests."
            ))

        # Check for inline <style> blocks
        style_blocks = soup.find_all('style')
        total_inline_css = sum(len(s.get_text()) for s in style_blocks)
        if total_inline_css > 5000:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Large inline CSS ({total_inline_css} chars). "
                f"Move to external stylesheet for better caching."
            ))

        return issues

    def _check_javascript(self, soup, html):
        """Check JavaScript optimization."""
        issues = []
        scripts = soup.find_all('script', src=True)

        if len(scripts) > self.MAX_JS_FILES:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"Page loads {len(scripts)} JavaScript files. "
                f"Consider bundling/combining to reduce HTTP requests."
            ))

        # Check for jQuery loaded multiple times
        jquery_count = 0
        jquery_sources = []
        for script in scripts:
            src = script.get('src', '')
            if 'jquery' in src.lower():
                jquery_count += 1
                jquery_sources.append(src)

        if jquery_count > 1:
            issues.append(self._issue(
                self.SEVERITY_CRITICAL,
                f"jQuery loaded {jquery_count} times! This wastes bandwidth and can cause conflicts. "
                f"Sources: {', '.join(s.split('/')[-1] for s in jquery_sources)}"
            ))

        # Check for unminified scripts
        for script in scripts:
            src = script.get('src', '')
            filename = src.split('/')[-1].split('?')[0]
            if filename.endswith('.js') and not filename.endswith('.min.js') and 'jquery' not in filename.lower():
                issues.append(self._issue(
                    self.SEVERITY_INFO,
                    f"Potentially unminified JS: {filename}. Consider minifying for production.",
                ))

        return issues

    def _check_fonts(self, soup, html):
        """Check web font optimization."""
        issues = []
        
        font_links = soup.find_all('link', href=re.compile(r'fonts\.googleapis\.com|fonts\.gstatic\.com'))
        
        if font_links:
            # Check for font-display
            for link in font_links:
                href = link.get('href', '')
                if 'display=swap' not in href and 'display=optional' not in href:
                    issues.append(self._issue(
                        self.SEVERITY_WARNING,
                        f"Google Font loaded without display parameter. "
                        f"Add '&display=swap' to prevent invisible text during loading.",
                        element=str(link)[:200]
                    ))

            # Count font families
            family_count = 0
            for link in font_links:
                href = link.get('href', '')
                families = href.count('family=')
                pipes = href.count('|')
                family_count += max(families, pipes + 1)

            if family_count > 3:
                issues.append(self._issue(
                    self.SEVERITY_WARNING,
                    f"Loading {family_count} font families. "
                    f"Each font adds latency. Consider using 2-3 max."
                ))

        # Check for preconnect
        preconnects = soup.find_all('link', rel='preconnect')
        preconnect_domains = [p.get('href', '') for p in preconnects]
        
        if font_links and 'https://fonts.gstatic.com' not in preconnect_domains:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                "Missing preconnect for Google Fonts. "
                "Add <link rel='preconnect' href='https://fonts.gstatic.com' crossorigin> "
                "for faster font loading."
            ))

        return issues

    def _check_caching_hints(self, crawl_result):
        """Check for caching headers."""
        issues = []
        if not crawl_result or not crawl_result.response_headers:
            return issues

        headers = crawl_result.response_headers
        cache_control = headers.get('cache-control', '')
        expires = headers.get('expires', '')

        if not cache_control and not expires:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                "No Cache-Control or Expires header set. "
                "Configure caching to improve repeat visit performance."
            ))
        elif 'no-cache' in cache_control or 'no-store' in cache_control:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                f"Cache-Control is set to '{cache_control}'. "
                f"Consider allowing caching for static content."
            ))

        return issues

    def _check_compression(self, crawl_result):
        """Check for response compression."""
        issues = []
        if not crawl_result or not crawl_result.response_headers:
            return issues

        encoding = crawl_result.response_headers.get('content-encoding', '')
        if not encoding:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                "Response not compressed. Enable gzip or brotli compression "
                "on the server for significant bandwidth savings (60-80% for text)."
            ))

        return issues

    def _check_render_blocking(self, soup):
        """Check for render-blocking resources."""
        issues = []
        head = soup.find('head')
        if not head:
            return issues

        # CSS in head without media query is render-blocking
        blocking_css = head.find_all('link', rel='stylesheet')
        non_critical_css = []
        for css in blocking_css:
            media = css.get('media', 'all')
            href = css.get('href', '')
            filename = href.split('/')[-1][:50]
            if media == 'all' and 'bootstrap' not in href.lower():
                non_critical_css.append(filename)

        if len(non_critical_css) > 3:
            issues.append(self._issue(
                self.SEVERITY_INFO,
                f"{len(non_critical_css)} render-blocking CSS files in <head>. "
                f"Consider inlining critical CSS and loading the rest asynchronously."
            ))

        return issues

    def _check_lazy_loading(self, soup):
        """Check for lazy loading of below-fold images."""
        issues = []
        images = soup.find_all('img')

        images_without_lazy = 0
        for i, img in enumerate(images):
            loading = img.get('loading', '')
            if i > 0 and loading != 'lazy':  # Skip first image (likely above fold)
                images_without_lazy += 1

        if images_without_lazy > 3:
            issues.append(self._issue(
                self.SEVERITY_WARNING,
                f"{images_without_lazy} images without lazy loading. "
                f"Add loading='lazy' to below-the-fold images to improve initial page load."
            ))

        return issues
