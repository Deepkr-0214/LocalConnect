// Discount Box JavaScript
let currentOfferIndex = 0;
let vendorOffers = [];
let rotationInterval;
let isDragging = false;
let dragOffset = { x: 0, y: 0 };

// Make discount box draggable
function makeDraggable() {
    const discountBox = document.getElementById('discountBox');
    
    discountBox.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
    
    // Touch events for mobile
    discountBox.addEventListener('touchstart', startDrag);
    document.addEventListener('touchmove', drag);
    document.addEventListener('touchend', stopDrag);
}

function startDrag(e) {
    e.preventDefault();
    isDragging = true;
    
    const discountBox = document.getElementById('discountBox');
    const rect = discountBox.getBoundingClientRect();
    
    const clientX = e.clientX || e.touches[0].clientX;
    const clientY = e.clientY || e.touches[0].clientY;
    
    dragOffset.x = clientX - rect.left;
    dragOffset.y = clientY - rect.top;
    
    discountBox.style.transition = 'none';
}

function drag(e) {
    if (!isDragging) return;
    
    e.preventDefault();
    const discountBox = document.getElementById('discountBox');
    
    const clientX = e.clientX || e.touches[0].clientX;
    const clientY = e.clientY || e.touches[0].clientY;
    
    let newX = clientX - dragOffset.x;
    let newY = clientY - dragOffset.y;
    
    // Keep within viewport bounds
    const maxX = window.innerWidth - discountBox.offsetWidth;
    const maxY = window.innerHeight - discountBox.offsetHeight;
    
    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));
    
    discountBox.style.left = newX + 'px';
    discountBox.style.top = newY + 'px';
    discountBox.style.bottom = 'auto';
}

function stopDrag() {
    if (isDragging) {
        isDragging = false;
        const discountBox = document.getElementById('discountBox');
        discountBox.style.transition = 'all 0.3s ease';
    }
}

// Load offers for current vendor
function loadVendorOffers(vendorId) {
    console.log('Loading offers for vendor:', vendorId);
    fetch(`/vendor/${vendorId}/offers`)
        .then(response => {
            console.log('Offers API response status:', response.status);
            return response.json();
        })
        .then(offers => {
            console.log('Loaded offers:', offers);
            vendorOffers = offers;
            if (offers.length > 0) {
                showDiscountBox();
                if (offers.length > 1) {
                    startOfferRotation();
                }
            } else {
                console.log('No offers found, showing default discount box');
                // Show default discount box even without offers
                showDefaultDiscountBox();
            }
        })
        .catch(error => {
            console.error('Error loading offers:', error);
            // Show default discount box on error
            showDefaultDiscountBox();
        });
}

// Show default discount box when no offers
function showDefaultDiscountBox() {
    const discountBox = document.getElementById('discountBox');
    
    document.getElementById('discountTitle').textContent = '🎉 OFFERS';
    document.getElementById('discountDesc').textContent = 'Check back soon!';
    
    discountBox.style.display = 'block';
    
    // Add click to open modal
    discountBox.onclick = openOffersModal;
    
    // Make draggable after showing
    makeDraggable();
}

// Show discount box
function showDiscountBox() {
    if (vendorOffers.length === 0) return;
    
    const discountBox = document.getElementById('discountBox');
    const offer = vendorOffers[currentOfferIndex];
    
    document.getElementById('discountTitle').textContent = 
        offer.discount_type === 'percentage' ? `${offer.discount_value}% OFF` : `₹${offer.discount_value} OFF`;
    
    document.getElementById('discountDesc').textContent = 
        offer.min_order > 0 ? `on orders above ₹${offer.min_order}` : offer.description;
    
    discountBox.style.display = 'block';
    
    // Add click to open modal
    discountBox.onclick = openOffersModal;
    
    // Make draggable after showing
    makeDraggable();
}

// Start offer rotation
function startOfferRotation() {
    rotationInterval = setInterval(() => {
        currentOfferIndex = (currentOfferIndex + 1) % vendorOffers.length;
        showDiscountBox();
    }, 5000);
}

// Close discount box
function closeDiscountBox() {
    document.getElementById('discountBox').style.display = 'none';
    if (rotationInterval) {
        clearInterval(rotationInterval);
    }
    // Remove permanent storage - box will show again on next visit
}

// Open offers modal
function openOffersModal() {
    const modal = document.getElementById('offersModal');
    const container = document.getElementById('offersContainer');
    
    container.innerHTML = '';
    
    if (vendorOffers.length === 0) {
        container.innerHTML = '<p>No active offers available.</p>';
    } else {
        vendorOffers.forEach(offer => {
            const offerCard = document.createElement('div');
            offerCard.className = 'offer-card';
            
            const imageHtml = offer.image ? 
                `<img src="${offer.image}" alt="Offer" onerror="this.style.display='none'">` : '';
            
            offerCard.innerHTML = `
                ${imageHtml}
                <div class="offer-title">${offer.title}</div>
                <div class="offer-description">${offer.description}</div>
                <div class="offer-details">
                    <span><strong>Discount:</strong> ${offer.discount_type === 'percentage' ? offer.discount_value + '%' : '₹' + offer.discount_value} OFF</span><br>
                    <span><strong>Min Order:</strong> ₹${offer.min_order}</span><br>
                    <span><strong>Valid till:</strong> ${new Date(offer.valid_to).toLocaleDateString()}</span>
                </div>
            `;
            container.appendChild(offerCard);
        });
    }
    
    modal.style.display = 'flex';
}

// Close offers modal
function closeOffersModal() {
    document.getElementById('offersModal').style.display = 'none';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Always show discount box on page load (no permanent close)
    const vendorId = window.currentVendorId || document.querySelector('[data-vendor-id]')?.dataset.vendorId;
    console.log('Discount box initializing for vendor ID:', vendorId);
    if (vendorId) {
        loadVendorOffers(vendorId);
    } else {
        console.error('No vendor ID found for discount box');
    }
});

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('offersModal');
    if (event.target === modal) {
        closeOffersModal();
    }
});