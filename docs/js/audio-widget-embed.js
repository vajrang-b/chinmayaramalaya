/**
 * CHINMAYA RAMALAYA - AUDIO AGENT FLOATING WIDGET EMBED
 * Injects a floating Neumorphic Devotional Audio Guide button on any page.
 */

(function () {
    function initAudioWidget() {
        if (document.getElementById('ramalaya-audio-widget-container')) return;

        const widgetContainer = document.createElement('div');
        widgetContainer.id = 'ramalaya-audio-widget-container';
        widgetContainer.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 99999;
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: system-ui, -apple-system, sans-serif;
        `;

        widgetContainer.innerHTML = `
            <a href="audio-agent/index.html" id="ramalaya-audio-trigger-btn" title="Open Ramalaya Devotional Audio AI Agent" style="
                width: 58px;
                height: 58px;
                border-radius: 50%;
                background: #f4efe8;
                box-shadow: 6px 6px 16px rgba(185, 172, 155, 0.5), -6px -6px 16px rgba(255, 255, 255, 0.95);
                border: 2px solid #b37e14;
                display: flex;
                align-items: center;
                justify-content: center;
                text-decoration: none;
                cursor: pointer;
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            ">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="#700000">
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
            </a>
        `;

        document.body.appendChild(widgetContainer);

        const btn = document.getElementById('ramalaya-audio-trigger-btn');
        btn.addEventListener('mouseenter', () => {
            btn.style.transform = 'scale(1.1) rotate(5deg)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'scale(1.0) rotate(0deg)';
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAudioWidget);
    } else {
        initAudioWidget();
    }
})();
