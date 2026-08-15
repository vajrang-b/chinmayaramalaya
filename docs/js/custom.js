/**
 * Chinmaya Ramalaya - Custom JavaScript
 * Handles:
 * 1. Go-To-Top button functionality with smooth scrolling
 * 2. Single Mobile navigation toggle (#primary-menu-trigger) & expandable submenus
 */

document.addEventListener('DOMContentLoaded', function () {

    // ----------------------------------------------------------------------
    // 1. GO-TO-TOP BUTTON HANDLER
    // ----------------------------------------------------------------------
    let gotoTopBtn = document.getElementById('gotoTop');

    if (!gotoTopBtn) {
        gotoTopBtn = document.createElement('div');
        gotoTopBtn.id = 'gotoTop';
        document.body.appendChild(gotoTopBtn);
    }

    gotoTopBtn.innerHTML = `
        <svg viewBox="0 0 24 24">
            <path d="M12 4l-8 8h5v8h6v-8h5z"/>
        </svg>
    `;
    gotoTopBtn.setAttribute('title', 'Back to top');
    gotoTopBtn.setAttribute('aria-label', 'Back to top');

    window.addEventListener('scroll', function () {
        if (window.scrollY > 250) {
            gotoTopBtn.classList.add('show');
        } else {
            gotoTopBtn.classList.remove('show');
        }
    }, { passive: true });

    gotoTopBtn.addEventListener('click', function (e) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // ----------------------------------------------------------------------
    // 2. SINGLE MOBILE NAV TRIGGER (#primary-menu-trigger)
    // ----------------------------------------------------------------------
    const primaryMenuTrigger = document.getElementById('primary-menu-trigger');
    const primaryMenu = document.querySelector('nav.primary-menu');

    if (primaryMenuTrigger && primaryMenu) {
        // Style trigger with clean SVG icon if empty
        if (!primaryMenuTrigger.querySelector('svg')) {
            primaryMenuTrigger.innerHTML = `
                <svg viewBox="0 0 24 24">
                    <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
                </svg>
            `;
        }

        // Toggle primary menu on single trigger click
        primaryMenuTrigger.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            primaryMenu.classList.toggle('active');
        });

        // Submenu toggles on mobile
        const menuItemsWithSub = primaryMenu.querySelectorAll('.menu-item');
        menuItemsWithSub.forEach(item => {
            const subMenu = item.querySelector('.sub-menu-container');
            const parentLink = item.querySelector('.menu-link');

            if (subMenu && parentLink) {
                // Click parent link on mobile opens submenu if href is empty or #
                parentLink.addEventListener('click', function (e) {
                    if (window.innerWidth <= 991) {
                        const href = parentLink.getAttribute('href');
                        if (!href || href === '#' || href.startsWith('javascript:')) {
                            e.preventDefault();
                            subMenu.classList.toggle('open');
                        }
                    }
                });
            }
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            if (window.innerWidth <= 991 && primaryMenu.classList.contains('active')) {
                if (!primaryMenu.contains(e.target) && !primaryMenuTrigger.contains(e.target)) {
                    primaryMenu.classList.remove('active');
                }
            }
        });
    }

    // ----------------------------------------------------------------------
    // 3. OPEN ALL DONATION LINKS & TABS IN NEW TAB (target="_blank")
    // ----------------------------------------------------------------------
    const donationSelector = 'a[href*="donate"], a[href*="crowdfund"], a[href*="paypal.com"]';
    const donationLinks = document.querySelectorAll(donationSelector);
    donationLinks.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });
});
