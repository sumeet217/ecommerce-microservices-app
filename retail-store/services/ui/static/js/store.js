/* ════════════════════════════════════════════════════════════════════
   RetailStore UI — store.js
   Client-side interactions for the Django-template-based storefront.
   No external dependencies beyond Bootstrap 5 (already loaded).
   ════════════════════════════════════════════════════════════════════ */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  /* ── 1. Auto-dismiss flash messages ──────────────────────────────── */
  document.querySelectorAll('.alert.auto-dismiss').forEach(el => {
    const dismiss = () => {
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-8px)';
      setTimeout(() => el.remove(), 500);
    };
    setTimeout(dismiss, 4500);
  });


  /* ── 2. Quantity stepper buttons ─────────────────────────────────── */
  document.querySelectorAll('.qty-stepper').forEach(wrap => {
    const input = wrap.querySelector('.qty-input');
    const dec   = wrap.querySelector('[data-action="dec"]');
    const inc   = wrap.querySelector('[data-action="inc"]');
    if (!input) return;
    const min = parseInt(input.min || '1');
    const max = parseInt(input.max || '99');

    dec && dec.addEventListener('click', () => {
      const v = parseInt(input.value) - 1;
      if (v >= min) { input.value = v; input.dispatchEvent(new Event('change')); }
    });
    inc && inc.addEventListener('click', () => {
      const v = parseInt(input.value) + 1;
      if (v <= max) { input.value = v; input.dispatchEvent(new Event('change')); }
    });
  });


  /* ── 3. Cart qty: auto-submit on change (debounced 600ms) ────────── */
  document.querySelectorAll('.cart-qty-form .qty-input').forEach(input => {
    let timer;
    input.addEventListener('change', () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const form = input.closest('form');
        if (form) {
          // Show a subtle loading state
          const btn = form.querySelector('button[type="submit"]');
          if (btn) btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
          form.submit();
        }
      }, 600);
    });
  });


  /* ── 4. Confirm dialogs (clear cart, cancel order, etc.) ─────────── */
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });


  /* ── 5. Product image gallery thumbnails ─────────────────────────── */
  document.querySelectorAll('.thumb-img').forEach(thumb => {
    thumb.addEventListener('click', () => {
      const main = document.getElementById('main-product-img');
      if (!main) return;
      main.style.transition = 'opacity 0.15s ease';
      main.style.opacity = '0';
      setTimeout(() => {
        main.src = thumb.src;
        main.style.opacity = '1';
        // Update border highlight
        document.querySelectorAll('.thumb-img').forEach(t => t.style.borderColor = 'var(--glass-border)');
        thumb.style.borderColor = 'var(--brand-primary)';
      }, 150);
    });
  });


  /* ── 6. Scroll-driven card fade-in (IntersectionObserver) ────────── */
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          const delay = Math.min(i * 0.06, 0.4); // cap delay at 400ms
          entry.target.style.animationDelay = `${delay}s`;
          entry.target.classList.add('animate-fade-up');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.product-card, .order-card').forEach(card => {
      observer.observe(card);
    });
  }


  /* ── 7. Add-to-cart button loading state ─────────────────────────── */
  document.querySelectorAll('form[action*="cart/add"]').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span>Adding…';
      }
    });
  });


  /* ── 8. Checkout form: submit button loading state ───────────────── */
  const checkoutForm = document.querySelector('form[action*="checkout"]');
  if (checkoutForm) {
    checkoutForm.addEventListener('submit', (e) => {
      const btn = checkoutForm.querySelector('button[type="submit"]');
      if (btn) {
        // Basic client-side validation before showing spinner
        const required = checkoutForm.querySelectorAll('[required]');
        const allFilled = Array.from(required).every(f => f.value.trim() !== '');
        if (allFilled) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Placing Order…';
        }
      }
    });
  }


  /* ── 9. Navbar active state detection ────────────────────────────── */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar-custom .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && currentPath.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && currentPath === '/') {
      link.classList.add('active');
    }
  });


  /* ── 10. Mobile menu — close on nav-link click ───────────────────── */
  const mobileMenu = document.getElementById('mobileMenu');
  if (mobileMenu) {
    mobileMenu.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        // Use Bootstrap collapse API if available
        const bsCollapse = window.bootstrap && bootstrap.Collapse.getInstance(mobileMenu);
        if (bsCollapse) bsCollapse.hide();
      });
    });
  }


  /* ── 11. Product card quick-view ripple effect ───────────────────── */
  document.querySelectorAll('.product-card').forEach(card => {
    card.addEventListener('click', function(e) {
      // Only ripple if not clicking a form button
      if (e.target.closest('form')) return;
      const ripple = document.createElement('span');
      const rect = card.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.cssText = `
        position:absolute;
        width:${size}px;height:${size}px;
        left:${e.clientX - rect.left - size/2}px;
        top:${e.clientY - rect.top - size/2}px;
        background:rgba(108,71,255,0.08);
        border-radius:50%;
        transform:scale(0);
        animation:ripple-anim 0.5s ease-out forwards;
        pointer-events:none;
        z-index:1;
      `;
      card.style.position = 'relative';
      card.style.overflow = 'hidden';
      card.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  /* Ripple keyframe (injected once) */
  if (!document.getElementById('ripple-style')) {
    const style = document.createElement('style');
    style.id = 'ripple-style';
    style.textContent = `
      @keyframes ripple-anim {
        to { transform: scale(2.5); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }


  /* ── 12. Scroll-to-top on page load (preserve scroll on back) ────── */
  if (window.history.scrollRestoration) {
    window.history.scrollRestoration = 'auto';
  }

});
