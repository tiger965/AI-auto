/**
 * Main.js - Core JavaScript functionality
 * Project: AI Automation Interface
 * 
 * This file contains the main interactive functionality for the application,
 * including form handling, theme switching, and navigation.
 */

// Wait for DOM to be fully loaded before executing
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initThemeToggle();
    initMobileNavigation();
    initFormValidation();
    setupUserPreferences();
    
    // Check for stored preferences
    applyStoredPreferences();
});

/**
 * Theme Toggling Functionality
 * Handles switching between light and dark themes
 */
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            toggleTheme();
        });
    }
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
    // Add transition class to prevent visual glitches during theme change
    document.body.classList.add('theme-transition');
    
    // Toggle between themes
    if (document.body.classList.contains('night-theme')) {
        document.body.classList.remove('night-theme');
        document.body.classList.add('harmony-theme');
        localStorage.setItem('theme', 'harmony');
        // Update any theme indicators (like toggle switches)
        updateThemeIndicators('harmony');
    } else {
        document.body.classList.remove('harmony-theme');
        document.body.classList.add('night-theme');
        localStorage.setItem('theme', 'night');
        // Update any theme indicators (like toggle switches)
        updateThemeIndicators('night');
    }
    
    // Remove transition class after a short delay
    setTimeout(function() {
        document.body.classList.remove('theme-transition');
    }, 300);
}

/**
 * Update UI elements that indicate current theme
 * @param {string} theme - Current theme name
 */
function updateThemeIndicators(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
        if (theme === 'night') {
            themeToggle.innerHTML = '<i class="icon">☀️</i>';
            themeToggle.setAttribute('aria-label', 'Switch to light theme');
        } else {
            themeToggle.innerHTML = '<i class="icon">🌙</i>';
            themeToggle.setAttribute('aria-label', 'Switch to dark theme');
        }
    }
}

/**
 * Apply stored theme preference from localStorage
 */
function applyStoredPreferences() {
    const storedTheme = localStorage.getItem('theme');
    
    // If no theme is stored, check for system preference
    if (!storedTheme) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (prefersDark) {
            document.body.classList.add('night-theme');
            updateThemeIndicators('night');
        } else {
            document.body.classList.add('harmony-theme');
            updateThemeIndicators('harmony');
        }
    } else {
        // Apply stored theme
        if (storedTheme === 'night') {
            document.body.classList.add('night-theme');
            updateThemeIndicators('night');
        } else {
            document.body.classList.add('harmony-theme');
            updateThemeIndicators('harmony');
        }
    }
    
    // Apply other stored preferences
    applyFontSize();
    applyAnimationPreference();
    applyAudioPreference();
}

/**
 * Mobile Navigation Toggle
 */
function initMobileNavigation() {
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarNav = document.querySelector('.navbar-nav');
    
    if (navbarToggle && navbarNav) {
        navbarToggle.addEventListener('click', function() {
            navbarNav.classList.toggle('show');
            
            // Update ARIA attributes for accessibility
            const expanded = navbarNav.classList.contains('show');
            navbarToggle.setAttribute('aria-expanded', expanded);
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navbarToggle.contains(event.target) && !navbarNav.contains(event.target)) {
                if (navbarNav.classList.contains('show')) {
                    navbarNav.classList.remove('show');
                    navbarToggle.setAttribute('aria-expanded', false);
                }
            }
        });
    }
}

/**
 * Form Validation
 * Client-side validation for all forms
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add validation on submit
        form.addEventListener('submit', validateForm);
        
        // Add live validation on input
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateInput(this);
            });
        });
    });
}

/**
 * Validate a form on submission
 * @param {Event} event - Form submit event
 */
function validateForm(event) {
    const form = event.target;
    let isValid = true;
    
    // Validate all inputs in the form
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        if (!validateInput(input)) {
            isValid = false;
        }
    });
    
    // If form is invalid, prevent submission
    if (!isValid) {
        event.preventDefault();
        event.stopPropagation();
        
        // Focus the first invalid input
        const firstInvalid = form.querySelector('.is-invalid');
        if (firstInvalid) {
            firstInvalid.focus();
        }
    } else {
        // Form is valid, prepare for submission
        prepareFormData(form);
    }
}

/**
 * Validate a single input field
 * @param {HTMLElement} input - Input element to validate
 * @returns {boolean} - Whether the input is valid
 */
function validateInput(input) {
    // Skip validation for disabled inputs
    if (input.disabled || input.type === 'hidden') {
        return true;
    }
    
    let isValid = true;
    const value = input.value.trim();
    
    // Remove previous validation state
    input.classList.remove('is-valid', 'is-invalid');
    
    // Check for required fields
    if (input.hasAttribute('required') && value === '') {
        setInputInvalid(input, 'This field is required');
        isValid = false;
    }
    
    // Validate email format
    else if (input.type === 'email' && value !== '') {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(value)) {
            setInputInvalid(input, 'Please enter a valid email address');
            isValid = false;
        }
    }
    
    // Validate URL format
    else if (input.type === 'url' && value !== '') {
        try {
            new URL(value);
        } catch (e) {
            setInputInvalid(input, 'Please enter a valid URL');
            isValid = false;
        }
    }
    
    // Validate password strength
    else if (input.type === 'password' && input.dataset.minLength) {
        const minLength = parseInt(input.dataset.minLength, 10);
        if (value.length < minLength) {
            setInputInvalid(input, `Password must be at least ${minLength} characters`);
            isValid = false;
        }
    }
    
    // Validate number inputs
    else if (input.type === 'number') {
        const min = input.hasAttribute('min') ? parseFloat(input.min) : null;
        const max = input.hasAttribute('max') ? parseFloat(input.max) : null;
        const numValue = parseFloat(value);
        
        if (value !== '' && isNaN(numValue)) {
            setInputInvalid(input, 'Please enter a valid number');
            isValid = false;
        } else if (min !== null && numValue < min) {
            setInputInvalid(input, `Minimum value is ${min}`);
            isValid = false;
        } else if (max !== null && numValue > max) {
            setInputInvalid(input, `Maximum value is ${max}`);
            isValid = false;
        }
    }
    
    // Custom validation based on data-validate attribute
    else if (input.dataset.validate) {
        switch (input.dataset.validate) {
            case 'alpha-only':
                if (!/^[A-Za-z\s]+$/.test(value) && value !== '') {
                    setInputInvalid(input, 'Please use only letters');
                    isValid = false;
                }
                break;
            case 'numeric-only':
                if (!/^[0-9]+$/.test(value) && value !== '') {
                    setInputInvalid(input, 'Please use only numbers');
                    isValid = false;
                }
                break;
            // Add more custom validations as needed
        }
    }
    
    // Input is valid
    if (isValid && value !== '') {
        input.classList.add('is-valid');
    }
    
    return isValid;
}

/**
 * Mark an input as invalid with a specific message
 * @param {HTMLElement} input - Input element to mark
 * @param {string} message - Error message to display
 */
function setInputInvalid(input, message) {
    input.classList.add('is-invalid');
    
    // Find or create feedback element
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentNode.insertBefore(feedback, input.nextSibling);
    }
    
    feedback.textContent = message;
}

/**
 * Prepare form data before submission
 * @param {HTMLFormElement} form - Form to prepare
 */
function prepareFormData(form) {
    // Example: Add timestamp to form data
    const timestampInput = document.createElement('input');
    timestampInput.type = 'hidden';
    timestampInput.name = 'submittedAt';
    timestampInput.value = Date.now();
    form.appendChild(timestampInput);
    
    // Example: Track form analytics
    if (typeof trackFormSubmission === 'function') {
        trackFormSubmission(form.id);
    }
}

/**
 * User Preferences Management
 * Setup UI controls for user preferences
 */
function setupUserPreferences() {
    // Font size preference
    const fontSizeControls = document.querySelectorAll('[data-preference="font-size"]');
    fontSizeControls.forEach(control => {
        control.addEventListener('click', function() {
            const size = this.dataset.value;
            setFontSizePreference(size);
        });
    });
    
    // Animation preference
    const animationToggle = document.getElementById('animation-toggle');
    if (animationToggle) {
        animationToggle.addEventListener('change', function() {
            const enableAnimations = this.checked;
            setAnimationPreference(enableAnimations);
        });
    }
    
    // Audio preference
    const audioToggle = document.getElementById('audio-toggle');
    if (audioToggle) {
        audioToggle.addEventListener('change', function() {
            const enableAudio = this.checked;
            setAudioPreference(enableAudio);
        });
    }
}

/**
 * Set font size preference
 * @param {string} size - Font size preference (small, medium, large)
 */
function setFontSizePreference(size) {
    localStorage.setItem('fontSizePreference', size);
    applyFontSize();
}

/**
 * Apply stored font size preference
 */
function applyFontSize() {
    const size = localStorage.getItem('fontSizePreference') || 'medium';
    
    // Remove existing size classes
    document.documentElement.classList.remove('font-size-small', 'font-size-medium', 'font-size-large');
    
    // Add appropriate size class
    document.documentElement.classList.add(`font-size-${size}`);
    
    // Update UI indicators
    const fontSizeControls = document.querySelectorAll('[data-preference="font-size"]');
    fontSizeControls.forEach(control => {
        if (control.dataset.value === size) {
            control.classList.add('active');
        } else {
            control.classList.remove('active');
        }
    });
}

/**
 * Set animation preference
 * @param {boolean} enabled - Whether animations should be enabled
 */
function setAnimationPreference(enabled) {
    localStorage.setItem('animationsEnabled', enabled ? 'true' : 'false');
    applyAnimationPreference();
}

/**
 * Apply stored animation preference
 */
function applyAnimationPreference() {
    const enabled = localStorage.getItem('animationsEnabled') !== 'false';
    
    if (!enabled) {
        document.documentElement.classList.add('reduce-motion');
    } else {
        document.documentElement.classList.remove('reduce-motion');
    }
    
    // Update UI indicators
    const animationToggle = document.getElementById('animation-toggle');
    if (animationToggle) {
        animationToggle.checked = enabled;
    }
}

/**
 * Set audio preference
 * @param {boolean} enabled - Whether audio should be enabled
 */
function setAudioPreference(enabled) {
    localStorage.setItem('audioEnabled', enabled ? 'true' : 'false');
    applyAudioPreference();
}

/**
 * Apply stored audio preference
 */
function applyAudioPreference() {
    const enabled = localStorage.getItem('audioEnabled') !== 'false';
    
    // Set global audio state
    window.audioEnabled = enabled;
    
    // Update UI indicators
    const audioToggle = document.getElementById('audio-toggle');
    if (audioToggle) {
        audioToggle.checked = enabled;
    }
}

/**
 * Page Navigation without refresh
 * @param {string} url - URL to navigate to
 */
function navigateTo(url) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            // Extract the content area from the loaded HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const content = doc.querySelector('#main-content').innerHTML;
            
            // Update the current page's content
            document.querySelector('#main-content').innerHTML = content;
            
            // Update URL in browser history
            window.history.pushState({}, '', url);
            
            // Update active state in navigation
            updateNavigation(url);
            
            // Re-initialize components on the new page
            initFormValidation();
        })
        .catch(error => {
            console.error('Navigation error:', error);
            // Fallback to traditional navigation
            window.location.href = url;
        });
}

/**
 * Update navigation active states
 * @param {string} url - Current URL
 */
function updateNavigation(url) {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === url) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Initialize navigation events
 */
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            // Skip for external links or links with modifiers
            if (this.target === '_blank' || 
                event.ctrlKey || 
                event.metaKey || 
                event.shiftKey) {
                return;
            }
            
            event.preventDefault();
            navigateTo(this.getAttribute('href'));
        });
    });
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', function() {
        navigateTo(window.location.pathname);
    });
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        toggleTheme,
        validateForm,
        validateInput,
        navigateTo
    };
}