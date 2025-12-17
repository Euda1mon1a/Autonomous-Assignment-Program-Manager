/**
 * Extra JavaScript for Residency Scheduler Documentation
 */

// Add smooth scroll behavior for anchor links
document.addEventListener('DOMContentLoaded', function() {
  // Smooth scrolling for internal links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href').substring(1);
      const targetElement = document.getElementById(targetId);

      if (targetElement) {
        e.preventDefault();
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Add 'external' class to external links
  document.querySelectorAll('a[href^="http"]').forEach(link => {
    if (!link.href.includes(window.location.hostname)) {
      link.classList.add('external');
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });

  // Initialize feature cards animation
  const featureCards = document.querySelectorAll('.feature-card');
  if (featureCards.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }
      });
    }, { threshold: 0.1 });

    featureCards.forEach(card => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(20px)';
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      observer.observe(card);
    });
  }

  // Copy code button enhancement
  document.querySelectorAll('.md-clipboard').forEach(button => {
    button.addEventListener('click', function() {
      // Add visual feedback
      this.classList.add('copied');
      setTimeout(() => {
        this.classList.remove('copied');
      }, 2000);
    });
  });

  // Add keyboard shortcut hints
  document.addEventListener('keydown', function(e) {
    // Press '/' to focus search
    if (e.key === '/' && !isInputFocused()) {
      e.preventDefault();
      const searchInput = document.querySelector('.md-search__input');
      if (searchInput) {
        searchInput.focus();
      }
    }

    // Press 'Escape' to blur search
    if (e.key === 'Escape') {
      document.activeElement.blur();
    }
  });
});

// Helper function to check if an input is focused
function isInputFocused() {
  const activeElement = document.activeElement;
  return activeElement.tagName === 'INPUT' ||
         activeElement.tagName === 'TEXTAREA' ||
         activeElement.isContentEditable;
}

// Theme toggle enhancement with transition
document$.subscribe(function() {
  const themeToggle = document.querySelector('[data-md-component="palette"]');
  if (themeToggle) {
    themeToggle.addEventListener('change', function() {
      // Add smooth transition when theme changes
      document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
      setTimeout(() => {
        document.body.style.transition = '';
      }, 300);
    });
  }
});

// Progress indicator for long pages
document.addEventListener('scroll', function() {
  const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
  const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
  const scrolled = (winScroll / height) * 100;

  const progressBar = document.querySelector('.progress-bar-fill');
  if (progressBar) {
    progressBar.style.width = scrolled + '%';
  }
});

// Console Easter egg
console.log('%c🌺 Aloha! Welcome to Residency Scheduler Documentation',
  'background: linear-gradient(135deg, #E57373, #26A69A); color: white; padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: bold;');
console.log('%cBuilt with care for healthcare professionals',
  'color: #26A69A; font-size: 12px;');
