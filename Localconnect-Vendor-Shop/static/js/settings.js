// Settings Page JavaScript

// Shop name update function
function updateHeaderProfileName() {
    const shopNameInput = document.getElementById('shop_name');
    if (shopNameInput) {
        const shopName = shopNameInput.value.trim();
        const headerProfileName = document.querySelector('.profile-name');
        const dropdownProfileName = document.querySelector('.profile-details .profile-name');
        
        if (shopName && headerProfileName) {
            const displayName = shopName.length > 15 ? shopName.substring(0, 15) + '...' : shopName;
            headerProfileName.textContent = displayName;
        }
        
        if (shopName && dropdownProfileName) {
            dropdownProfileName.textContent = shopName;
        }
        
        // Save to localStorage
        localStorage.setItem('shopName', shopName);
    }
}

// Shop email update function
function updateHeaderProfileEmail() {
    const shopEmailInput = document.getElementById('shop_email');
    if (shopEmailInput) {
        const shopEmail = shopEmailInput.value.trim();
        const dropdownProfileEmail = document.querySelector('.profile-details .profile-email');
        
        if (shopEmail && dropdownProfileEmail) {
            dropdownProfileEmail.textContent = shopEmail;
        }
        
        // Save to localStorage
        localStorage.setItem('shopEmail', shopEmail);
    }
}

// Save all form data
function saveFormData() {
    const inputs = ['shop_name', 'shop_email', 'phone', 'address', 'name', 'email'];
    inputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            localStorage.setItem(id, input.value);
        }
    });
}

// Load all form data
function loadFormData() {
    const inputs = ['shop_name', 'shop_email', 'phone', 'address', 'name', 'email'];
    inputs.forEach(id => {
        const input = document.getElementById(id);
        const savedValue = localStorage.getItem(id);
        if (input && savedValue) {
            input.value = savedValue;
        }
    });
}

// Load saved shop name and email
function loadGlobalShopName() {
    const savedShopName = localStorage.getItem('shopName');
    if (savedShopName) {
        const headerProfileName = document.querySelector('.profile-name');
        const dropdownProfileName = document.querySelector('.profile-details .profile-name');
        
        if (headerProfileName) {
            const displayName = savedShopName.length > 15 ? savedShopName.substring(0, 15) + '...' : savedShopName;
            headerProfileName.textContent = displayName;
        }
        
        if (dropdownProfileName) {
            dropdownProfileName.textContent = savedShopName;
        }
    }
}

function loadGlobalShopEmail() {
    const savedShopEmail = localStorage.getItem('shopEmail');
    if (savedShopEmail) {
        const dropdownProfileEmail = document.querySelector('.profile-details .profile-email');
        if (dropdownProfileEmail) {
            dropdownProfileEmail.textContent = savedShopEmail;
        }
    }
}

// Shop Image Functions
function showShopImageOptions() {
    document.getElementById('shopImageModal').style.display = 'block';
}

function closeShopImageModal() {
    document.getElementById('shopImageModal').style.display = 'none';
    document.getElementById('shopEmojiPicker').style.display = 'none';
}

function uploadShopImage() {
    document.getElementById('shopImageUpload').click();
}

function showShopEmojiPicker() {
    document.getElementById('shopEmojiPicker').style.display = 'block';
}

function previewShopImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const shopImage = document.getElementById('shopImage');
            shopImage.innerHTML = `<img src="${e.target.result}" alt="Shop Image">`;
            shopImage.classList.remove('emoji');
            
            // Save to localStorage for persistence
            localStorage.setItem('shopImage', e.target.result);
            localStorage.setItem('shopImageType', 'upload');
            
            // Update global shop images
            if (typeof loadGlobalShopImage === 'function') {
                loadGlobalShopImage();
            }
            
            closeShopImageModal();
            showToast('Shop image updated successfully!');
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function selectShopEmoji(emoji) {
    const shopImage = document.getElementById('shopImage');
    shopImage.innerHTML = emoji;
    shopImage.classList.add('emoji');
    
    // Save to localStorage for persistence
    localStorage.setItem('shopImage', emoji);
    localStorage.setItem('shopImageType', 'emoji');
    
    // Update global shop images
    if (typeof loadGlobalShopImage === 'function') {
        loadGlobalShopImage();
    }
    
    closeShopImageModal();
    showToast('Shop avatar updated successfully!');
}

// Load saved shop image on page load
function loadShopImage() {
    const savedImage = localStorage.getItem('shopImage');
    const imageType = localStorage.getItem('shopImageType');
    
    if (savedImage && imageType) {
        const shopImage = document.getElementById('shopImage');
        if (imageType === 'emoji') {
            shopImage.innerHTML = savedImage;
            shopImage.classList.add('emoji');
        } else if (imageType === 'upload') {
            shopImage.innerHTML = `<img src="${savedImage}" alt="Shop Image">`;
            shopImage.classList.remove('emoji');
        }
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('shopImageModal');
    if (event.target === modal) {
        closeShopImageModal();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Load saved shop image, name, and form data
    loadShopImage();
    loadGlobalShopName();
    loadFormData();
    
    // Add event listeners to form inputs
    const shopNameInput = document.getElementById('shop_name');
    const shopEmailInput = document.getElementById('shop_email');
    
    if (shopNameInput) {
        shopNameInput.addEventListener('input', () => {
            updateHeaderProfileName();
            saveFormData();
        });
    }
    
    if (shopEmailInput) {
        shopEmailInput.addEventListener('input', () => {
            updateHeaderProfileEmail();
            saveFormData();
        });
    }
    
    // Add event listeners to all form inputs for persistence
    const allInputs = document.querySelectorAll('input, textarea');
    allInputs.forEach(input => {
        input.addEventListener('input', saveFormData);
    });
    
    // Show success message if form was submitted
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'true') {
        showSuccessMessage();
    }
    
    // Initialize preference toggles
    initializePreferences();
});

// Show success message
function showSuccessMessage() {
    const message = document.getElementById('successMessage');
    message.style.display = 'flex';
    
    setTimeout(() => {
        message.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => {
            message.style.display = 'none';
            message.style.animation = '';
        }, 300);
    }, 3000);
}

// Initialize preferences
function initializePreferences() {
    // Load saved preferences from localStorage
    const preferences = {
        email_notifications: localStorage.getItem('email_notifications') !== 'false',
        sound_alerts: localStorage.getItem('sound_alerts') !== 'false'
    };
    
    // Set checkbox states
    Object.keys(preferences).forEach(key => {
        const checkbox = document.getElementById(key);
        if (checkbox) {
            checkbox.checked = preferences[key];
            checkbox.addEventListener('change', () => {
                localStorage.setItem(key, checkbox.checked);
                showPreferenceUpdate(key, checkbox.checked);
            });
        }
    });
}

// Show preference update feedback
function showPreferenceUpdate(preference, enabled) {
    const messages = {
        email_notifications: enabled ? 'Email notifications enabled' : 'Email notifications disabled',
        sound_alerts: enabled ? 'Sound alerts enabled' : 'Sound alerts disabled'
    };
    
    showToast(messages[preference]);
}

// Show toast notification
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `
        <i class="fa-solid fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    // Add toast styles
    Object.assign(toast.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        background: '#10b981',
        color: 'white',
        padding: '12px 20px',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontWeight: '600',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        zIndex: '1000',
        transform: 'translateY(100px)',
        transition: 'transform 0.3s ease'
    });
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.transform = 'translateY(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.transform = 'translateY(100px)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Change password function
function changePassword() {
    const newPassword = prompt('Enter new password:');
    if (newPassword && newPassword.length >= 6) {
        // Simulate password change
        showToast('Password changed successfully');
    } else if (newPassword) {
        alert('Password must be at least 6 characters long');
    }
}

// Confirm logout
function confirmLogout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}

// Confirm account deactivation
function confirmDeactivate() {
    const confirmation = prompt('Type "DEACTIVATE" to confirm account deactivation:');
    if (confirmation === 'DEACTIVATE') {
        alert('Account deactivation feature will be available soon');
    } else if (confirmation) {
        alert('Confirmation text does not match');
    }
}

// Add CSS for toast animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);