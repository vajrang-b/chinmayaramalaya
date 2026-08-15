#!/usr/bin/env python3
"""
Website Validator - Complete website audit tool.
Usage: python validate.py <url> [--output-dir reports] [--max-pages 50]

Performs comprehensive validation including:
- HTML validity
- SEO best practices
- Accessibility (WCAG 2.1 AA)
- Performance optimization
- Security headers & practices
- Broken link detection
- Content quality

Generates an interactive HTML report and JSON data files.
"""

import argparse
import json
import os
import sys
import time
from urllib.parse import urlparse

from crawler import WebCrawler
from validators.html_validator import HTMLValidator
from validators.seo_validator import SEOValidator
from validators.accessibility_validator import AccessibilityValidator
from validators.performance_validator import PerformanceValidator
from validators.security_validator import SecurityValidator
from validators.link_validator import LinkValidator
from validators.content_validator import ContentValidator
from report_generator import ReportGenerator


def print_banner():
    """Print a nice banner."""
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║          🔍 Website Validator & Auditor              ║")
    print("║     Complete SEO, A11y, Security & Performance       ║")
    print("║                    Audit Tool                        ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()


def print_progress_bar(current, total, prefix="", length=40):
    """Print a progress bar."""
    percent = current / total if total > 0 else 0
    filled = int(length * percent)
    bar = "█" * filled + "░" * (length - filled)
    print(f"\r  {prefix} |{bar}| {current}/{total} ({percent*100:.0f}%)", end="", flush=True)


def run_validation(url, output_dir="reports", max_pages=50):
    """Run the complete website validation pipeline."""
    start_time = time.time()
    parsed = urlparse(url)

    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    domain = parsed.netloc
    print(f"🌐 Target: {url}")
    print(f"📁 Output: {output_dir}/{domain.replace('www.', '')}/")
    print(f"📄 Max pages: {max_pages}")
    print()

    # ═══════════════════════════════════════════════
    # Phase 1: Crawl the website
    # ═══════════════════════════════════════════════
    print("━" * 55)
    print("📡 PHASE 1: Crawling website...")
    print("━" * 55)

    crawler = WebCrawler(url, output_dir=output_dir, max_pages=max_pages)
    crawl_results = crawler.crawl()

    print(f"\n  ✅ Crawled {len(crawl_results)} pages\n")

    # ═══════════════════════════════════════════════
    # Phase 2: Run all validators
    # ═══════════════════════════════════════════════
    print("━" * 55)
    print("🔬 PHASE 2: Running validation checks...")
    print("━" * 55)

    html_validator = HTMLValidator()
    seo_validator = SEOValidator()
    a11y_validator = AccessibilityValidator()
    perf_validator = PerformanceValidator()
    security_validator = SecurityValidator()
    link_validator = LinkValidator()
    content_validator = ContentValidator()

    validation_results = {}
    total_pages = len(crawl_results)

    # Prepare all_pages_data for cross-page checks
    all_pages_data = {}
    for page_url, result in crawl_results.items():
        all_pages_data[page_url] = {"html": result.html}

    for i, (page_url, result) in enumerate(crawl_results.items()):
        print_progress_bar(i + 1, total_pages, prefix="Validating")
        html = result.html

        page_results = []

        # HTML Validation
        page_results.append(html_validator.validate(page_url, html))

        # SEO Validation (only check sitemap/robots once)
        seo_result = seo_validator.validate(page_url, html,
                                            all_pages_data if i == 0 else None)
        # Only check sitemap/robots for first page
        if i > 0:
            seo_result["issues"] = [
                issue for issue in seo_result["issues"]
                if "sitemap" not in issue["message"].lower() and
                   "robots.txt" not in issue["message"].lower()
            ]
        page_results.append(seo_result)

        # Accessibility Validation
        page_results.append(a11y_validator.validate(page_url, html))

        # Performance Validation
        page_results.append(perf_validator.validate(page_url, html, result))

        # Security Validation
        page_results.append(security_validator.validate(page_url, html, result))

        # Content Validation
        page_results.append(content_validator.validate(page_url, html))

        validation_results[page_url] = page_results

    print()  # New line after progress bar

    # Link Validation (site-wide)
    print("\n  🔗 Checking links (internal + external)...")
    link_results = link_validator.validate_all(crawl_results)
    validation_results['__links__'] = link_results
    link_summary = link_results.get("summary", {})
    print(f"  ✅ Checked {link_summary.get('total_internal_links', 0)} internal, "
          f"{link_summary.get('total_external_links', 0)} external links")

    # ═══════════════════════════════════════════════
    # Phase 3: Generate reports
    # ═══════════════════════════════════════════════
    print()
    print("━" * 55)
    print("📊 PHASE 3: Generating report...")
    print("━" * 55)

    report_dir = os.path.join(output_dir, domain.replace("www.", ""))
    generator = ReportGenerator()
    report_path = generator.generate(url, crawl_results, validation_results, report_dir)

    # ═══════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════
    elapsed = time.time() - start_time

    # Load summary for display
    with open(os.path.join(report_dir, "summary.json"), "r") as f:
        summary = json.load(f)

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║                 AUDIT COMPLETE ✅                    ║")
    print("╠══════════════════════════════════════════════════════╣")

    overall = summary.get("overall_score", 0)
    emoji = "🟢" if overall >= 80 else ("🟡" if overall >= 50 else "🔴")
    print(f"║  {emoji} Overall Score: {overall}/100                          ║")
    print("║                                                      ║")

    total = summary.get("total_issues", {})
    print(f"║  🔴 Critical: {total.get('critical', 0):>3}  🟡 Warnings: {total.get('warning', 0):>3}  🔵 Info: {total.get('info', 0):>3}  ║")
    print("║                                                      ║")

    for cat, score in summary.get("category_scores", {}).items():
        cat_emoji = "🟢" if score >= 80 else ("🟡" if score >= 50 else "🔴")
        cat_name = cat.replace("_", " ").title()
        print(f"║  {cat_emoji} {cat_name:<20} {score:>3}/100                    ║")

    print("║                                                      ║")
    print(f"║  ⏱️  Completed in {elapsed:.1f}s                              ║")
    print(f"║  📄 Pages scanned: {summary.get('pages_scanned', 0):>3}                              ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  📊 Report: {report_path:<40}  ║")
    print(f"║  📁 JSON data: {report_dir + '/raw/':<37}  ║")
    print(f"║  📸 Screenshots: {report_dir + '/screenshots/':<35}  ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    return report_path


def main():
    parser = argparse.ArgumentParser(
        description="Complete Website Validator & Auditor Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate.py https://www.chinmayaramalaya.org/
  python validate.py https://example.com --max-pages 20
  python validate.py https://example.com --output-dir my_reports
        """
    )
    parser.add_argument(
        "url",
        help="URL of the website to audit (e.g., https://www.example.com)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="reports",
        help="Output directory for reports (default: reports)"
    )
    parser.add_argument(
        "--max-pages", "-m",
        type=int,
        default=50,
        help="Maximum number of pages to crawl (default: 50)"
    )

    args = parser.parse_args()

    print_banner()

    try:
        report_path = run_validation(args.url, args.output_dir, args.max_pages)
        print(f"✅ Open the report: file://{os.path.abspath(report_path)}")
        print()
    except KeyboardInterrupt:
        print("\n\n⚠️  Audit interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
