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

function toggleShopStatus(checkbox) {
    const isOpen = checkbox.checked;
    const statusBadge = document.querySelector('.status-badge');
    const statusIndicator = document.querySelector('.status-indicator');
    const headerToggle = document.getElementById('header_shop_status');

    // Update status badge in settings
    if (statusBadge) {
        statusBadge.className = `status-badge ${isOpen ? 'open' : 'closed'}`;
        statusBadge.innerHTML = `<i class="fa-solid fa-${isOpen ? 'check-circle' : 'times-circle'}"></i><span>${isOpen ? 'Open for Orders' : 'Closed'}</span>`;
    }

    // Update header status indicator
    if (statusIndicator) {
        statusIndicator.className = `status-indicator ${isOpen ? 'open' : 'closed'}`;
        const statusText = statusIndicator.querySelector('.status-text');
        if (statusText) statusText.textContent = isOpen ? 'Open' : 'Closed';
    }

    // Sync header toggle
    if (headerToggle) headerToggle.checked = isOpen;

    // Send to server
    fetch('/toggle_shop_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_open: isOpen })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(isOpen ? 'Shop is now Open' : 'Shop is now Closed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            checkbox.checked = !isOpen;
        });
}

function previewShopImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const base64Image = e.target.result;
            const shopImage = document.getElementById('shopImage');
            const imgTag = `<img src="${base64Image}" alt="Shop Image" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`;
            shopImage.innerHTML = imgTag;
            shopImage.classList.remove('emoji');

            // Send to server
            fetch('/vendor/update_shop_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ shop_image: base64Image })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        // Update navbar images
                        const headerImg = document.getElementById('headerShopImage');
                        const dropdownImg = document.getElementById('dropdownShopImage');
                        if (headerImg) headerImg.innerHTML = imgTag;
                        if (dropdownImg) dropdownImg.innerHTML = imgTag;
                    }
                });

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

    // Send to server
    fetch('/vendor/update_shop_image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shop_image: emoji })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Update all navbar images
                const headerImg = document.getElementById('headerShopImage');
                const dropdownImg = document.getElementById('dropdownShopImage');
                if (headerImg) headerImg.innerHTML = emoji;
                if (dropdownImg) dropdownImg.innerHTML = emoji;
            }
        });

    closeShopImageModal();
    showToast('Shop avatar updated successfully!');
}

function updateNavbarName() {
    const shopName = document.getElementById('shop_name').value.trim();
    if (shopName) {
        const headerName = document.querySelector('.profile-pill .profile-name');
        const dropdownName = document.querySelector('.profile-details .profile-name');

        if (headerName) {
            headerName.textContent = shopName.length > 15 ? shopName.substring(0, 15) + '...' : shopName;
        }
        if (dropdownName) {
            dropdownName.textContent = shopName;
        }
    }
}

function handleFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    // Parse shop location coordinates if provided
    const shopLocation = document.getElementById('shop_location').value;
    if (shopLocation && shopLocation.includes(',')) {
        const [lat, lng] = shopLocation.split(',').map(coord => parseFloat(coord.trim()));
        if (!isNaN(lat) && !isNaN(lng)) {
            formData.append('latitude', lat);
            formData.append('longitude', lng);
        }
    }

    fetch(form.action, {
        method: 'POST',
        body: formData
    })
        .then(res => {
            if (res.ok) {
                showToast('Settings updated successfully!');
                updateNavbarName();
            }
            return res;
        })
        .then(res => res.text())
        .then(() => {
            // Keep user on page
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Failed to update settings');
        });

    return false;
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

const subCategories = {
    'Food & Restaurant': ['Street Food', 'Food Shop', 'Restaurant', 'Dhaba'],
    'Garage': ['2-Wheeler', '3-Wheeler', '4-Wheeler'],
    'Electronics': ['Mobiles', 'Home Appliances', 'Kitchen Appliances'],
    'Fashion': ['Ladies', 'Gents', 'Boy', 'Girl'],
    'Grocery': ['Vegetables', 'Dairy & Eggs', 'General Store', 'Fruits'],
    'Pharmacy': ['Ayurvedic Medicine', 'Chemist & Drug Medicine', 'Baby Medicine']
};

function updateSubCategories() {
    const categorySelect = document.getElementById('business_category');
    const subCategorySelect = document.getElementById('business_sub_category');
    const selectedCategory = categorySelect.value;
    const currentSub = "{{ vendor_profile.business_sub_category if vendor_profile else '' }}";

    // Clear existing options
    subCategorySelect.innerHTML = '<option value="">Select Sub-Category</option>';

    if (selectedCategory && subCategories[selectedCategory]) {
        subCategories[selectedCategory].forEach(subCat => {
            const option = document.createElement('option');
            option.value = subCat;
            option.textContent = subCat;
            if (subCat === currentSub) {
                option.selected = true;
            }
            subCategorySelect.appendChild(option);
        });
    }
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('shopImageModal');
    if (event.target === modal) {
        closeShopImageModal();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Load saved shop image only
    loadShopImage();

    // Initialize subcategories
    updateSubCategories();

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

// Delete vendor account permanently
function deleteVendorAccount() {
    if (!confirm('Are you sure you want to permanently delete your vendor account? This action cannot be undone!')) {
        return;
    }

    if (!confirm('This will delete all your menu items, orders history, and business data. Type "DELETE" to confirm:')) {
        return;
    }

    const userInput = prompt('Type "DELETE" to confirm account deletion:');
    if (userInput !== 'DELETE') {
        alert('Confirmation failed. Account deletion cancelled.');
        return;
    }

    fetch('/vendor/delete-account', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Vendor account deleted successfully. You will be redirected to the home page.');
                localStorage.clear();
                sessionStorage.clear();
                window.location.href = data.redirect;
            } else {
                alert('Error deleting account: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Network error. Please try again.');
        });
}

// Get vendor current location
function getVendorCurrentLocation() {
    const locationField = document.getElementById('shop_location');
    if (!locationField) {
        alert('Location field not found');
        return;
    }

    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
    }

    locationField.value = 'Getting location...';
    showToast('Getting your current location...');

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            locationField.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            showToast('Location coordinates updated successfully!');
        },
        (error) => {
            locationField.value = '';
            let errorMessage = 'Unable to get location';
            if (error.code === 1) errorMessage = 'Location permission denied';
            else if (error.code === 2) errorMessage = 'Location unavailable';
            else if (error.code === 3) errorMessage = 'Location request timeout';

            alert(errorMessage);
            showToast(errorMessage);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000
        }
    );
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