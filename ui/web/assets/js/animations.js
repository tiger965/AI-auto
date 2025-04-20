/**
 * Animations.js - UI animation effects
 * Project: AI Automation Interface
 * 
 * This file handles all animation effects for the interface,
 * providing smooth transitions and visual feedback.
 */

// Wait for DOM to be fully loaded before executing
document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations based on user preference
    const reduceMotion = document.documentElement.classList.contains('reduce-motion');
    
    if (!reduceMotion) {
        initPageTransitions();
        initElementAnimations();
        initButtonEffects();
        initFeedbackAnimations();
    } else {
        // Apply minimal animations for users with reduce-motion preference
        initMinimalAnimations();
    }
});

/**
 * Initialize page transition effects
 */
function initPageTransitions() {
    // Fade in page content on load
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
        mainContent.style.opacity = '0';
        setTimeout(() => {
            mainContent.style.transition = 'opacity 0.5s ease';
            mainContent.style.opacity = '1';
        }, 100);
    }
    
    // Setup page exit animations
    document.addEventListener('beforeunload', function() {
        document.body.classList.add('page-exit');
    });
    
    // Intercept internal link clicks for smooth transitions
    document.addEventListener('click', function(e) {
        // Find closest anchor tag
        const link = e.target.closest('a');
        
        if (link && 
            !link.target && 
            link.hostname === window.location.hostname && 
            !e.ctrlKey && 
            !e.metaKey && 
            !e.shiftKey) {
            
            e.preventDefault();
            
            // Begin transition out
            mainContent.style.transition = 'opacity 0.3s ease';
            mainContent.style.opacity = '0';
            
            // Wait for animation to complete before navigating
            setTimeout(() => {
                window.location.href = link.href;
            }, 300);
        }
    });
}

/**
 * Initialize animations for UI elements
 */
function initElementAnimations() {
    // Animate cards when they enter viewport
    const cards = document.querySelectorAll('.card');
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('card-animate-in');
                cardObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    cards.forEach(card => {
        card.classList.add('card-prepare-animation');
        cardObserver.observe(card);
    });
    
    // Animate list items with staggered delay
    const lists = document.querySelectorAll('ul.animate-list, ol.animate-list');
    const listObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Get all list items
                const items = entry.target.querySelectorAll('li');
                
                // Apply staggered animation
                items.forEach((item, index) => {
                    item.style.animationDelay = `${index * 0.1}s`;
                    item.classList.add('item-animate-in');
                });
                
                listObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    lists.forEach(list => {
        list.classList.add('list-prepare-animation');
        listObserver.observe(list);
    });
    
    // Section reveal animations
    const sections = document.querySelectorAll('.section-animate');
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('section-animate-in');
                sectionObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    sections.forEach(section => {
        section.classList.add('section-prepare-animation');
        sectionObserver.observe(section);
    });
}

/**
 * Initialize button click and hover effects
 */
function initButtonEffects() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        // Ripple effect on click
        button.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            // Remove ripple after animation completes
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
        
        // Hover effect
        button.addEventListener('mouseenter', function() {
            this.classList.add('btn-hover');
        });
        
        button.addEventListener('mouseleave', function() {
            this.classList.remove('btn-hover');
        });
        
        // Focus effect for accessibility
        button.addEventListener('focus', function() {
            this.classList.add('btn-focus');
        });
        
        button.addEventListener('blur', function() {
            this.classList.remove('btn-focus');
        });
    });
    
    // Special effects for action buttons
    const actionButtons = document.querySelectorAll('.btn-action');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Add pulse effect
            this.classList.add('btn-pulse');
            
            // Remove pulse after animation completes
            setTimeout(() => {
                this.classList.remove('btn-pulse');
            }, 500);
        });
    });
}

/**
 * Initialize feedback animations (success, error, etc.)
 */
function initFeedbackAnimations() {
    // Success message animation
    const successMessages = document.querySelectorAll('.success-message');
    successMessages.forEach(message => {
        // Add slide-in and fade effect
        message.classList.add('message-animate-in');
        
        // Auto-dismiss after 5 seconds if it has auto-dismiss class
        if (message.classList.contains('auto-dismiss')) {
            setTimeout(() => {
                message.classList.add('message-animate-out');
                
                // Remove from DOM after animation completes
                setTimeout(() => {
                    message.remove();
                }, 500);
            }, 5000);
        }
        
        // Add close button functionality
        const closeBtn = message.querySelector('.close-message');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                message.classList.add('message-animate-out');
                
                // Remove from DOM after animation completes
                setTimeout(() => {
                    message.remove();
                }, 500);
            });
        }
    });
    
    // Error shake animation
    const errorFields = document.querySelectorAll('.is-invalid');
    errorFields.forEach(field => {
        field.classList.add('shake-animation');
        
        // Remove animation class after it completes
        setTimeout(() => {
            field.classList.remove('shake-animation');
        }, 500);
    });
    
    // Loading spinner animations
    const loadingSpinners = document.querySelectorAll('.loading-spinner');
    loadingSpinners.forEach(spinner => {
        // Add pulsing effect
        spinner.classList.add('spinner-pulse');
    });
    
    // Progress bar animations
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        // Get target width from data attribute
        const targetWidth = bar.dataset.progress || '0';
        
        // Start at 0 width
        bar.style.width = '0%';
        
        // Animate to target width
        setTimeout(() => {
            bar.style.transition = 'width 1s ease-in-out';
            bar.style.width = `${targetWidth}%`;
        }, 100);
    });
}

/**
 * Initialize minimal animations for users with reduce-motion preference
 */
function initMinimalAnimations() {
    // Apply instant transitions instead of animations
    document.documentElement.style.setProperty('--transition-normal', '0s');
    
    // Remove all animation classes
    const animatedElements = document.querySelectorAll('.card-prepare-animation, .list-prepare-animation, .section-prepare-animation');
    animatedElements.forEach(element => {
        // Replace with instant visibility
        element.style.opacity = '1';
        element.style.transform = 'none';
    });
    
    // Simplified feedback indicators
    const successMessages = document.querySelectorAll('.success-message');
    successMessages.forEach(message => {
        message.style.opacity = '1';
        message.style.transform = 'none';
    });
    
    // Set loading spinners to static state
    const loadingSpinners = document.querySelectorAll('.loading-spinner');
    loadingSpinners.forEach(spinner => {
        spinner.classList.add('spinner-static');
    });
    
    // Instant progress bars
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const targetWidth = bar.dataset.progress || '0';
        bar.style.transition = 'none';
        bar.style.width = `${targetWidth}%`;
    });
}

/**
 * Show toast notification with animation
 * @param {string} message - Message to display in toast
 * @param {string} type - Type of toast (success, error, info, warning)
 * @param {number} duration - Duration to show toast in ms (default: 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    
    // Add toast content
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon"></span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" aria-label="Close">&times;</button>
        </div>
    `;
    
    // Add to toast container (create if it doesn't exist)
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
        toast.classList.add('toast-show');
    }, 10);
    
    // Setup close button
    const closeButton = toast.querySelector('.toast-close');
    closeButton.addEventListener('click', () => {
        closeToast(toast);
    });
    
    // Auto-close after duration
    if (duration > 0) {
        setTimeout(() => {
            closeToast(toast);
        }, duration);
    }
}

/**
 * Close toast with animation
 * @param {HTMLElement} toast - Toast element to close
 */
function closeToast(toast) {
    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');
    
    // Remove from DOM after animation completes
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
        
        // Remove container if no more toasts
        const toastContainer = document.querySelector('.toast-container');
        if (toastContainer && toastContainer.children.length === 0) {
            toastContainer.remove();
        }
    }, 300);
}

/**
 * Create and animate a modal dialog
 * @param {string} title - Modal title
 * @param {string} content - Modal content (HTML allowed)
 * @param {Object} options - Modal options
 */
function showModal(title, content, options = {}) {
    // Default options
    const defaultOptions = {
        closeButton: true,
        confirmButton: false,
        confirmText: 'OK',
        cancelButton: false,
        cancelText: 'Cancel',
        size: 'medium', // small, medium, large
        onConfirm: null,
        onCancel: null,
        onClose: null
    };
    
    // Merge options
    const modalOptions = { ...defaultOptions, ...options };
    
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    
    // Create modal container
    const modal = document.createElement('div');
    modal.className = `modal modal-${modalOptions.size}`;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    
    // Create modal content
    let modalHTML = `
        <div class="modal-header">
            <h3 class="modal-title">${title}</h3>
            ${modalOptions.closeButton ? '<button class="modal-close" aria-label="Close">&times;</button>' : ''}
        </div>
        <div class="modal-body">
            ${content}
        </div>
    `;
    
    // Add footer if needed
    if (modalOptions.confirmButton || modalOptions.cancelButton) {
        modalHTML += `
            <div class="modal-footer">
                ${modalOptions.cancelButton ? `<button class="btn btn-outline modal-cancel">${modalOptions.cancelText}</button>` : ''}
                ${modalOptions.confirmButton ? `<button class="btn btn-primary modal-confirm">${modalOptions.confirmText}</button>` : ''}
            </div>
        `;
    }
    
    modal.innerHTML = modalHTML;
    
    // Add to DOM
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Prevent body scrolling
    document.body.classList.add('modal-open');
    
    // Animate open
    setTimeout(() => {
        overlay.classList.add('modal-overlay-show');
        modal.classList.add('modal-show');
    }, 10);
    
    // Setup event listeners
    if (modalOptions.closeButton) {
        const closeButton = modal.querySelector('.modal-close');
        closeButton.addEventListener('click', () => {
            closeModal(overlay, modal, modalOptions.onClose);
        });
    }
    
    if (modalOptions.confirmButton) {
        const confirmButton = modal.querySelector('.modal-confirm');
        confirmButton.addEventListener('click', () => {
            closeModal(overlay, modal, modalOptions.onConfirm);
        });
    }
    
    if (modalOptions.cancelButton) {
        const cancelButton = modal.querySelector('.modal-cancel');
        cancelButton.addEventListener('click', () => {
            closeModal(overlay, modal, modalOptions.onCancel);
        });
    }
    
    // Close when clicking overlay
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeModal(overlay, modal, modalOptions.onClose);
        }
    });
    
    // Close on Escape key
    document.addEventListener('keydown', function escapeListener(e) {
        if (e.key === 'Escape') {
            document.removeEventListener('keydown', escapeListener);
            closeModal(overlay, modal, modalOptions.onClose);
        }
    });
    
    // Return modal reference
    return {
        overlay,
        modal,
        close: () => closeModal(overlay, modal)
    };
}

/**
 * Close modal with animation
 * @param {HTMLElement} overlay - Modal overlay
 * @param {HTMLElement} modal - Modal element
 * @param {Function} callback - Optional callback to execute after closing
 */
function closeModal(overlay, modal, callback = null) {
    overlay.classList.remove('modal-overlay-show');
    modal.classList.remove('modal-show');
    modal.classList.add('modal-hide');
    
    // Execute callback if provided
    if (typeof callback === 'function') {
        callback();
    }
    
    // Remove from DOM after animation completes
    setTimeout(() => {
        if (overlay.parentNode) {
            document.body.removeChild(overlay);
        }
        
        // Restore body scrolling if no other modals are open
        if (!document.querySelector('.modal-overlay')) {
            document.body.classList.remove('modal-open');
        }
    }, 300);
}

/**
 * Create a typing animation effect
 * @param {HTMLElement} element - Element to apply typing effect to
 * @param {string} text - Text to type
 * @param {number} speed - Typing speed in ms per character
 * @param {Function} callback - Callback after animation completes
 */
function typeEffect(element, text, speed = 50, callback = null) {
    let i = 0;
    element.textContent = '';
    
    // Clear any existing timers on this element
    if (element._typeTimer) {
        clearInterval(element._typeTimer);
    }
    
    // Start typing effect
    element._typeTimer = setInterval(() => {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
        } else {
            clearInterval(element._typeTimer);
            element._typeTimer = null;
            
            if (typeof callback === 'function') {
                callback();
            }
        }
    }, speed);
    
    // Return control object
    return {
        stop: () => {
            if (element._typeTimer) {
                clearInterval(element._typeTimer);
                element._typeTimer = null;
            }
        },
        complete: () => {
            if (element._typeTimer) {
                clearInterval(element._typeTimer);
                element._typeTimer = null;
                element.textContent = text;
                
                if (typeof callback === 'function') {
                    callback();
                }
            }
        }
    };
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showToast,
        showModal,
        typeEffect
    };
} else {
    // Add to window object in browser environment
    window.uiAnimations = {
        showToast,
        showModal,
        typeEffect
    };
}