/* ===== Interactive Features ===== */

// Password visibility toggle - defined globally so it's available for inline onclick handlers
function togglePasswordVisibility(fieldId, button) {
    const field = document.getElementById(fieldId);
    const icon = button.querySelector('i');

    if (field && icon) {
        if (field.type === 'password') {
            field.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            field.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('open');
        });
    }

    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    const storageKey = 'kisii-theme';
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const applyTheme = (theme) => {
        document.body.classList.remove('theme-light', 'theme-dark');

        if (theme === 'light') {
            document.body.classList.add('theme-light');
        } else if (theme === 'dark') {
            document.body.classList.add('theme-dark');
        }

        localStorage.setItem(storageKey, theme);

        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.className = theme === 'light' ? 'fas fa-sun' : 'fas fa-moon';
            }
        }
    };

    const getSystemTheme = () => (mediaQuery.matches ? 'dark' : 'light');

    const initialTheme = 'light';
    applyTheme(initialTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isDark = document.body.classList.contains('theme-dark');
            const nextTheme = isDark ? 'light' : 'dark';
            applyTheme(nextTheme);
        });
    }

    mediaQuery.addEventListener?.('change', (event) => {
        if (!localStorage.getItem(storageKey)) {
            applyTheme(event.matches ? 'dark' : 'light');
        }
    });

    // Hero slide rotation
    const heroTitle = document.querySelector('.hero-section h2');
    const heroMessages = [
        "AYA' ATEKIRE CHINSA IBERE",
        "LIVE LOCAL STORIES, SHARED WITH THE WORLD",
        "YOUR COMMUNITY, YOUR CHANNEL"
    ];
    if (heroTitle) {
        let heroIndex = 0;
        setInterval(() => {
            heroIndex = (heroIndex + 1) % heroMessages.length;
            heroTitle.textContent = heroMessages[heroIndex];
        }, 5000);
    }

    // Back to Top Button
    const backToTopBtn = document.getElementById('backToTop');

    if (backToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });

        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Video card hover effects
    const videoCards = document.querySelectorAll('.video-card');
    videoCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transform = 'translateY(-8px)';
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = 'translateY(0)';
        });
    });

    // Category card animations
    const categoryCards = document.querySelectorAll('.category-card');
    categoryCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;

        card.addEventListener('mouseenter', function () {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Smooth scroll for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Ensure password visibility toggles exist for any password inputs (admin/editor pages)
    const addPasswordToggles = () => {
        const pwdInputs = document.querySelectorAll('input[type="password"]');
        pwdInputs.forEach((input) => {
            // don't add if already has a sibling toggle button
            const wrapper = input.closest('.password-input-wrapper') || input.parentElement;
            const hasToggle = wrapper && wrapper.querySelector && wrapper.querySelector('.password-toggle-btn');
            if (hasToggle) return;

            // ensure input has an id for toggle function
            if (!input.id) {
                input.id = 'pwd_' + Math.random().toString(36).slice(2, 9);
            }

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'password-toggle-btn';
            btn.setAttribute('aria-label', 'Toggle password visibility');
            btn.title = 'Show or hide password';
            btn.style = 'color:#888; margin-left:8px;';
            btn.innerHTML = '<i class="fas fa-eye"></i>';
            btn.addEventListener('click', function () {
                togglePasswordVisibility(input.id, this);
            });

            // append the button next to the input
            if (wrapper) {
                wrapper.style.position = 'relative';
                // try to position button inside wrapper
                wrapper.appendChild(btn);
            } else {
                input.parentElement.appendChild(btn);
            }
        });
    };

    addPasswordToggles();

    // Newsletter subscription
    const newsletterForm = document.getElementById('newsletterForm');
    const newsletterStatus = document.getElementById('newsletterStatus');
    if (newsletterForm && newsletterStatus) {
        newsletterForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const emailInput = newsletterForm.querySelector('input[name="email"]');
            const submitButton = newsletterForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;

            newsletterStatus.textContent = 'Subscribing...';
            newsletterStatus.className = 'newsletter-status';
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i> Subscribing';

            const formData = new FormData(newsletterForm);
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';

            try {
                const response = await fetch(newsletterForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();
                newsletterStatus.textContent = data.message || 'Subscription complete.';
                newsletterStatus.className = `newsletter-status ${response.ok ? 'success' : 'error'}`;
                if (response.ok) {
                    newsletterForm.reset();
                } else if (emailInput) {
                    emailInput.focus();
                }
            } catch (error) {
                newsletterStatus.textContent = 'Unable to subscribe right now. Please try again.';
                newsletterStatus.className = 'newsletter-status error';
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            }
        });
    }

    // Add loading animation to images
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('load', function () {
            this.style.opacity = '1';
        });
        img.style.opacity = '0.7';
    });

    // Lazy load images (basic implementation)
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    observer.unobserve(entry.target);
                }
            });
        });

        document.querySelectorAll('.video-thumbnail img').forEach(img => imageObserver.observe(img));
    }

    // Add animation to stat items on scroll
    const statItems = document.querySelectorAll('.stat-item');
    if (statItems.length > 0) {
        const statObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animation = 'slideInUp 0.6s ease-out forwards';
                }
            });
        });

        statItems.forEach(item => statObserver.observe(item));
    }

    // Video card play button overlay
    document.querySelectorAll('.video-thumbnail').forEach(thumbnail => {
        const link = thumbnail.querySelector('a');
        if (link) {
            thumbnail.addEventListener('mouseenter', function () {
                link.style.opacity = '1';
            });

            thumbnail.addEventListener('mouseleave', function () {
                link.style.opacity = '0';
            });
        }
    });

    // Add keyboard navigation for better accessibility
    document.addEventListener('keydown', (e) => {
        // Press / to focus search (if search exists)
        if (e.key === '/') {
            const searchInput = document.querySelector('input[type="text"][placeholder*="Search"]');
            if (searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
        }
    });

    // Add smooth transition for page navigation
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Only apply to internal links
            if (href && href.startsWith('/') && !href.startsWith('#')) {
                document.documentElement.style.opacity = '1';
            }
        });
    });

    // Add delete confirmation for dashboard actions
    document.querySelectorAll('.delete-button').forEach(button => {
        button.addEventListener('click', function (event) {
            const confirmed = window.confirm('Are you sure you want to delete this item? This action cannot be undone.');
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    // Add ripple effect to buttons on click
    document.querySelectorAll('button, a[class*="button"]').forEach(element => {
        element.addEventListener('click', function (e) {
            const ripple = document.createElement('span');
            ripple.style.position = 'absolute';
            ripple.style.pointerEvents = 'none';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.5)';
            ripple.style.width = '0px';
            ripple.style.height = '0px';
            ripple.style.left = '50%';
            ripple.style.top = '50%';
            ripple.style.transform = 'translate(-50%, -50%)';
            ripple.style.opacity = '1';
            ripple.style.animation = 'ripple 0.6s ease-out';

            if (window.getComputedStyle(this).position === 'static') {
                this.style.position = 'relative';
            }
            this.style.overflow = 'hidden';
            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });
});

// Add ripple animation to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        from {
            width: 0;
            height: 0;
            opacity: 1;
        }
        to {
            width: 300px;
            height: 300px;
            opacity: 0;
        }
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    img {
        transition: opacity 0.3s ease;
    }
`;
document.head.appendChild(style);
