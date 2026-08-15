# Chinmaya Ramalaya Website Audit & Fixed Site Repository

This repository contains:
1. **`docs/`**: The complete updated website with all structural, SEO, accessibility, security, and content flaws fixed, preserved with its original visual layout. Hosted via **GitHub Pages** `/docs` folder.
2. **`reports/`**: The automated audit results, interactive HTML report (`reports/chinmayaramalaya.org/report.html`), screenshots, and raw JSON datasets.
3. **`validate.py`**: The complete reusable website validator tool.

---

## 📁 Repository Structure

```
chinmayaramalaya/
├── docs/                      # 🌐 Standalone Fixed Website (GitHub Pages /docs folder)
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
├── validators/                # 🔬 Audit Modules
├── crawler.py                 # 📡 Playwright Web Crawler Engine
├── report_generator.py        # 📊 Report Generator
└── validate.py                # 🚀 Main CLI Entry Point
```

---

## 🚀 GitHub Pages Setup (2 Steps)

1. Run `git push` in your terminal:
   ```bash
   git push origin main
   ```
2. On GitHub:
   - Go to **Settings** > **Pages**
   - **Source**: `Deploy from a branch`
   - **Branch**: `main`
   - **Folder**: Select `/docs`
   - Click **Save**.

Your site will be live at:  
👉 **`https://vajrang-b.github.io/chinmayaramalaya/`**
