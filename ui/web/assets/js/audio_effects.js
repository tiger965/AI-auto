/**
 * Audio_effects.js - Sound effects and audio management
 * Project: AI Automation Interface
 * 
 * This file handles all sound-related functionality including
 * user interaction sounds, notifications, and ambient audio.
 */

// Audio context for advanced audio processing
let audioContext;
// Global flag for audio enabled state
let audioEnabled = true;
// Cache for loaded audio buffers
const audioCache = {};
// Currently playing ambient sounds
const activeSounds = {};
// Volume settings
const volumeSettings = {
    master: 0.7,    // Master volume (0-1)
    ui: 0.5,        // UI sounds volume
    notification: 0.7, // Notification volume
    ambient: 0.3    // Ambient sounds volume
};

// Wait for DOM to be fully loaded before executing
document.addEventListener('DOMContentLoaded', function() {
    // Check user preference for audio
    audioEnabled = localStorage.getItem('audioEnabled') !== 'false';
    
    // Initialize audio context on first user interaction (browser requirement)
    document.addEventListener('click', initAudioContext, { once: true });
    document.addEventListener('keydown', initAudioContext, { once: true });
    
    // Initialize audio controls
    initAudioControls();
    
    // Preload common sounds
    if (audioEnabled) {
        preloadSounds();
    }
});

/**
 * Initialize the audio context (must be triggered by user interaction)
 */
function initAudioContext() {
    if (!audioContext) {
        try {
            window.AudioContext = window.AudioContext || window.webkitAudioContext;
            audioContext = new AudioContext();
            console.log('Audio context initialized');
        } catch (e) {
            console.error('Web Audio API not supported:', e);
        }
    }
}

/**
 * Initialize audio control elements
 */
function initAudioControls() {
    // Master audio toggle
    const audioToggle = document.getElementById('audio-toggle');
    if (audioToggle) {
        audioToggle.checked = audioEnabled;
        audioToggle.addEventListener('change', function() {
            audioEnabled = this.checked;
            localStorage.setItem('audioEnabled', audioEnabled);
            
            // Stop all sounds if disabled
            if (!audioEnabled) {
                stopAllSounds();
            }
        });
    }
    
    // Volume controls
    const volumeControls = document.querySelectorAll('[data-volume-control]');
    volumeControls.forEach(control => {
        const type = control.dataset.volumeControl;
        
        // Set initial value
        if (volumeSettings[type] !== undefined) {
            control.value = volumeSettings[type] * 100;
        }
        
        // Handle changes
        control.addEventListener('input', function() {
            const value = parseFloat(this.value) / 100;
            setVolume(type, value);
        });
    });
    
    // Ambient sound toggles
    const ambientToggles = document.querySelectorAll('[data-ambient-sound]');
    ambientToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const sound = this.dataset.ambientSound;
            
            if (this.checked) {
                playAmbientSound(sound);
            } else {
                stopAmbientSound(sound);
            }
        });
    });
}

/**
 * Preload commonly used sounds
 */
function preloadSounds() {
    // UI sounds
    loadSound('click', 'assets/audio/click.mp3');
    loadSound('notification', 'assets/audio/notification.mp3');
    
    // Only preload ambient sounds if explicitly requested
    // They're larger files, so we load them on demand otherwise
}

/**
 * Load a sound file into cache
 * @param {string} name - Reference name for the sound
 * @param {string} url - URL of the sound file
 * @returns {Promise} - Promise that resolves when the sound is loaded
 */
function loadSound(name, url) {
    return new Promise((resolve, reject) => {
        if (!audioContext) {
            initAudioContext();
        }
        
        // If audio context isn't available, fail silently
        if (!audioContext) {
            resolve(null);
            return;
        }
        
        // Check cache first
        if (audioCache[name]) {
            resolve(audioCache[name]);
            return;
        }
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load sound: ${response.status} ${response.statusText}`);
                }
                return response.arrayBuffer();
            })
            .then(arrayBuffer => audioContext.decodeAudioData(arrayBuffer))
            .then(audioBuffer => {
                audioCache[name] = audioBuffer;
                console.log(`Sound loaded: ${name}`);
                resolve(audioBuffer);
            })
            .catch(error => {
                console.error(`Error loading sound ${name}:`, error);
                reject(error);
            });
    });
}

/**
 * Play a sound effect
 * @param {string} name - Name of the sound to play
 * @param {Object} options - Options for playback
 * @param {number} options.volume - Volume for this sound (0-1)
 * @param {boolean} options.loop - Whether to loop the sound
 * @returns {Object|null} - Control object for the sound or null if disabled
 */
function playSound(name, options = {}) {
    // Check if audio is enabled
    if (!audioEnabled || !audioContext) {
        return null;
    }
    
    // Default options
    const defaultOptions = {
        volume: volumeSettings.ui,
        loop: false
    };
    
    // Merge options
    const soundOptions = { ...defaultOptions, ...options };
    
    // Get sound from cache or load it
    const sound = audioCache[name];
    if (!sound) {
        // Try to load it on demand
        loadSound(name, `assets/audio/${name}.mp3`)
            .then(buffer => {
                if (buffer) {
                    playSoundBuffer(buffer, soundOptions);
                }
            })
            .catch(error => console.error(`Could not play sound ${name}:`, error));
        
        return null;
    }
    
    // Play the cached sound
    return playSoundBuffer(sound, soundOptions);
}

/**
 * Internal function to play an audio buffer
 * @param {AudioBuffer} buffer - Audio buffer to play
 * @param {Object} options - Playback options
 * @returns {Object} - Control object for the sound
 */
function playSoundBuffer(buffer, options) {
    // Create source
    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.loop = options.loop;
    
    // Create gain node for volume control
    const gainNode = audioContext.createGain();
    gainNode.gain.value = options.volume * volumeSettings.master;
    
    // Connect nodes
    source.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Start playback
    source.start(0);
    
    // Create control object
    const control = {
        source,
        gainNode,
        stop: function() {
            try {
                source.stop(0);
            } catch (e) {
                // Ignore errors if already stopped
            }
        },
        setVolume: function(volume) {
            gainNode.gain.value = volume * volumeSettings.master;
        }
    };
    
    return control;
}

/**
 * Play UI click/interaction sound
 */
function playClickSound() {
    playSound('click', { volume: volumeSettings.ui });
}

/**
 * Play notification sound
 */
function playNotificationSound() {
    playSound('notification', { volume: volumeSettings.notification });
}

/**
 * Play an ambient background sound
 * @param {string} name - Name of ambient sound (must be in assets/audio/ambient/)
 * @returns {Object|null} - Control object for the sound or null if disabled
 */
function playAmbientSound(name) {
    // Stop any existing instance of this ambient sound
    stopAmbientSound(name);
    
    // Load and play the ambient sound
    const path = `assets/audio/ambient/${name}.mp3`;
    
    return loadSound(`ambient_${name}`, path)
        .then(buffer => {
            if (buffer) {
                const control = playSoundBuffer(buffer, {
                    volume: volumeSettings.ambient,
                    loop: true
                });
                
                // Store reference to control for later stopping
                activeSounds[name] = control;
                return control;
            }
            return null;
        })
        .catch(error => {
            console.error(`Error playing ambient sound ${name}:`, error);
            return null;
        });
}

/**
 * Stop a currently playing ambient sound
 * @param {string} name - Name of ambient sound to stop
 */
function stopAmbientSound(name) {
    if (activeSounds[name]) {
        activeSounds[name].stop();
        delete activeSounds[name];
    }
}

/**
 * Stop all currently playing sounds
 */
function stopAllSounds() {
    // Stop all ambient sounds
    Object.keys(activeSounds).forEach(name => {
        activeSounds[name].stop();
    });
    
    // Clear the active sounds list
    Object.keys(activeSounds).forEach(key => {
        delete activeSounds[key];
    });
    
    // If we have an audio context, close and reopen it to stop all sounds
    if (audioContext) {
        audioContext.close().then(() => {
            audioContext = new AudioContext();
        });
    }
}

/**
 * Set volume for a specific category of sounds
 * @param {string} type - Volume type (master, ui, notification, ambient)
 * @param {number} value - Volume value (0-1)
 */
function setVolume(type, value) {
    // Ensure value is in valid range
    value = Math.max(0, Math.min(1, value));
    
    // Update volume setting
    volumeSettings[type] = value;
    
    // Apply to active sounds
    if (type === 'master') {
        // Update all active sound volumes
        Object.values(activeSounds).forEach(control => {
            control.setVolume(control.gainNode.gain.value / volumeSettings.master * value);
        });
    } else if (type === 'ambient') {
        // Update only ambient sounds
        Object.keys(activeSounds).forEach(name => {
            if (name.startsWith('ambient_')) {
                activeSounds[name].setVolume(value * volumeSettings.master);
            }
        });
    }
    
    // Save to localStorage
    localStorage.setItem('volumeSettings', JSON.stringify(volumeSettings));
}

/**
 * Create audio indicators for system status
 * @param {string} status - Status type (success, error, warning, info)
 */
function playStatusSound(status) {
    switch (status) {
        case 'success':
            // High short beep
            createBeep(880, 0.2, { type: 'sine' });
            break;
        case 'error':
            // Low double beep
            createBeep(220, 0.15, { type: 'square' })
                .then(() => createBeep(220, 0.15, { delay: 0.1, type: 'square' }));
            break;
        case 'warning':
            // Medium descending beep
            createBeep(440, 0.2, { type: 'triangle' })
                .then(() => createBeep(330, 0.2, { delay: 0.1, type: 'triangle' }));
            break;
        case 'info':
            // Short medium beep
            createBeep(660, 0.1, { type: 'sine' });
            break;
    }
}

/**
 * Create a beep sound using the Web Audio API
 * @param {number} frequency - Frequency in Hz
 * @param {number} duration - Duration in seconds
 * @param {Object} options - Additional options
 * @returns {Promise} - Promise that resolves when the beep completes
 */
function createBeep(frequency, duration, options = {}) {
    return new Promise(resolve => {
        if (!audioEnabled || !audioContext) {
            resolve();
            return;
        }
        
        // Default options
        const defaultOptions = {
            type: 'sine', // sine, square, triangle, sawtooth
            volume: volumeSettings.notification * volumeSettings.master,
            delay: 0,
            fadeIn: 0.01,
            fadeOut: 0.05
        };
        
        // Merge options
        const beepOptions = { ...defaultOptions, ...options };
        
        // Create oscillator
        const oscillator = audioContext.createOscillator();
        oscillator.type = beepOptions.type;
        oscillator.frequency.value = frequency;
        
        // Create gain node for volume and fades
        const gainNode = audioContext.createGain();
        gainNode.gain.value = 0;
        
        // Connect nodes
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Calculate start time with delay
        const startTime = audioContext.currentTime + beepOptions.delay;
        const fadeInEnd = startTime + beepOptions.fadeIn;
        const fadeOutStart = startTime + duration - beepOptions.fadeOut;
        const endTime = startTime + duration;
        
        // Schedule volume changes
        gainNode.gain.setValueAtTime(0, startTime);
        gainNode.gain.linearRampToValueAtTime(beepOptions.volume, fadeInEnd);
        gainNode.gain.setValueAtTime(beepOptions.volume, fadeOutStart);
        gainNode.gain.linearRampToValueAtTime(0, endTime);
        
        // Start and stop the oscillator
        oscillator.start(startTime);
        oscillator.stop(endTime);
        
        // Resolve promise when beep completes
        setTimeout(() => {
            resolve();
        }, (beepOptions.delay + duration) * 1000);
    });
}

/**
 * Add audio feedback to interactive elements
 */
function addAudioFeedback() {
    // Add click sounds to buttons
    const buttons = document.querySelectorAll('button, .btn, [role="button"]');
    buttons.forEach(button => {
        button.addEventListener('click', playClickSound);
    });
    
    // Add subtle sounds to form controls
    const formControls = document.querySelectorAll('input, select, textarea');
    formControls.forEach(control => {
        control.addEventListener('focus', () => {
            playSound('focus', { volume: volumeSettings.ui * 0.5 });
        });
    });
    
    // Add notification sounds to alerts
    const notifications = document.querySelectorAll('.alert, .toast');
    notifications.forEach(notification => {
        // Play sound when notification is added to the DOM
        playNotificationSound();
    });
}

/**
 * Synchronize audio with animations
 * @param {string} animationName - Name of animation to sync with
 * @param {Object} options - Sync options
 */
function syncAudioWithAnimation(animationName, options = {}) {
    // Implementation depends on your animation system
    // This is a placeholder showing the pattern
    switch (animationName) {
        case 'success-animation':
            playStatusSound('success');
            break;
        case 'error-animation':
            playStatusSound('error');
            break;
        case 'loading-start':
            playSound('loading', { loop: true });
            break;
        case 'loading-end':
            // Stop the loading sound
            stopAmbientSound('loading');
            playStatusSound('success');
            break;
    }
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        playSound,
        playClickSound,
        playNotificationSound,
        playAmbientSound,
        stopAmbientSound,
        setVolume,
        playStatusSound,
        syncAudioWithAnimation
    };
} else {
    // Add to window object in browser environment
    window.audioEffects = {
        playSound,
        playClickSound,
        playNotificationSound,
        playAmbientSound,
        stopAmbientSound,
        setVolume,
        playStatusSound,
        syncAudioWithAnimation,
        addAudioFeedback
    };
}