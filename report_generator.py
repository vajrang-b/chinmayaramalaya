"""
Report Generator - Creates beautiful interactive HTML reports and JSON data files.
"""

import json
import os
from datetime import datetime
from urllib.parse import urlparse


class ReportGenerator:
    """Generates beautiful HTML reports from validation results."""

    def generate(self, base_url, crawl_results, validation_results, report_dir):
        """Generate HTML report and JSON data files."""
        # Save JSON data
        self._save_json_data(validation_results, report_dir)

        # Generate HTML report
        html = self._build_html_report(base_url, crawl_results, validation_results)
        report_path = os.path.join(report_dir, "report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        # Save summary JSON
        summary = self._build_summary(base_url, crawl_results, validation_results)
        with open(os.path.join(report_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)

        return report_path

    def _save_json_data(self, validation_results, report_dir):
        """Save raw validation data as JSON."""
        raw_dir = os.path.join(report_dir, "raw")
        os.makedirs(raw_dir, exist_ok=True)

        categories = {}
        for url, results in validation_results.items():
            if url == '__links__':
                with open(os.path.join(raw_dir, "link_validation.json"), "w") as f:
                    json.dump(results, f, indent=2)
                continue

            for result in results:
                cat = result.get("category", "unknown")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append({"url": url, **result})

        for cat, data in categories.items():
            with open(os.path.join(raw_dir, f"{cat}_issues.json"), "w") as f:
                json.dump(data, f, indent=2)

    def _build_summary(self, base_url, crawl_results, validation_results):
        """Build summary data."""
        total_issues = {"critical": 0, "warning": 0, "info": 0}
        category_scores = {}

        for url, results in validation_results.items():
            if url == '__links__':
                link_result = results
                for issue in link_result.get("issues", []):
                    total_issues[issue["severity"]] = total_issues.get(issue["severity"], 0) + 1
                category_scores["links"] = link_result.get("score", 0)
                continue

            for result in results:
                cat = result.get("category", "unknown")
                score = result.get("score", 100)
                if cat not in category_scores:
                    category_scores[cat] = []
                if isinstance(category_scores[cat], list):
                    category_scores[cat].append(score)
                for issue in result.get("issues", []):
                    sev = issue.get("severity", "info")
                    total_issues[sev] = total_issues.get(sev, 0) + 1

        # Average scores per category
        avg_scores = {}
        for cat, scores in category_scores.items():
            if isinstance(scores, list):
                avg_scores[cat] = round(sum(scores) / len(scores)) if scores else 100
            else:
                avg_scores[cat] = scores

        overall = round(sum(avg_scores.values()) / len(avg_scores)) if avg_scores else 0

        return {
            "url": base_url,
            "scan_date": datetime.now().isoformat(),
            "pages_scanned": len(crawl_results),
            "overall_score": overall,
            "category_scores": avg_scores,
            "total_issues": total_issues,
        }

    def _build_html_report(self, base_url, crawl_results, validation_results):
        """Build the complete HTML report."""
        summary = self._build_summary(base_url, crawl_results, validation_results)
        domain = urlparse(base_url).netloc

        # Collect all issues organized by page then by category
        pages_data = {}
        link_data = None

        for url, results in validation_results.items():
            if url == '__links__':
                link_data = results
                continue
            pages_data[url] = results

        # Build category colors
        category_colors = {
            "html": "#e74c3c",
            "seo": "#3498db",
            "accessibility": "#9b59b6",
            "performance": "#f39c12",
            "security": "#2ecc71",
            "links": "#1abc9c",
            "content": "#e67e22",
        }

        category_icons = {
            "html": "🧱",
            "seo": "🔍",
            "accessibility": "♿",
            "performance": "⚡",
            "security": "🔒",
            "links": "🔗",
            "content": "📝",
        }

        severity_colors = {
            "critical": "#e74c3c",
            "warning": "#f39c12",
            "info": "#3498db",
        }

        severity_icons = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵",
        }

        # Build screenshot gallery data
        screenshots = []
        for url, result in crawl_results.items():
            if result.screenshot_desktop:
                screenshots.append({
                    "url": url,
                    "desktop": os.path.basename(result.screenshot_desktop),
                    "mobile": os.path.basename(result.screenshot_mobile) if result.screenshot_mobile else None,
                })

        # Count issues per category
        category_issue_counts = {}
        for url, results in pages_data.items():
            for result in results:
                cat = result.get("category", "unknown")
                if cat not in category_issue_counts:
                    category_issue_counts[cat] = {"critical": 0, "warning": 0, "info": 0}
                for issue in result.get("issues", []):
                    sev = issue.get("severity", "info")
                    category_issue_counts[cat][sev] += 1

        if link_data:
            cat = "links"
            if cat not in category_issue_counts:
                category_issue_counts[cat] = {"critical": 0, "warning": 0, "info": 0}
            for issue in link_data.get("issues", []):
                sev = issue.get("severity", "info")
                category_issue_counts[cat][sev] += 1

        # Generate score cards HTML
        score_cards_html = ""
        for cat, score in summary["category_scores"].items():
            color = category_colors.get(cat, "#666")
            icon = category_icons.get(cat, "📋")
            counts = category_issue_counts.get(cat, {"critical": 0, "warning": 0, "info": 0})
            score_class = "score-good" if score >= 80 else ("score-ok" if score >= 50 else "score-bad")

            score_cards_html += f"""
            <div class="score-card" onclick="scrollToCategory('{cat}')">
                <div class="score-icon">{icon}</div>
                <div class="score-value {score_class}">{score}</div>
                <div class="score-label">{cat.replace('_', ' ').title()}</div>
                <div class="score-issues">
                    {'<span class="badge critical">' + str(counts["critical"]) + ' critical</span>' if counts["critical"] else ''}
                    {'<span class="badge warning">' + str(counts["warning"]) + ' warning</span>' if counts["warning"] else ''}
                    {'<span class="badge info">' + str(counts["info"]) + ' info</span>' if counts["info"] else ''}
                </div>
            </div>"""

        # Generate issues HTML organized by category
        issues_by_category = {}
        for url, results in pages_data.items():
            for result in results:
                cat = result.get("category", "unknown")
                if cat not in issues_by_category:
                    issues_by_category[cat] = []
                for issue in result.get("issues", []):
                    issues_by_category[cat].append({
                        "url": url,
                        "page": urlparse(url).path or "/",
                        **issue,
                    })

        if link_data:
            issues_by_category["links"] = []
            for issue in link_data.get("issues", []):
                issues_by_category["links"].append({
                    "url": base_url,
                    "page": "(site-wide)",
                    **issue,
                })

        category_sections_html = ""
        for cat in sorted(issues_by_category.keys()):
            issues = issues_by_category[cat]
            color = category_colors.get(cat, "#666")
            icon = category_icons.get(cat, "📋")
            score = summary["category_scores"].get(cat, 0)
            score_class = "score-good" if score >= 80 else ("score-ok" if score >= 50 else "score-bad")

            # Sort by severity
            severity_order = {"critical": 0, "warning": 1, "info": 2}
            issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 3))

            issues_html = ""
            for issue in issues:
                sev = issue.get("severity", "info")
                sev_icon = severity_icons.get(sev, "⚪")
                sev_color = severity_colors.get(sev, "#999")
                page = issue.get("page", "/")
                msg = issue.get("message", "")
                elem = issue.get("element", "")
                wcag = issue.get("wcag", "")

                issues_html += f"""
                <div class="issue-row severity-{sev}">
                    <div class="issue-severity" style="color: {sev_color}">{sev_icon} {sev.upper()}</div>
                    <div class="issue-content">
                        <div class="issue-page">{self._escape_html(page)}</div>
                        <div class="issue-message">{self._escape_html(msg)}</div>
                        {'<div class="issue-wcag">WCAG: ' + self._escape_html(wcag) + '</div>' if wcag else ''}
                        {'<div class="issue-element"><code>' + self._escape_html(elem) + '</code></div>' if elem else ''}
                    </div>
                </div>"""

            category_sections_html += f"""
            <div class="category-section" id="category-{cat}">
                <div class="category-header" onclick="toggleCategory('{cat}')">
                    <h2>{icon} {cat.replace('_', ' ').title()}</h2>
                    <div class="category-score {score_class}">{score}/100</div>
                    <div class="category-count">{len(issues)} issue{'s' if len(issues) != 1 else ''}</div>
                    <div class="category-toggle" id="toggle-{cat}">▼</div>
                </div>
                <div class="category-body" id="body-{cat}">
                    {issues_html}
                </div>
            </div>"""

        # Screenshots section
        screenshots_html = ""
        for ss in screenshots:
            page_name = urlparse(ss["url"]).path or "/"
            screenshots_html += f"""
            <div class="screenshot-card">
                <h4>{self._escape_html(page_name)}</h4>
                <div class="screenshot-pair">
                    <div class="screenshot-item">
                        <div class="screenshot-label">Desktop (1920×1080)</div>
                        <img src="screenshots/{ss['desktop']}" alt="Desktop view" loading="lazy" onclick="openModal(this.src)">
                    </div>
                    {'<div class="screenshot-item"><div class="screenshot-label">Mobile (375×812)</div><img src="screenshots/' + ss['mobile'] + '" alt="Mobile view" loading="lazy" onclick="openModal(this.src)"></div>' if ss.get('mobile') else ''}
                </div>
            </div>"""

        # Pages summary table
        pages_table_html = ""
        for url, result in crawl_results.items():
            path = urlparse(url).path or "/"
            status = result.status_code or "?"
            load_time = f"{result.load_time_ms:.0f}ms" if result.load_time_ms else "N/A"
            title = result.title or "(no title)"
            status_class = "status-ok" if status == 200 else "status-error"

            pages_table_html += f"""
            <tr>
                <td><a href="{self._escape_html(url)}" target="_blank">{self._escape_html(path)}</a></td>
                <td class="{status_class}">{status}</td>
                <td>{self._escape_html(title[:50])}</td>
                <td>{load_time}</td>
                <td>{len(result.images)}</td>
                <td>{len(result.internal_links)}</td>
                <td>{len(result.external_links)}</td>
            </tr>"""

        # Overall score display
        overall_score = summary["overall_score"]
        overall_class = "score-good" if overall_score >= 80 else ("score-ok" if overall_score >= 50 else "score-bad")

        # Full HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Audit Report - {self._escape_html(domain)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --bg-primary: #0f0f1a;
            --bg-secondary: #1a1a2e;
            --bg-tertiary: #16213e;
            --bg-card: #1e1e36;
            --text-primary: #e8e8f0;
            --text-secondary: #a0a0c0;
            --text-muted: #6a6a8a;
            --accent-gradient: linear-gradient(135deg, #667eea, #764ba2);
            --accent-color: #667eea;
            --border-color: #2a2a4a;
            --critical-color: #ff4757;
            --warning-color: #ffa502;
            --info-color: #3498db;
            --success-color: #2ed573;
        }}

        body {{
            font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}

        .report-header {{
            background: var(--accent-gradient);
            padding: 40px 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .report-header::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 30% 50%, rgba(255,255,255,0.1), transparent 60%);
        }}

        .report-header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 8px;
            position: relative;
        }}

        .report-header .domain {{
            font-size: 1.2rem;
            opacity: 0.9;
            position: relative;
        }}

        .report-header .scan-date {{
            font-size: 0.85rem;
            opacity: 0.7;
            margin-top: 8px;
            position: relative;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        /* Overall Score */
        .overall-section {{
            text-align: center;
            padding: 40px 20px;
            margin: -30px auto 30px;
            max-width: 300px;
            background: var(--bg-card);
            border-radius: 20px;
            border: 1px solid var(--border-color);
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        .overall-score {{
            font-size: 5rem;
            font-weight: 800;
            line-height: 1;
        }}

        .overall-label {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 8px;
        }}

        .score-good {{ color: var(--success-color); }}
        .score-ok {{ color: var(--warning-color); }}
        .score-bad {{ color: var(--critical-color); }}

        /* Issue Summary Bar */
        .summary-bar {{
            display: flex;
            justify-content: center;
            gap: 30px;
            padding: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}

        .summary-stat {{
            text-align: center;
            padding: 15px 25px;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            min-width: 120px;
        }}

        .summary-stat .stat-number {{
            font-size: 2rem;
            font-weight: 700;
        }}

        .summary-stat .stat-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* Score Cards */
        .score-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin-bottom: 40px;
        }}

        .score-card {{
            background: var(--bg-card);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            border: 1px solid var(--border-color);
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .score-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border-color: var(--accent-color);
        }}

        .score-icon {{ font-size: 2rem; margin-bottom: 8px; }}
        .score-value {{ font-size: 2.5rem; font-weight: 800; line-height: 1; }}
        .score-label {{ font-size: 0.85rem; color: var(--text-secondary); margin-top: 6px; text-transform: capitalize; }}

        .score-issues {{
            margin-top: 8px;
            display: flex;
            gap: 4px;
            justify-content: center;
            flex-wrap: wrap;
        }}

        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.7rem;
            font-weight: 600;
        }}

        .badge.critical {{ background: rgba(255,71,87,0.2); color: var(--critical-color); }}
        .badge.warning {{ background: rgba(255,165,2,0.2); color: var(--warning-color); }}
        .badge.info {{ background: rgba(52,152,219,0.2); color: var(--info-color); }}

        /* Category Sections */
        .category-section {{
            background: var(--bg-card);
            border-radius: 16px;
            border: 1px solid var(--border-color);
            margin-bottom: 16px;
            overflow: hidden;
        }}

        .category-header {{
            display: flex;
            align-items: center;
            padding: 16px 24px;
            cursor: pointer;
            gap: 16px;
            transition: background 0.2s;
        }}

        .category-header:hover {{
            background: var(--bg-tertiary);
        }}

        .category-header h2 {{
            font-size: 1.2rem;
            flex: 1;
        }}

        .category-score {{
            font-size: 1.1rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 8px;
            background: var(--bg-primary);
        }}

        .category-count {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        .category-toggle {{
            color: var(--text-muted);
            font-size: 0.8rem;
            transition: transform 0.3s;
        }}

        .category-toggle.collapsed {{
            transform: rotate(-90deg);
        }}

        .category-body {{
            border-top: 1px solid var(--border-color);
            max-height: 2000px;
            overflow: hidden;
            transition: max-height 0.5s ease;
        }}

        .category-body.collapsed {{
            max-height: 0;
            border-top: none;
        }}

        /* Issue Rows */
        .issue-row {{
            display: flex;
            gap: 16px;
            padding: 14px 24px;
            border-bottom: 1px solid rgba(42,42,74,0.5);
            transition: background 0.2s;
        }}

        .issue-row:hover {{
            background: var(--bg-tertiary);
        }}

        .issue-row:last-child {{ border-bottom: none; }}

        .issue-severity {{
            min-width: 90px;
            font-weight: 700;
            font-size: 0.75rem;
            padding-top: 2px;
        }}

        .issue-content {{ flex: 1; }}

        .issue-page {{
            font-size: 0.75rem;
            color: var(--accent-color);
            margin-bottom: 2px;
            font-family: monospace;
        }}

        .issue-message {{
            font-size: 0.9rem;
            line-height: 1.5;
        }}

        .issue-wcag {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 4px;
            font-style: italic;
        }}

        .issue-element {{
            margin-top: 6px;
        }}

        .issue-element code {{
            font-size: 0.75rem;
            background: var(--bg-primary);
            padding: 4px 8px;
            border-radius: 4px;
            color: var(--text-secondary);
            display: inline-block;
            max-width: 100%;
            overflow-x: auto;
            word-break: break-all;
        }}

        /* Filter Controls */
        .filter-bar {{
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}

        .filter-btn {{
            padding: 6px 16px;
            border-radius: 20px;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }}

        .filter-label {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        /* Pages Table */
        .pages-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        .pages-table th {{
            text-align: left;
            padding: 12px 16px;
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .pages-table td {{
            padding: 10px 16px;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.9rem;
        }}

        .pages-table a {{
            color: var(--accent-color);
            text-decoration: none;
        }}

        .pages-table a:hover {{ text-decoration: underline; }}

        .status-ok {{ color: var(--success-color); font-weight: 600; }}
        .status-error {{ color: var(--critical-color); font-weight: 600; }}

        /* Screenshots */
        .screenshots-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 16px;
        }}

        .screenshot-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid var(--border-color);
        }}

        .screenshot-card h4 {{
            margin-bottom: 12px;
            color: var(--accent-color);
            font-family: monospace;
        }}

        .screenshot-pair {{
            display: flex;
            gap: 12px;
        }}

        .screenshot-item {{
            flex: 1;
        }}

        .screenshot-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 6px;
        }}

        .screenshot-item img {{
            width: 100%;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s;
            border: 1px solid var(--border-color);
        }}

        .screenshot-item img:hover {{
            transform: scale(1.02);
        }}

        /* Section headers */
        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin: 40px 0 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }}

        /* Image Modal */
        .modal {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            cursor: pointer;
            align-items: center;
            justify-content: center;
        }}

        .modal.active {{ display: flex; }}

        .modal img {{
            max-width: 95vw;
            max-height: 95vh;
            object-fit: contain;
            border-radius: 8px;
        }}

        /* Footer */
        .report-footer {{
            text-align: center;
            padding: 30px;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 60px;
            border-top: 1px solid var(--border-color);
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .report-header h1 {{ font-size: 1.8rem; }}
            .score-cards {{ grid-template-columns: repeat(2, 1fr); }}
            .screenshots-grid {{ grid-template-columns: 1fr; }}
            .issue-row {{ flex-direction: column; gap: 4px; }}
            .issue-severity {{ min-width: auto; }}
            .summary-bar {{ gap: 12px; }}
            .pages-table {{ font-size: 0.8rem; }}
            .screenshot-pair {{ flex-direction: column; }}
        }}

        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .score-card, .category-section {{
            animation: fadeIn 0.4s ease-out;
        }}

        /* Print styles */
        @media print {{
            body {{ background: white; color: black; }}
            .filter-bar, .category-toggle {{ display: none; }}
            .category-body.collapsed {{ max-height: none; }}
        }}
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
    <div class="report-header">
        <h1>🔍 Website Audit Report</h1>
        <div class="domain">{self._escape_html(domain)}</div>
        <div class="scan-date">Scanned on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} • {summary['pages_scanned']} pages analyzed</div>
    </div>

    <div class="container">
        <!-- Overall Score -->
        <div class="overall-section">
            <div class="overall-score {overall_class}">{overall_score}</div>
            <div class="overall-label">Overall Health Score</div>
        </div>

        <!-- Summary Stats -->
        <div class="summary-bar">
            <div class="summary-stat">
                <div class="stat-number" style="color: var(--critical-color)">{summary['total_issues']['critical']}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="summary-stat">
                <div class="stat-number" style="color: var(--warning-color)">{summary['total_issues']['warning']}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="summary-stat">
                <div class="stat-number" style="color: var(--info-color)">{summary['total_issues']['info']}</div>
                <div class="stat-label">Info</div>
            </div>
            <div class="summary-stat">
                <div class="stat-number" style="color: var(--success-color)">{summary['pages_scanned']}</div>
                <div class="stat-label">Pages</div>
            </div>
        </div>

        <!-- Category Scores -->
        <h2 class="section-title">📊 Category Scores</h2>
        <div class="score-cards">
            {score_cards_html}
        </div>

        <!-- Filter Controls -->
        <h2 class="section-title">📋 Detailed Findings</h2>
        <div class="filter-bar">
            <span class="filter-label">Filter by severity:</span>
            <button class="filter-btn active" onclick="filterIssues('all')">All</button>
            <button class="filter-btn" onclick="filterIssues('critical')">🔴 Critical</button>
            <button class="filter-btn" onclick="filterIssues('warning')">🟡 Warning</button>
            <button class="filter-btn" onclick="filterIssues('info')">🔵 Info</button>
        </div>

        <!-- Category Sections -->
        {category_sections_html}

        <!-- Pages Overview -->
        <h2 class="section-title">📄 Pages Overview</h2>
        <div class="category-section">
            <div style="overflow-x: auto;">
                <table class="pages-table">
                    <thead>
                        <tr>
                            <th>Page</th>
                            <th>Status</th>
                            <th>Title</th>
                            <th>Load Time</th>
                            <th>Images</th>
                            <th>Int. Links</th>
                            <th>Ext. Links</th>
                        </tr>
                    </thead>
                    <tbody>
                        {pages_table_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Screenshots -->
        <h2 class="section-title">📸 Visual Screenshots</h2>
        <div class="screenshots-grid">
            {screenshots_html}
        </div>
    </div>

    <!-- Image Modal -->
    <div class="modal" id="imageModal" onclick="closeModal()">
        <img id="modalImage" src="" alt="Full size screenshot">
    </div>

    <div class="report-footer">
        Generated by <strong>Website Validator Tool</strong> • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        <br>Powered by Playwright, BeautifulSoup & Python
    </div>

    <script>
        // Toggle category sections
        function toggleCategory(cat) {{
            const body = document.getElementById('body-' + cat);
            const toggle = document.getElementById('toggle-' + cat);
            body.classList.toggle('collapsed');
            toggle.classList.toggle('collapsed');
        }}

        // Scroll to category
        function scrollToCategory(cat) {{
            const elem = document.getElementById('category-' + cat);
            if (elem) {{
                elem.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                // Ensure it's expanded
                const body = document.getElementById('body-' + cat);
                if (body && body.classList.contains('collapsed')) {{
                    toggleCategory(cat);
                }}
            }}
        }}

        // Filter issues by severity
        function filterIssues(severity) {{
            const rows = document.querySelectorAll('.issue-row');
            rows.forEach(row => {{
                if (severity === 'all') {{
                    row.style.display = 'flex';
                }} else {{
                    row.style.display = row.classList.contains('severity-' + severity) ? 'flex' : 'none';
                }}
            }});

            // Update active button
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }}

        // Image modal
        function openModal(src) {{
            document.getElementById('modalImage').src = src;
            document.getElementById('imageModal').classList.add('active');
        }}

        function closeModal() {{
            document.getElementById('imageModal').classList.remove('active');
        }}

        // Keyboard support for modal
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModal();
        }});
    </script>
</body>
</html>"""

        return html

    def _escape_html(self, text):
        """Escape HTML special characters."""
        if not text:
            return ""
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
