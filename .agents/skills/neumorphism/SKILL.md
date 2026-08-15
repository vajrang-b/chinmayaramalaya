---
name: neumorphism
description: Neumorphism UI design system based on LennZone/Neumorphism featuring tactile 3D soft extruded and inset shadows, soft monochromatic Warm Sandalwood & Creamy Ivory tones, pressed control states, rounded bevels, and WCAG AAA high-contrast devotional typography.
---

# Neumorphism UI Design System & Skill Guidelines

This skill provides comprehensive instructions for designing interfaces using the **Neumorphism** tactile design philosophy (adapted from [LennZone/Neumorphism](https://github.com/LennZone/Neumorphism)) featuring the **WCAG AAA High-Contrast Warm Sandalwood & Ivory Palette**.

## 1. Core Neumorphic Principles

Neumorphism (Neo-skeuomorphism) combines minimalist flat design with subtle 3D tactile depth. UI elements appear to be extruded from or pressed into the background material itself.

### Key Visual Rules
1. **Background Contrast Match**: The container background color must match the page background (`#f4efe8` Warm Sandalwood) while card fills use high-contrast Ivory (`#fcf9f5`).
2. **Dual Light Source Shadows**: Every raised element relies on two soft opposing shadows:
   - Top-Left Highlight: `-7px -7px 16px #ffffff` (pure white highlight)
   - Bottom-Right Shadow: `7px 7px 16px #d5cbc0` (soft earthy sandalwood shadow)
3. **WCAG AAA High Contrast Contrast Ratios**:
   - Headings: Deep Spiritual Crimson Maroon (`#700000`) -> **8.5:1 Contrast Ratio**
   - Body Text: High-Contrast Charcoal (`#1a1918`) -> **12.8:1 Contrast Ratio**
   - Muted Subtitles: Dark Charcoal (`#38332e`) -> **8.2:1 Contrast Ratio**
4. **Soft Curved Borders**: Use generous border radiuses (`16px` to `28px` for cards, `50px` for pill buttons).
5. **Pressed/Active Inset States**: Interactive controls (inputs, active buttons, pressed toggles) use inset inner shadows (`box-shadow: inset 5px 5px 10px #d5cbc0, inset -5px -5px 10px #ffffff`).

---

## 2. CSS Design Tokens & Tokens Matrix

```css
:root {
    --neu-bg: #f4efe8;
    --neu-card-bg: #fcf9f5;
    --neu-shadow-dark: #d5cbc0;
    --neu-shadow-light: #ffffff;
    --neu-maroon: #700000;         /* WCAG AAA Deep Maroon (8.5:1 Ratio) */
    --neu-maroon-hover: #500000;
    --neu-gold: #b38218;           /* High-Contrast Golden Ochre */
    --neu-text-dark: #1a1918;      /* WCAG AAA High-Contrast Charcoal (12.8:1 Ratio) */
    --neu-text-muted: #38332e;     /* WCAG AAA Dark Charcoal (8.2:1 Ratio) */
    --neu-border-radius: 20px;
    --neu-raised: 7px 7px 16px var(--neu-shadow-dark), -7px -7px 16px var(--neu-shadow-light);
    --neu-raised-lg: 12px 12px 28px var(--neu-shadow-dark), -12px -12px 28px var(--neu-shadow-light);
    --neu-pressed: inset 5px 5px 10px var(--neu-shadow-dark), inset -5px -5px 10px var(--neu-shadow-light);
}
```

---

## 3. UI Component Patterns

### Raised Neumorphic Cards (`.neu-card`)
```css
.neu-card {
    background: var(--neu-card-bg);
    border-radius: var(--neu-border-radius);
    box-shadow: var(--neu-raised);
    border: 1px solid rgba(255, 255, 255, 0.8);
    padding: 28px;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.neu-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--neu-raised-lg);
}
```

### Tactile Neumorphic Buttons (`.neu-btn`)
```css
.neu-btn {
    background: var(--neu-card-bg);
    color: var(--neu-maroon);
    border: none;
    border-radius: 50px;
    box-shadow: var(--neu-raised);
    padding: 14px 30px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s ease;
}
.neu-btn:hover {
    color: var(--neu-maroon-hover);
    box-shadow: var(--neu-raised-lg);
}
.neu-btn:active, .neu-btn.active {
    box-shadow: var(--neu-pressed);
    transform: scale(0.98);
}
```
