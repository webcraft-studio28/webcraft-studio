const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// ===== Mobile nav toggle =====
const navToggle = document.getElementById('navToggle');
const nav = document.getElementById('nav');

if (navToggle && nav) {
  navToggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });
  nav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      nav.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// ===== Sticky header shadow on scroll =====
const header = document.getElementById('siteHeader');
if (header) {
  window.addEventListener('scroll', () => {
    header.classList.toggle('scrolled', window.scrollY > 10);
  }, { passive: true });
}

// ===== Scroll reveal animations (staggered per parent) =====
const revealGroups = new Map();
document.querySelectorAll('.reveal').forEach(el => {
  const parent = el.parentElement;
  const index = parent ? (revealGroups.get(parent) || 0) : 0;
  if (parent) revealGroups.set(parent, index + 1);
  el.style.setProperty('--reveal-delay', prefersReducedMotion ? '0ms' : `${Math.min(index * 70, 420)}ms`);
});

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in-view');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

// ===== Count-up numbers =====
if (!prefersReducedMotion) {
  const countEls = document.querySelectorAll('[data-count-to]');
  const countObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      countObserver.unobserve(el);
      const target = parseFloat(el.getAttribute('data-count-to'));
      const prefix = el.getAttribute('data-count-prefix') || '';
      const suffix = el.getAttribute('data-count-suffix') || '';
      const decimals = el.getAttribute('data-count-decimals') ? parseInt(el.getAttribute('data-count-decimals'), 10) : 0;
      const duration = 1100;
      const start = performance.now();
      function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = target * eased;
        el.textContent = prefix + value.toFixed(decimals) + suffix;
        if (progress < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }, { threshold: 0.6 });
  countEls.forEach(el => countObserver.observe(el));
}

// ===== Subtle parallax on hero decor =====
if (!prefersReducedMotion) {
  const heroDecor = document.querySelector('.hero-decor');
  if (heroDecor) {
    window.addEventListener('scroll', () => {
      const offset = window.scrollY * 0.15;
      heroDecor.style.transform = `translateY(${offset}px)`;
    }, { passive: true });
  }
}

// ===== Footer year =====
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// ===== Contact form submission (Formspree) =====
const contactForm = document.getElementById('contactForm');
const formNote = document.getElementById('formNote');
if (contactForm && formNote) {
  const submitBtn = contactForm.querySelector('button[type="submit"]');

  contactForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    formNote.classList.remove('error');
    formNote.textContent = 'Sending...';
    if (submitBtn) submitBtn.disabled = true;

    try {
      const response = await fetch(contactForm.action, {
        method: 'POST',
        body: new FormData(contactForm),
        headers: { 'Accept': 'application/json' }
      });

      if (response.ok) {
        formNote.textContent = "Thanks — your message is on its way. I'll get back to you within 24 hours.";
        contactForm.reset();
      } else {
        const data = await response.json().catch(() => null);
        const detail = data && Array.isArray(data.errors) && data.errors.length
          ? data.errors.map(e => e.message).join(', ')
          : null;
        formNote.textContent = detail || "Something went wrong — please try again or use the email link below.";
        formNote.classList.add('error');
      }
    } catch (err) {
      formNote.textContent = "Couldn't send — please check your connection or use the email link below.";
      formNote.classList.add('error');
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  });
}

// ===== Currency converter for pricing (display only — quotes/invoices stay in USD) =====
(function () {
  const priceEls = document.querySelectorAll('.price-num[data-usd]');
  const select = document.getElementById('currencySelect');
  if (!priceEls.length) return;

  const SYMBOLS = { USD: '$', GBP: '£', INR: '₹' };
  const RATE_CACHE_KEY = 'wcCurrencyRates';
  const RATE_CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours
  const CURRENCY_KEY = 'wcCurrency';

  function guessDefaultCurrency() {
    const lang = (navigator.language || '').toLowerCase();
    if (lang.endsWith('-gb')) return 'GBP';
    if (lang.endsWith('-in') || lang.startsWith('hi')) return 'INR';
    return 'USD';
  }

  function getCachedRates() {
    try {
      const raw = localStorage.getItem(RATE_CACHE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed.time || Date.now() - parsed.time > RATE_CACHE_TTL) return null;
      return parsed.rates || null;
    } catch (err) {
      return null;
    }
  }

  function setCachedRates(rates) {
    try {
      localStorage.setItem(RATE_CACHE_KEY, JSON.stringify({ time: Date.now(), rates }));
    } catch (err) {
      // localStorage unavailable (private browsing, etc.) — safe to ignore
    }
  }

  function applyCurrency(currency, rates) {
    const rate = currency === 'USD' ? 1 : rates && rates[currency];
    if (!rate) return; // no rate yet — leave the current (USD fallback) values in place
    priceEls.forEach((el) => {
      const usd = parseFloat(el.getAttribute('data-usd'));
      const converted = Math.round(usd * rate);
      el.setAttribute('data-count-to', String(converted));
      el.setAttribute('data-count-prefix', SYMBOLS[currency]);
      el.textContent = SYMBOLS[currency] + converted;
    });
  }

  let currentCurrency = localStorage.getItem(CURRENCY_KEY) || guessDefaultCurrency();
  if (select) select.value = currentCurrency;

  const cachedRates = getCachedRates();
  if (cachedRates) applyCurrency(currentCurrency, cachedRates);

  fetch('https://api.frankfurter.dev/v1/latest?from=USD&to=GBP,INR')
    .then((res) => (res.ok ? res.json() : Promise.reject(res)))
    .then((data) => {
      if (data && data.rates) {
        setCachedRates(data.rates);
        applyCurrency(currentCurrency, data.rates);
      }
    })
    .catch(() => {
      // Rate fetch failed — quietly keep displaying USD, no visible error to the visitor
    });

  if (select) {
    select.addEventListener('change', () => {
      currentCurrency = select.value;
      try { localStorage.setItem(CURRENCY_KEY, currentCurrency); } catch (err) {}
      applyCurrency(currentCurrency, getCachedRates());
    });
  }
})();
