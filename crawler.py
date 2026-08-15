"""
Crawler module - Uses Playwright to crawl all pages on a website.
Discovers links, captures screenshots, measures timing, extracts HTML.
"""

import json
import os
import time
import re
from urllib.parse import urljoin, urlparse, urlunparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class CrawlResult:
    """Result of crawling a single page."""
    def __init__(self, url):
        self.url = url
        self.status_code = None
        self.html = ""
        self.title = ""
        self.load_time_ms = 0
        self.ttfb_ms = 0
        self.dom_content_loaded_ms = 0
        self.resource_count = 0
        self.total_bytes = 0
        self.resources = []
        self.internal_links = []
        self.external_links = []
        self.images = []
        self.scripts = []
        self.stylesheets = []
        self.screenshot_desktop = None
        self.screenshot_mobile = None
        self.errors = []
        self.console_errors = []
        self.response_headers = {}

    def to_dict(self):
        return {
            "url": self.url,
            "status_code": self.status_code,
            "title": self.title,
            "load_time_ms": self.load_time_ms,
            "ttfb_ms": self.ttfb_ms,
            "dom_content_loaded_ms": self.dom_content_loaded_ms,
            "resource_count": self.resource_count,
            "total_bytes": self.total_bytes,
            "resources": self.resources,
            "internal_links": self.internal_links,
            "external_links": self.external_links,
            "images": self.images,
            "scripts": self.scripts,
            "stylesheets": self.stylesheets,
            "screenshot_desktop": self.screenshot_desktop,
            "screenshot_mobile": self.screenshot_mobile,
            "errors": self.errors,
            "console_errors": self.console_errors,
            "response_headers": self.response_headers,
            "html_length": len(self.html),
        }


class WebCrawler:
    """Crawls a website using Playwright, discovers all pages, and extracts data."""

    def __init__(self, base_url, output_dir="reports", max_pages=100, timeout=30000):
        self.base_url = base_url.rstrip("/")
        parsed = urlparse(self.base_url)
        self.domain = parsed.netloc
        self.scheme = parsed.scheme
        self.output_dir = output_dir
        self.max_pages = max_pages
        self.timeout = timeout
        self.visited = set()
        self.to_visit = set()
        self.results = {}
        self.all_links = set()

        # Create output directories
        domain_dir = self.domain.replace("www.", "")
        self.report_dir = os.path.join(output_dir, domain_dir)
        self.screenshots_dir = os.path.join(self.report_dir, "screenshots")
        self.pages_dir = os.path.join(self.report_dir, "pages")
        self.raw_dir = os.path.join(self.report_dir, "raw")
        for d in [self.screenshots_dir, self.pages_dir, self.raw_dir]:
            os.makedirs(d, exist_ok=True)

    def _normalize_url(self, url):
        """Normalize a URL for comparison."""
        parsed = urlparse(url)
        # Remove fragment
        normalized = urlunparse((
            parsed.scheme or self.scheme,
            parsed.netloc or self.domain,
            parsed.path.rstrip("/") or "/",
            parsed.params,
            parsed.query,
            ""  # remove fragment
        ))
        return normalized

    def _is_same_domain(self, url):
        """Check if URL belongs to the same domain."""
        parsed = urlparse(url)
        if not parsed.netloc:
            return True
        return parsed.netloc == self.domain or parsed.netloc == self.domain.replace("www.", "")

    def _is_page_url(self, url):
        """Check if URL is a crawlable page (not a file download)."""
        parsed = urlparse(url)
        path = parsed.path.lower().rstrip('/')

        # No extension or .html/.htm = page
        if '.' not in path.split('/')[-1]:
            return True
        ext = path.split('.')[-1]
        if ext in ['html', 'htm', 'php', 'asp', 'aspx', 'jsp']:
            return True

        # Everything else is a resource, skip it
        return False

    def _extract_links(self, page, current_url):
        """Extract all links from a page."""
        internal = []
        external = []
        try:
            links = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    href: a.href,
                    text: a.textContent.trim().substring(0, 100),
                    rel: a.getAttribute('rel') || '',
                    target: a.getAttribute('target') || '',
                    is_visible: a.offsetParent !== null
                }));
            }""")
            for link in links:
                href = link['href']
                if not href or href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('tel:'):
                    continue
                full_url = urljoin(current_url, href)
                link_data = {
                    "url": full_url,
                    "text": link['text'],
                    "rel": link['rel'],
                    "target": link['target'],
                    "source_page": current_url,
                }
                if self._is_same_domain(full_url):
                    internal.append(link_data)
                    self.all_links.add(full_url)
                else:
                    external.append(link_data)
        except Exception as e:
            pass
        return internal, external

    def _extract_images(self, page):
        """Extract all images from a page."""
        try:
            return page.evaluate("""() => {
                return Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src,
                    alt: img.getAttribute('alt') || '',
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    loading: img.getAttribute('loading') || '',
                    has_alt: img.hasAttribute('alt'),
                }));
            }""")
        except Exception:
            return []

    def _extract_resources(self, page):
        """Extract scripts and stylesheets."""
        try:
            scripts = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('script[src]')).map(s => ({
                    src: s.src,
                    async: s.async,
                    defer: s.defer,
                }));
            }""")
            stylesheets = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => ({
                    href: l.href,
                    media: l.getAttribute('media') || 'all',
                }));
            }""")
            return scripts, stylesheets
        except Exception:
            return [], []

    def _capture_screenshot(self, page, url, viewport_name, width, height):
        """Capture a screenshot at a given viewport size."""
        try:
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(500)  # Let layout settle

            # Create safe filename from URL
            parsed = urlparse(url)
            path = parsed.path.strip("/") or "index"
            safe_name = re.sub(r'[^a-zA-Z0-9]', '-', path)
            filename = f"{safe_name}-{viewport_name}.png"
            filepath = os.path.join(self.screenshots_dir, filename)

            page.screenshot(path=filepath, full_page=True)
            return filepath
        except Exception as e:
            return None

    def _crawl_page(self, page, url, progress_callback=None):
        """Crawl a single page and extract all data."""
        result = CrawlResult(url)
        console_errors = []

        # Listen for console errors
        page.on("console", lambda msg: console_errors.append({
            "type": msg.type,
            "text": msg.text,
        }) if msg.type in ["error", "warning"] else None)

        try:
            # Track resources loaded
            resources = []

            def handle_response(response):
                try:
                    resources.append({
                        "url": response.url,
                        "status": response.status,
                        "content_type": response.headers.get("content-type", ""),
                        "size": int(response.headers.get("content-length", 0)),
                    })
                except Exception:
                    pass

            page.on("response", handle_response)

            # Navigate to page
            start_time = time.time()
            response = page.goto(url, wait_until="networkidle", timeout=self.timeout)
            load_time = (time.time() - start_time) * 1000

            if response:
                result.status_code = response.status
                result.response_headers = dict(response.headers)

                # Get timing
                try:
                    timing = page.evaluate("""() => {
                        const t = performance.timing;
                        return {
                            ttfb: t.responseStart - t.navigationStart,
                            domContentLoaded: t.domContentLoadedEventEnd - t.navigationStart,
                            loadComplete: t.loadEventEnd - t.navigationStart,
                        };
                    }""")
                    result.ttfb_ms = timing.get('ttfb', 0)
                    result.dom_content_loaded_ms = timing.get('domContentLoaded', 0)
                    result.load_time_ms = timing.get('loadComplete', 0) or load_time
                except Exception:
                    result.load_time_ms = load_time

            # Get page HTML
            result.html = page.content()

            # Get title
            result.title = page.title()

            # Extract links
            result.internal_links, result.external_links = self._extract_links(page, url)

            # Extract images
            result.images = self._extract_images(page)

            # Extract scripts and stylesheets
            result.scripts, result.stylesheets = self._extract_resources(page)

            # Store resources
            result.resources = resources
            result.resource_count = len(resources)
            result.total_bytes = sum(r.get("size", 0) for r in resources)

            # Console errors
            result.console_errors = console_errors

            # Capture screenshots
            result.screenshot_desktop = self._capture_screenshot(
                page, url, "desktop", 1920, 1080
            )
            result.screenshot_mobile = self._capture_screenshot(
                page, url, "mobile", 375, 812
            )

            # Add discovered internal links to visit queue
            for link in result.internal_links:
                link_url = self._normalize_url(link["url"])
                if (link_url not in self.visited and
                    self._is_page_url(link_url) and
                    self._is_same_domain(link_url)):
                    self.to_visit.add(link_url)

        except PlaywrightTimeout:
            result.errors.append(f"Timeout loading {url}")
            result.status_code = 0
        except Exception as e:
            result.errors.append(f"Error loading {url}: {str(e)}")
            result.status_code = 0

        return result

    def crawl(self, progress_callback=None):
        """Crawl the entire website starting from base_url."""
        self.to_visit.add(self._normalize_url(self.base_url))

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="ChinmayaRamalayaValidator/1.0 (Website Audit Tool)",
                viewport={"width": 1920, "height": 1080},
            )
            page = context.new_page()

            page_count = 0
            while self.to_visit and page_count < self.max_pages:
                url = self.to_visit.pop()
                if url in self.visited:
                    continue

                self.visited.add(url)
                page_count += 1

                if progress_callback:
                    progress_callback(page_count, url)

                print(f"  [{page_count}] Crawling: {url}")

                result = self._crawl_page(page, url, progress_callback)
                self.results[url] = result

                # Save per-page JSON
                parsed = urlparse(url)
                path = parsed.path.strip("/") or "index"
                safe_name = re.sub(r'[^a-zA-Z0-9]', '-', path)
                page_json = os.path.join(self.pages_dir, f"{safe_name}.json")
                with open(page_json, "w") as f:
                    json.dump(result.to_dict(), f, indent=2)

            browser.close()

        # Save crawl summary
        summary = {
            "base_url": self.base_url,
            "domain": self.domain,
            "pages_crawled": len(self.results),
            "total_links_discovered": len(self.all_links),
            "pages": {url: r.to_dict() for url, r in self.results.items()},
        }
        with open(os.path.join(self.raw_dir, "crawl_summary.json"), "w") as f:
            json.dump(summary, f, indent=2)

        return self.results
