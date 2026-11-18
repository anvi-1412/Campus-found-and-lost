/**
 * Campus Lost & Found Management System - Main Interactive JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Navigation Toggle
  const mobileToggle = document.querySelector('.mobile-nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', function () {
      navLinks.classList.toggle('active');
      const isExpanded = navLinks.classList.contains('active');
      mobileToggle.setAttribute('aria-expanded', isExpanded);
    });
  }

  // 2. Alert Dismissal & Auto-fade
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      });
    }

    // Auto dismiss after 6 seconds
    setTimeout(function () {
      if (alert && alert.parentElement) {
        alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 400);
      }
    }, 6000);
  });

  // 3. Tab Switching Component
  const tabButtons = document.querySelectorAll('.tab-btn');
  tabButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      const targetTab = this.getAttribute('data-tab');
      const parentContainer = this.closest('.tabs-container') || document;

      // Update active button
      parentContainer.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');

      // Update active pane
      parentContainer.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
      const activePane = parentContainer.querySelector(`#${targetTab}`);
      if (activePane) {
        activePane.classList.add('active');
      }

      // Update URL hash without scroll jump
      if (history.pushState) {
        history.pushState(null, null, `?tab=${targetTab.replace('tab-', '')}`);
      }
    });
  });

  // 4. File Upload Drag & Drop with Instant Image Preview
  const uploadZones = document.querySelectorAll('.file-upload-zone');
  uploadZones.forEach(function (zone) {
    const input = zone.querySelector('input[type="file"]');
    const previewContainer = zone.parentElement.querySelector('.file-preview-container');
    const previewImg = previewContainer ? previewContainer.querySelector('.file-preview-img') : null;
    const removeBtn = previewContainer ? previewContainer.querySelector('.file-preview-remove') : null;

    if (!input) return;

    ['dragenter', 'dragover'].forEach(eventName => {
      zone.addEventListener(eventName, function (e) {
        e.preventDefault();
        zone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      zone.addEventListener(eventName, function (e) {
        e.preventDefault();
        zone.classList.remove('dragover');
      }, false);
    });

    zone.addEventListener('drop', function (e) {
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        input.files = e.dataTransfer.files;
        handlePreview(input.files[0]);
      }
    });

    input.addEventListener('change', function () {
      if (this.files && this.files[0]) {
        handlePreview(this.files[0]);
      }
    });

    function handlePreview(file) {
      // Validate file size (< 8MB)
      if (file.size > 8 * 1024 * 1024) {
        alert('File size exceeds 8MB limit. Please choose a smaller photo.');
        input.value = '';
        return;
      }

      // Validate image mime type
      if (!file.type.startsWith('image/')) {
        alert('Please choose an image file (PNG, JPG, JPEG, WEBP).');
        input.value = '';
        return;
      }

      if (previewContainer && previewImg) {
        const reader = new FileReader();
        reader.onload = function (e) {
          previewImg.src = e.target.result;
          previewContainer.style.display = 'block';
          zone.style.display = 'none';
        };
        reader.readAsDataURL(file);
      }
    }

    if (removeBtn) {
      removeBtn.addEventListener('click', function (e) {
        e.preventDefault();
        input.value = '';
        if (previewImg) previewImg.src = '';
        if (previewContainer) previewContainer.style.display = 'none';
        zone.style.display = 'block';
      });
    }
  });

  // 5. Client-Side Form Validations
  const registerForm = document.querySelector('form#register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', function (e) {
      const password = document.getElementById('password');
      const confirmPassword = document.getElementById('confirm_password');

      if (password && confirmPassword && password.value !== confirmPassword.value) {
        e.preventDefault();
        alert('Passwords do not match! Please check and try again.');
        confirmPassword.focus();
      }
    });
  }

  // 6. Generic Modal Open/Close Support
  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
    }
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  };

  // Close modals on clicking backdrop
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', function (e) {
      if (e.target === this) {
        this.classList.remove('active');
      }
    });
  });
});
