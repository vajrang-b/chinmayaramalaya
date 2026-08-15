/**
 * Chinmaya Ramalaya - Custom JavaScript
 * Handles:
 * 1. Modern Go-To-Top button functionality with smooth scrolling
 * 2. Mobile navigation toggle & expandable submenus
 */

document.addEventListener('DOMContentLoaded', function () {

    // ----------------------------------------------------------------------
    // 1. GO-TO-TOP BUTTON HANDLER
    // ----------------------------------------------------------------------
    let gotoTopBtn = document.getElementById('gotoTop');

    if (!gotoTopBtn) {
        // Create button dynamically if not in HTML
        gotoTopBtn = document.createElement('div');
        gotoTopBtn.id = 'gotoTop';
        document.body.appendChild(gotoTopBtn);
    }

    // Set SVG arrow inside gotoTop button
    gotoTopBtn.innerHTML = `
        <svg viewBox="0 0 24 24">
            <path d="M12 4l-8 8h5v8h6v-8h5z"/>
        </svg>
    `;
    gotoTopBtn.setAttribute('title', 'Back to top');
    gotoTopBtn.setAttribute('aria-label', 'Back to top');
    gotoTopBtn.setAttribute('role', 'button');

    // Show / Hide button based on scroll position
    window.addEventListener('scroll', function () {
        if (window.scrollY > 250) {
            gotoTopBtn.classList.add('show');
        } else {
            gotoTopBtn.classList.remove('show');
        }
    }, { passive: true });

    // Smooth scroll to top on click
    gotoTopBtn.addEventListener('click', function (e) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // ----------------------------------------------------------------------
    // 2. MOBILE NAVIGATION TOGGLE & ACCORDION SUBMENUS
    // ----------------------------------------------------------------------
    const headerRow = document.querySelector('#header-wrap .header-row') || document.querySelector('#header .header-row');
    const primaryMenu = document.querySelector('nav.primary-menu');

    if (headerRow && primaryMenu) {
        // Inject Mobile Toggle Button if not present
        if (!document.querySelector('.mobile-nav-toggle')) {
            const mobileBtn = document.createElement('button');
            mobileBtn.className = 'mobile-nav-toggle';
            mobileBtn.setAttribute('type', 'button');
            mobileBtn.setAttribute('aria-label', 'Toggle Navigation Menu');
            mobileBtn.innerHTML = `
                <svg viewBox="0 0 24 24">
                    <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
                </svg>
                <span>Menu</span>
            `;

            // Insert toggle button before navigation
            primaryMenu.parentNode.insertBefore(mobileBtn, primaryMenu);

            // Toggle menu on click
            mobileBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                primaryMenu.classList.toggle('active');
                const isExpanded = primaryMenu.classList.contains('active');
                mobileBtn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
            });
        }

        // Handle Submenu Expand/Collapse on Mobile
        const menuItemsWithSub = primaryMenu.querySelectorAll('.menu-item');
        menuItemsWithSub.forEach(item => {
            const subMenu = item.querySelector('.sub-menu-container');
            const parentLink = item.querySelector('.menu-link');

            if (subMenu && parentLink) {
                // Append submenu toggle arrow button
                const toggleArrow = document.createElement('button');
                toggleArrow.className = 'submenu-toggle-btn';
                toggleArrow.innerHTML = '▾';
                toggleArrow.setAttribute('type', 'button');
                toggleArrow.setAttribute('aria-label', 'Toggle Submenu');

                parentLink.appendChild(toggleArrow);

                // Prevent link jump if href is empty or javascript
                parentLink.addEventListener('click', function (e) {
                    if (window.innerWidth <= 991) {
                        const href = parentLink.getAttribute('href');
                        if (!href || href === '#' || href.startsWith('javascript:')) {
                            e.preventDefault();
                            subMenu.classList.toggle('open');
                            toggleArrow.classList.toggle('open');
                        }
                    }
                });

                toggleArrow.addEventListener('click', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    subMenu.classList.toggle('open');
                    toggleArrow.classList.toggle('open');
                });
            }
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            if (window.innerWidth <= 991 && primaryMenu.classList.contains('active')) {
                if (!primaryMenu.contains(e.target) && !e.target.closest('.mobile-nav-toggle')) {
                    primaryMenu.classList.remove('active');
                }
            }
        });
    }
});
