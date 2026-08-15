# Chinmaya Ramalaya AI Agent Coding & Design Rules

## 1. Editorial Minimalist & Devotional Design System
- **Tone & Atmosphere**: Devotional, reverent, peaceful, clean, and spacious.
- **Forbidden UI Styles**:
  - ❌ **NO Neumorphism**: Avoid soft extruded plastic shadows or low-contrast light angles.
  - ❌ **NO Neo-Brutalism**: Avoid thick raw black borders, aggressive neon highlights, or chaotic layouts.
  - ❌ **NO Ad-hoc Colors**: Never invent random accent colors.

## 2. Strict Brand Color Palette & CSS Variables
All styling must strictly use the predefined brand design tokens from `docs/css/theme.css` / `docs/css/custom.css`:
- `--primary-maroon`: `#8b0000` (Headers, main titles, primary buttons)
- `--primary-maroon-hover`: `#6d0000` (Button hover states)
- `--saffron-gold`: `#c89b3c` (Subheadings, borders, gold CTA buttons, icons)
- `--saffron-gold-hover`: `#b0852e` (Gold button hover states)
- `--saffron-light-bg`: `#fdf6ea` (Soft saffron background tint for chips and badges)
- `--text-dark`: `#222222` (High-contrast charcoal for body text)
- `--text-muted`: `#555555` (Subtitles, meta info)
- `--bg-page`: `#ffffff` (Page background)
- `--bg-card`: `#ffffff` (Material Design cards)
- `--border-accent`: `#f0e6d6` (Soft saffron card borders)

## 3. Typography Rules
- **Headings (`<h1>` – `<h3>`)**: Must use serif typography (`'Playfair Display'`, `'PT Serif'`, Georgia, serif) in deep spiritual maroon (`var(--primary-maroon)`).
- **Body Text (`<p>`, `<span>`, `<a>`)**: Must use clean sans-serif typography (`'Poppins'`, `'Lato'`, `'Inter'`) with generous line-height (`1.75`–`1.85`).

## 4. Layout & Cards
- **Glassmorphism Accents (`.glass-card`, `.glass-panel`)**: Use frosted glass overlays with soft backdrop blur (`backdrop-filter: blur(12px)`) exclusively for floating highlights, quote cards, and modal drawers.
- **Material Design Cards (`.material-card`, `.entry`, `.grid-inner`)**: Use subtle corner radiuses (`12px`–`16px`), `#f0e6d6` borders, and soft non-intrusive drop shadows (`0 4px 20px rgba(0,0,0,0.04)`).
- **Single Container Navigation**: Maintain single horizontal container navigation (`.nav-container`) with desktop flex row alignment (`@media (min-width: 992px)`) and slide-in drawer mobile overlay (`@media (max-width: 991px)`).

## 5. Clean Code Standards
- **Zero Inline Styles**: All custom styles must be defined in `docs/css/custom.css` or `docs/css/theme.css`. Do not add inline `style="..."` attributes to HTML tags.
- **Semantic HTML5 Tags**: Always use `<header>`, `<nav>`, `<main id="content">`, `<section>`, `<article>`, `<aside>`, `<footer>`.
- **High-Contrast Footer**: Ensure footer elements strictly maintain WCAG AAA compliance (`#1a1918` background, `#ffffff` headings, `#cccccc` body, `#e0d8cc` links, and `#f7ca65` gold accents).
