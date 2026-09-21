/**
 * Student Internship Cloud Portal — JavaScript
 * AWS Cloud Web Application Project
 *
 * NOTE: This file contains NO AWS credentials, account IDs, or secrets.
 * EC2 metadata is loaded dynamically from the server-side health endpoint.
 */

'use strict';

/* ============================================================
   Smooth Scroll for nav links
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  const navLinks = document.querySelectorAll('a[href^="#"]');
  navLinks.forEach(link => {
    link.addEventListener('click', e => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
});

/* ============================================================
   Intersection Observer — fade-in on scroll
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  const animatables = document.querySelectorAll(
    '.overview-card, .service-card, .security-card, ' +
    '.alarm-card, .backup-step, .cost-card'
  );

  animatables.forEach((el, index) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = `opacity 0.5s ease ${index * 0.07}s, transform 0.5s ease ${index * 0.07}s`;
    observer.observe(el);
  });
});

/* ============================================================
   Live clock in status bar
   ============================================================ */
function updateClock() {
  const el = document.getElementById('live-clock');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toUTCString().replace('GMT', 'UTC');
}

document.addEventListener('DOMContentLoaded', () => {
  updateClock();
  setInterval(updateClock, 1000);
});

/* ============================================================
   Health check — calls /health endpoint and updates status
   ============================================================ */
async function checkHealth() {
  const statusEl   = document.getElementById('app-status');
  const statusDot  = document.getElementById('status-dot');

  if (!statusEl) return;

  try {
    const response = await fetch('health.html', {
      method: 'GET',
      cache: 'no-store',
      signal: AbortSignal.timeout(5000)
    });

    if (response.ok) {
      statusEl.textContent  = 'Application: Healthy';
      if (statusDot) {
        statusDot.className = 'status-dot green';
      }
    } else {
      statusEl.textContent = 'Application: Degraded';
      if (statusDot) statusDot.className = 'status-dot orange';
    }
  } catch {
    // Expected when running locally without a server — not an error
    statusEl.textContent = 'Application: Running Locally';
    if (statusDot) statusDot.className = 'status-dot orange';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  setInterval(checkHealth, 60000); // re-check every 60 s
});

/* ============================================================
   Copy-to-clipboard for code blocks
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('pre').forEach(pre => {
    const btn = document.createElement('button');
    btn.textContent = 'Copy';
    btn.style.cssText = `
      position:absolute; top:0.6rem; right:0.6rem;
      background:rgba(255,153,0,0.15); color:#FF9900;
      border:1px solid rgba(255,153,0,0.3); border-radius:4px;
      padding:0.25rem 0.6rem; font-size:0.75rem;
      cursor:pointer; transition:all 0.2s;
    `;
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(pre.innerText).then(() => {
        btn.textContent = 'Copied!';
        btn.style.color = '#2ECC71';
        setTimeout(() => { btn.textContent = 'Copy'; btn.style.color = '#FF9900'; }, 2000);
      });
    });
    pre.style.position = 'relative';
    pre.appendChild(btn);
  });
});

/* ============================================================
   Service card accent colour from data attribute
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.service-card[data-color]').forEach(card => {
    card.style.setProperty('--card-color', card.dataset.color);
  });
});
