# Devotional Website Design System & Guidelines

## Overview & Philosophy
For a devotional platform like **Chinmaya Ramalaya**, an **Editorial Minimalist** design style paired with subtle **Glassmorphism** and **Material Design** accents creates a tranquil, reverent, and elevated user experience.

Devotional platforms require peace, clarity, and spiritual reverence. The UI avoids cluttered, aggressive, or chaotic visual trends (such as Neumorphism or Neo-Brutalism) and instead prioritizes readable scriptures, daily reflections, audio chants, and community updates within a spacious, peaceful atmosphere.

---

## 1. Minimalist Editorial Layout (The Core)

The core architecture uses generous white space, clean grid alignment, and classic lettering to evoke the feel of a modern spiritual journal.

### Typography
* **Headings (`<h1>` – `<h3>`)**: Timeless serif typeface (e.g., *Playfair Display*, *Merriweather*, or *PT Serif*) to convey respect, tradition, and sacred wisdom.
* **Body Text (`<p>`, `<span>`, `<a>`)**: Clean sans-serif (e.g., *Poppins*, *Lato*, or *Inter*) for high legibility across mobile and desktop devices.
* **Font Scaling**: High contrast between headings and body text to create clear visual hierarchy.

### Whitespace & Breathing Room
* **Padding & Margins**: Ample vertical padding (`35px`–`50px`) around sections to allow text blocks room to breathe.
* **Line Height**: Relaxed line spacing (`1.75`–`1.8`) for effortless reading of longer devotional texts, quotes, and stotrams.

### Color Palette (Earthy & Reverent Tones)
* **Primary Spiritual Maroon**: `#8b0000` (Used for headers, primary CTA buttons, and key highlights)
* **Temple Saffron Gold**: `#c89b3c` (Used for accents, sub-headings, icons, and borders)
* **Warm Cream Tint**: `#fdf6ea` / `#fcfbfa` (Soft, non-glare background tone)
* **Deep Charcoal Text**: `#222222` (High contrast for maximum text legibility)
* **Muted Neutral**: `#555555` (For subtitles and meta notes)

---

## 2. Glassmorphism & Material Design (Interactive Accents)

While the overall layout remains clean and flat, subtle layers are used to draw focus to interactive elements such as daily quote cards, audio players, or registration forms.

### Frosted Glass Overlays
* **Usage**: Reserved for floating cards, daily reflection highlights, and modal drawers.
* **Styling**: Semi-transparent background with soft backdrop blurs:
  ```css
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(240, 230, 214, 0.6);
  ```

### Material Design Cards
* **Usage**: Content sections, announcements, program lists, and donation options.
* **Styling**: Subtle corner radiuses (`12px`–`16px`) with soft, non-intrusive drop shadows:
  ```css
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0e6d6;
  ```

---

## 3. Design Styles to Avoid

* ❌ **Neumorphism**: Avoid extruded plastic/soft-shadow UI, as it causes muddy contrast and reduces readability on text-dense pages.
* ❌ **Neo-Brutalism**: Avoid thick black borders, neon colors, and raw styling, which feel aggressive and disrupt a serene mood.

---

## 4. Media & Feature Requirements

The Chinmaya Ramalaya platform hosts:
1. **Devotional Text & Reflections**: Bhagavad Gita study logs, Swami Chinmayananda quotes, and announcements.
2. **Audio Resources**: *Sthothraanjali* chant audio files and daily prayer guides.
3. **Program & Event Registration**: Bala Vihar registration, Yoga classes, and special camps.
4. **Temple Construction & Donation Portal**: Dedicated sponsorship, Puja services, and fundraising channels.
