/* ===== Interactive Features ===== */

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
    const storedTheme = localStorage.getItem('kisii-theme');
    if (storedTheme === 'light') {
        document.body.classList.add('theme-light');
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('theme-light');
            const isLight = document.body.classList.contains('theme-light');
            localStorage.setItem('kisii-theme', isLight ? 'light' : 'dark');
            const icon = themeToggle.querySelector('i');
            icon.className = isLight ? 'fas fa-sun' : 'fas fa-moon';
        });
    }

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

    // Hero parallax and featured card rotation
    const heroSection = document.querySelector('.hero-section');
    const heroContent = document.querySelector('.hero-content');
    if (heroSection && heroContent) {
        window.addEventListener('scroll', () => {
            const offset = window.scrollY * 0.15;
            heroContent.style.setProperty('--hero-shift', `${Math.min(offset, 60)}px`);
        }, { passive: true });
    }

    const featuredSlides = document.querySelectorAll('.featured-slide');
    const autoplayToggle = document.getElementById('autoplayToggle');
    let featuredRotationTimer = null;
    let autoplayEnabled = true;
    let hoverPaused = false;

    const startFeaturedRotation = () => {
        if (featuredRotationTimer) {
            clearInterval(featuredRotationTimer);
        }

        featuredRotationTimer = setInterval(() => {
            if (!autoplayEnabled || hoverPaused) {
                return;
            }

            featuredSlides.forEach((slide, index) => {
                slide.classList.toggle('is-active', index === (index + 1) % featuredSlides.length);
            });
        }, 4000);
    };

    if (featuredSlides.length > 1) {
        let activeIndex = 0;
        const rotateFeaturedSlides = () => {
            if (!autoplayEnabled || hoverPaused) {
                return;
            }
            featuredSlides.forEach((slide, index) => {
                slide.classList.toggle('is-active', index === activeIndex);
            });
            activeIndex = (activeIndex + 1) % featuredSlides.length;
        };

        featuredRotationTimer = setInterval(rotateFeaturedSlides, 4000);
        featuredSlides[0].classList.add('is-active');

        const featuredHoverZone = document.querySelector('.playlist-rail');
        if (featuredHoverZone) {
            featuredHoverZone.addEventListener('mouseenter', () => {
                hoverPaused = true;
            });
            featuredHoverZone.addEventListener('mouseleave', () => {
                hoverPaused = false;
            });
        }

        if (autoplayToggle) {
            autoplayToggle.addEventListener('click', () => {
                autoplayEnabled = !autoplayEnabled;
                autoplayToggle.innerHTML = autoplayEnabled
                    ? '<i class="fas fa-pause"></i> Pause'
                    : '<i class="fas fa-play"></i> Play';
                autoplayToggle.setAttribute('aria-pressed', autoplayEnabled ? 'true' : 'false');

                if (autoplayEnabled) {
                    rotateFeaturedSlides();
                } else if (featuredRotationTimer) {
                    clearInterval(featuredRotationTimer);
                }
            });
        }
    }

    const playlistItems = document.querySelectorAll('.playlist-item');
    const previewModal = document.getElementById('previewModal');
    const previewModalCard = previewModal?.querySelector('.preview-modal-card');
    const previewModalTitle = document.getElementById('previewModalTitle');
    const previewModalDescription = document.getElementById('previewModalDescription');
    const previewModalLink = document.getElementById('previewModalLink');
    const previewVideo = document.getElementById('previewVideo');
    const previewFullscreenBtn = document.getElementById('previewFullscreenBtn');
    let previewFullscreen = false;

    const closePreviewModal = () => {
        previewModal.classList.remove('is-open');
        previewModal.setAttribute('aria-hidden', 'true');
        previewModalCard.classList.remove('is-fullscreen');
        previewFullscreen = false;
        previewVideo?.pause();
    };

    playlistItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            item.classList.add('is-active');
        });
        item.addEventListener('mouseleave', () => {
            item.classList.remove('is-active');
        });
        item.addEventListener('click', () => {
            previewModalTitle.textContent = item.dataset.title || 'Preview';
            previewModalDescription.textContent = item.dataset.description || 'A featured broadcast from Kisii TV.';
            previewModalLink.href = item.dataset.link || '#';
            previewModal.classList.add('is-open');
            previewModal.setAttribute('aria-hidden', 'false');
            previewVideo?.play().catch(() => { });
        });
    });

    document.querySelectorAll('[data-close-modal]').forEach(control => {
        control.addEventListener('click', () => {
            closePreviewModal();
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && previewModal?.classList.contains('is-open')) {
            closePreviewModal();
        }
    });

    previewFullscreenBtn?.addEventListener('click', () => {
        previewFullscreen = !previewFullscreen;
        previewModalCard.classList.toggle('is-fullscreen', previewFullscreen);
    });

    const heroProgressBar = document.getElementById('heroProgressBar');
    if (heroProgressBar) {
        let progress = 0;
        const interval = setInterval(() => {
            progress = (progress + 1) % 101;
            heroProgressBar.style.width = `${progress}%`;
            if (progress === 100) {
                clearInterval(interval);
            }
        }, 250);
    }

    const countdownTimer = document.getElementById('countdownTimer');
    if (countdownTimer) {
        let secondsLeft = 30;
        setInterval(() => {
            secondsLeft = secondsLeft > 0 ? secondsLeft - 1 : 30;
            const minutes = String(Math.floor(secondsLeft / 60)).padStart(2, '0');
            const secs = String(secondsLeft % 60).padStart(2, '0');
            countdownTimer.textContent = `${minutes}:${secs}`;
        }, 1000);
    }

    const featuredTitle = document.getElementById('featuredTitle');
    const featuredDescription = document.getElementById('featuredDescription');
    const featuredLink = document.getElementById('featuredLink');
    const featuredItems = [
        {
            title: 'Featured Broadcast',
            description: 'Catch the latest live stories, sports highlights, and community updates from Kisii TV.',
            link: featuredLink?.getAttribute('href') || '#'
        },
        {
            title: 'Live Sports Highlights',
            description: 'Relive the best moments from the latest local and regional matches.',
            link: featuredLink?.getAttribute('href') || '#'
        },
        {
            title: 'Community Spotlight',
            description: 'Watch inspiring interviews and stories from the people shaping Kisii.',
            link: featuredLink?.getAttribute('href') || '#'
        }
    ];

    if (featuredTitle && featuredDescription && featuredLink) {
        let featuredIndex = 0;
        setInterval(() => {
            featuredIndex = (featuredIndex + 1) % featuredItems.length;
            featuredTitle.textContent = featuredItems[featuredIndex].title;
            featuredDescription.textContent = featuredItems[featuredIndex].description;
            featuredLink.setAttribute('href', featuredItems[featuredIndex].link);
        }, 4000);
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

    // Add ripple effect to buttons on click
    document.querySelectorAll('button, a[class*="button"]').forEach(element => {
        element.addEventListener('click', function (e) {
            const ripple = document.createElement('span');
            ripple.style.position = 'absolute';
            ripple.style.pointerEvents = 'none';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.5)';
            ripple.style.animation = 'ripple 0.6s ease-out';

            this.parentElement.style.position = 'relative';
            this.parentElement.appendChild(ripple);

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
