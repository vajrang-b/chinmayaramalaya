# Chinmaya Ramalaya Website Audit & Fixed Site Repository

This repository contains:
1. **`website/`**: The complete updated website with all structural, SEO, accessibility, security, and content flaws fixed, preserved with its original visual layout. Ready to deploy directly to **GitHub Pages**.
2. **`reports/`**: The automated audit results, interactive HTML report (`reports/chinmayaramalaya.org/report.html`), screenshots, and raw JSON datasets.
3. **`validate.py`**: The complete reusable website validator tool.

---

## 📁 Repository Structure

```
chinmayaramalaya/
├── website/                   # 🌐 Standalone Fixed Website (Deploy to GitHub Pages)
│   ├── index.html
│   ├── aboutus.html
│   ├── registration.html
│   ├── balavihar.html
│   ├── youth-activities.html
│   ├── yoga-registration.html
│   ├── activities.html
│   ├── gallery.html
│   ├── downloads.html
│   ├── Sthothraanjali.html
│   ├── crowdfund.html
│   ├── donate.html
│   ├── contactus.html
│   ├── summerpicnic2026.html
│   ├── specialeventjuly2026.html
│   ├── terms.html
│   ├── privacy.html
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── pdfs/
│   ├── robots.txt
│   └── sitemap.xml
│
├── reports/                   # 📊 Audit Reports & Data
│   └── chinmayaramalaya.org/
│       ├── report.html        # Interactive HTML Dashboard
│       ├── summary.json
│       ├── raw/               # Category JSON Datasets
│       └── screenshots/       # 32 Desktop & Mobile Screenshots
│
├── validators/                # 🔬 Audit Modules (HTML, SEO, A11y, Perf, Security, Links, Content)
├── crawler.py                 # 📡 Playwright Web Crawler Engine
├── report_generator.py        # 📊 Report Generator
└── validate.py                # 🚀 Main CLI Entry Point
```

---

## 🚀 How to Host the Updated Website on GitHub Pages

To showcase the updated website on GitHub Pages:

### Method 1: Push Repository to GitHub & Enable GitHub Pages
1. Push this workspace to your GitHub repository:
   ```bash
   git add .
   git commit -m "Add audited & updated chinmayaramalaya website"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/chinmayaramalaya.git
   git push -u origin main
   ```
2. Go to your GitHub Repository **Settings** > **Pages**.
3. Under **Build and deployment**:
   - **Source**: Select `Deploy from a branch`
   - **Branch**: Select `main` and folder `/website` (or `/root` if using gh-pages branch).
4. Click **Save**. Your site will be live at:
   `https://YOUR_USERNAME.github.io/chinmayaramalaya/`

---

## 🔍 How to Re-Run the Website Validator Tool

You can run the validator on any live URL at any time:

```bash
source .venv/bin/activate
python validate.py https://www.chinmayaramalaya.org/ --max-pages 50
```
