#!/usr/bin/env python3
"""
Chinmaya Ramalaya - WCAG 2.1 Text Contrast Checker
Scans web pages using Playwright, computes rendered RGB text and background colors,
calculates luminosity ratios, and reports low-contrast elements (e.g. Address, Email, Footers).
"""

import sys
import math
import argparse
from playwright.sync_api import sync_playwright

def parse_rgba(color_str):
    """Parse 'rgb(r, g, b)' or 'rgba(r, g, b, a)' into tuple of floats (0..255)."""
    if not color_str or color_str == 'transparent':
        return None
    color_str = color_str.replace('rgba(', '').replace('rgb(', '').replace(')', '')
    parts = [float(p.strip()) for p in color_str.split(',')]
    if len(parts) == 3:
        return (parts[0], parts[1], parts[2], 1.0)
    elif len(parts) == 4:
        return (parts[0], parts[1], parts[2], parts[3])
    return None

def linearize(c_255):
    """Convert 0-255 sRGB value to linearized channel value."""
    c = c_255 / 255.0
    if c <= 0.04045:
        return c / 12.92
    else:
        return math.pow((c + 0.055) / 1.055, 2.4)

def calculate_luminance(rgb_tuple):
    """Calculate WCAG relative luminance L for an RGB color."""
    r, g, b = rgb_tuple[0], rgb_tuple[1], rgb_tuple[2]
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

def calculate_contrast_ratio(fg_rgb, bg_rgb):
    """Calculate WCAG contrast ratio (L1 + 0.05) / (L2 + 0.05)."""
    l1 = calculate_luminance(fg_rgb)
    l2 = calculate_luminance(bg_rgb)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)

def check_page_contrast(url, target_selectors=None, min_ratio=4.5):
    """Scan page and return list of text elements with contrast ratios."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        
        print(f"\n🌐 Navigating to: {url}")
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
        except Exception as e:
            print(f"⚠️ Page load timeout or error: {e}")
            page.goto(url, wait_until="domcontentloaded")
            
        # JS script to find visible text elements and compute colors
        results = page.evaluate("""
            () => {
                const textElements = [];
                const tags = ['p', 'span', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'address', 'abbr', 'strong', 'b', 'li', 'td', 'th', 'button', 'label'];
                
                function getEffectiveBackgroundColor(el) {
                    let current = el;
                    while (current && current !== document.body) {
                        const style = window.getComputedStyle(current);
                        const bg = style.backgroundColor;
                        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                            return bg;
                        }
                        current = current.parentElement;
                    }
                    return window.getComputedStyle(document.body).backgroundColor || 'rgb(244, 239, 232)';
                }

                tags.forEach(tag => {
                    const els = document.querySelectorAll(tag);
                    els.forEach(el => {
                        const text = el.innerText ? el.innerText.trim() : '';
                        // Skip empty text or hidden elements
                        if (!text || text.length === 0 || el.children.length > 5) return;
                        if (el.offsetWidth === 0 || el.offsetHeight === 0) return;

                        const style = window.getComputedStyle(el);
                        const color = style.color;
                        const bgColor = getEffectiveBackgroundColor(el);
                        const fontSize = style.fontSize;
                        const fontWeight = style.fontWeight;

                        textElements.push({
                            tag: tag,
                            text: text.substring(0, 60),
                            color: color,
                            bgColor: bgColor,
                            fontSize: fontSize,
                            fontWeight: fontWeight,
                            selector: el.className ? `${tag}.${el.className.split(' ').join('.')}` : tag
                        });
                    });
                });
                return textElements;
            }
        """)

        browser.close()
        return results

def main():
    parser = argparse.ArgumentParser(description="WCAG 2.1 Text Contrast Checker for Chinmaya Ramalaya")
    parser.add_argument("url", nargs="?", default="http://localhost:8080/index.html", help="Target URL to check")
    parser.add_argument("--min-ratio", type=float, default=4.5, help="Minimum WCAG contrast ratio (4.5 for AA, 7.0 for AAA)")
    args = parser.parse_args()

    results = check_page_contrast(args.url)
    
    print("\n" + "="*80)
    print(f"📊 WCAG 2.1 TEXT CONTRAST AUDIT REPORT ({args.url})")
    print("="*80)
    print(f"{'STATUS':<8} | {'RATIO':<6} | {'FG COLOR':<18} | {'BG COLOR':<18} | {'TEXT SNIPPET'}")
    print("-" * 80)

    fails = 0
    passes = 0

    for item in results:
        fg = parse_rgba(item['color'])
        bg = parse_rgba(item['bgColor'])
        
        if fg and bg:
            ratio = calculate_contrast_ratio(fg, bg)
            is_pass = ratio >= args.min_ratio
            status_str = "✅ PASS" if is_pass else "❌ FAIL"
            
            if is_pass:
                passes += 1
            else:
                fails += 1

            # Print failing items or key elements (Address, Email, Footers, etc.)
            text_snippet = item['text'].replace('\n', ' ')
            is_key_element = any(k in text_snippet.lower() for k in ['address', 'email', 'phone', 'follow us', 'contact', 'bvadmin', 'lucon'])
            
            if not is_pass or is_key_element:
                print(f"{status_str:<8} | {ratio:>5.2f}:1 | {item['color']:<18} | {item['bgColor']:<18} | {text_snippet[:35]}")

    print("-" * 80)
    print(f"Total Evaluated Elements: {len(results)} | Passes (≥{args.min_ratio}:1): {passes} | Low-Contrast Fails: {fails}")
    print("="*80)

if __name__ == "__main__":
    main()
