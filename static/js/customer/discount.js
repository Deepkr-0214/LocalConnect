// Enhanced Cart with Discount Functionality
let vendorOffers = [];
let appliedDiscount = null;

// Load vendor offers when page loads
function loadVendorOffers() {
    fetch(`/vendor/${vendorId}/offers`)
        .then(res => res.json())
        .then(offers => {
            vendorOffers = offers;
            console.log('Loaded vendor offers:', vendorOffers);
        })
        .catch(err => {
            console.log('No offers available for this vendor');
            vendorOffers = [];
        });
}

// Calculate best applicable discount
function calculateDiscount(subtotal) {
    let bestDiscount = 0;
    let bestOffer = null;
    
    if (vendorOffers && vendorOffers.length > 0) {
        for (let offer of vendorOffers) {
            if (subtotal >= offer.min_order) {
                const discount = offer.discount_type === 'percentage' 
                    ? Math.min((subtotal * offer.discount_value / 100), offer.max_discount || Infinity)
                    : offer.discount_value;
                
                if (discount > bestDiscount) {
                    bestDiscount = discount;
                    bestOffer = offer;
                }
            }
        }
    }
    
    return { discount: bestDiscount, offer: bestOffer };
}

// Enhanced openCart function with discount
function openCartWithDiscount() {
    const cartItems = menuItems.filter(i => i.qty > 0);
    const subtotal = cartItems.reduce((s, i) => s + (i.qty * i.price), 0);
    const cartItemsList = document.getElementById('cart-items-list');
    const modalTotal = document.getElementById('modal-total');

    if (cartItems.length === 0) {
        cartItemsList.innerHTML = `
            <div class="empty-cart" style="text-align:center;padding:60px 20px;">
                <i class="fa-solid fa-shopping-cart" style="font-size:4rem;color:#ddd;margin-bottom:20px;"></i>
                <h3 style="color:#7f8c8d;margin-bottom:10px;">Your cart is empty</h3>
                <p style="color:#bdc3c7;">Add some delicious items to get started!</p>
            </div>
        `;
        modalTotal.style.display = 'none';
    } else {
        const { discount, offer } = calculateDiscount(subtotal);
        const discountedSubtotal = subtotal - discount;
        const cashRestricted = discountedSubtotal > 200;
        
        const paymentMessage = cashRestricted ? 
            '<div style="background:#fff3cd;border:1px solid #ffeaa7;color:#856404;padding:12px;border-radius:8px;margin:15px 0;font-size:14px;"><i class="fa-solid fa-info-circle"></i> <strong>Note:</strong> Orders above ₹200 require online payment only. Cash payment is available for orders ₹200 and below.</div>' : '';
        
        const discountSection = offer ? `
            <div class="discount-section">
                <div class="discount-header">
                    <div class="discount-title">🎉 ${offer.title}</div>
                    <div class="discount-buttons">
                        <button class="discount-toggle" onclick="toggleDiscount()" id="discount-btn">
                            ${appliedDiscount ? 'Remove' : 'Apply'}
                        </button>
                        <button class="no-discount-btn" onclick="skipDiscount()" id="skip-btn">
                            No Thanks
                        </button>
                    </div>
                </div>
                <div class="discount-details">
                    ${offer.description}<br>
                    <strong>Save ₹${discount.toFixed(0)} on this order!</strong>
                </div>
            </div>
        ` : '';
        
        cartItemsList.innerHTML = cartItems.map(item => `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <p>₹${item.price} each</p>
                </div>
                <div class="cart-item-controls">
                    <div style="display:flex;align-items:center;background:var(--primary-green);color:white;border-radius:8px;padding:4px 8px;gap:10px;">
                        <button onclick="updateQty(${item.id}, -1)" style="background:none;border:none;color:white;cursor:pointer;font-size:16px;">-</button>
                        <span style="font-weight:700;min-width:20px;text-align:center;">${item.qty}</span>
                        <button onclick="updateQty(${item.id}, 1)" style="background:none;border:none;color:white;cursor:pointer;font-size:16px;">+</button>
                    </div>
                    <span style="font-weight:600;color:var(--primary-green);">₹${item.qty * item.price}</span>
                </div>
            </div>
        `).join('') + discountSection + paymentMessage;
        
        const finalTotal = appliedDiscount ? discountedSubtotal : subtotal;
        modalTotal.innerHTML = `Total: ₹${finalTotal}`;
        modalTotal.style.display = 'block';
    }
    document.getElementById('cart-modal').classList.add('active');
}

// Toggle discount application
function toggleDiscount() {
    const cartItems = menuItems.filter(i => i.qty > 0);
    const subtotal = cartItems.reduce((s, i) => s + (i.qty * i.price), 0);
    const { discount, offer } = calculateDiscount(subtotal);
    
    if (appliedDiscount) {
        appliedDiscount = null;
        document.getElementById('discount-btn').textContent = 'Apply';
        document.getElementById('skip-btn').style.display = 'inline-block';
    } else {
        appliedDiscount = { discount, offer };
        document.getElementById('discount-btn').textContent = 'Remove';
        document.getElementById('skip-btn').style.display = 'none';
    }
    
    // Update total display
    const finalTotal = appliedDiscount ? subtotal - appliedDiscount.discount : subtotal;
    document.getElementById('modal-total').innerHTML = `Total: ₹${finalTotal}`;
}

// Skip discount - customer doesn't want any discount
function skipDiscount() {
    appliedDiscount = null;
    document.querySelector('.discount-section').style.display = 'none';
    
    // Update total display
    const cartItems = menuItems.filter(i => i.qty > 0);
    const subtotal = cartItems.reduce((s, i) => s + (i.qty * i.price), 0);
    document.getElementById('modal-total').innerHTML = `Total: ₹${subtotal}`;
}

// Enhanced proceedToBuy with discount
function proceedToBuyWithDiscount() {
    const cartItems = menuItems.filter(i => i.qty > 0);
    if (cartItems.length === 0) { 
        alert('Your cart is empty!'); 
        return; 
    }
    
    const subtotal = cartItems.reduce((s, i) => s + (i.qty * i.price), 0);
    const finalTotal = appliedDiscount ? subtotal - appliedDiscount.discount : subtotal;
    
    showDeliverySelectionWithDiscount(subtotal, finalTotal);
}

// Enhanced delivery selection with discount
function showDeliverySelectionWithDiscount(subtotal, total) {
    document.getElementById('cart-items-list').innerHTML = `
        <div class="order-step">
            <h3>Choose Delivery Option</h3>
            <div class="delivery-options">
                <div class="delivery-option" onclick="selectDeliveryWithDiscount('takeaway', ${subtotal}, ${total})">
                    <div class="option-icon">🏪</div>
                    <div class="option-details">
                        <h4>Takeaway</h4>
                        <p>Ready in 15-20 minutes</p>
                        <span class="price">Free</span>
                    </div>
                </div>
                <div class="delivery-option" onclick="selectDeliveryWithDiscount('delivery', ${subtotal}, ${total})">
                    <div class="option-icon">🚚</div>
                    <div class="option-details">
                        <h4>Home Delivery</h4>
                        <p>Delivered in 25-30 minutes</p>
                        <span class="price">₹30</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('modal-total').innerHTML = `Subtotal: ₹${total}`;
}

// Enhanced delivery selection with discount
function selectDeliveryWithDiscount(type, subtotal, discountedSubtotal) {
    if (type === 'delivery') {
        showLocationChoiceWithDiscount(subtotal, discountedSubtotal);
    } else {
        window.selectedLocationType = null;
        proceedWithDeliveryTypeWithDiscount(type, subtotal, discountedSubtotal);
    }
}

// Enhanced location choice with discount
function showLocationChoiceWithDiscount(subtotal, discountedSubtotal) {
    document.getElementById('cart-items-list').innerHTML = `
        <div class="order-step">
            <h3>Choose Delivery Location</h3>
            <div class="delivery-options">
                <div class="delivery-option" onclick="selectLocationWithDiscount('home', ${subtotal}, ${discountedSubtotal})">
                    <div class="option-icon">🏠</div>
                    <div class="option-details">
                        <h4>Home Location</h4>
                        <p>Deliver to your saved home address</p>
                    </div>
                </div>
                <div class="delivery-option" onclick="selectLocationWithDiscount('current', ${subtotal}, ${discountedSubtotal})">
                    <div class="option-icon">📍</div>
                    <div class="option-details">
                        <h4>Current Location</h4>
                        <p>Deliver to your current GPS location</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('modal-total').innerHTML = `Subtotal: ₹${discountedSubtotal}`;
}

// Enhanced location selection with discount
function selectLocationWithDiscount(locationType, subtotal, discountedSubtotal) {
    window.selectedLocationType = locationType;
    proceedWithDeliveryTypeWithDiscount('delivery', subtotal, discountedSubtotal);
}

// Enhanced delivery type processing with discount
function proceedWithDeliveryTypeWithDiscount(type, originalSubtotal, discountedSubtotal) {
    const deliveryFee = type === 'delivery' ? 30 : 0;
    const finalTotal = discountedSubtotal + deliveryFee;
    const discount = appliedDiscount ? appliedDiscount.discount : 0;
    
    const cashRestricted = finalTotal > 200;
    const cashMessage = cashRestricted ? 
        '<div style="background:#fff3cd;border:1px solid #ffeaa7;color:#856404;padding:12px;border-radius:8px;margin:15px 0;font-size:14px;"><i class="fa-solid fa-info-circle"></i> <strong>Note:</strong> Orders above ₹200 require online payment only. Cash payment is available for orders ₹200 and below.</div>' : '';
    
    const discountHtml = discount > 0 ? 
        `<div class="summary-row discount-row">
            <span>Discount (${appliedDiscount.offer.title}):</span>
            <span>-₹${discount.toFixed(0)}</span>
        </div>` : '';
    
    document.getElementById('cart-items-list').innerHTML = `
        <div class="order-step">
            <h3>Payment Method</h3>
            <div class="order-summary">
                <div class="summary-row"><span>Subtotal:</span><span>₹${originalSubtotal}</span></div>
                ${discountHtml}
                <div class="summary-row"><span>${type === 'delivery' ? 'Delivery Fee:' : 'Takeaway:'}</span><span>${deliveryFee > 0 ? '₹' + deliveryFee : 'Free'}</span></div>
                <div class="summary-row total-row"><span>Total:</span><span>₹${finalTotal.toFixed(0)}</span></div>
            </div>
            ${cashMessage}
            <div style="margin:20px 0;">
                <label style="display:block;margin-bottom:8px;font-weight:600;color:#2c3e50;">Special Instructions (Optional):</label>
                <textarea id="customerSuggestion" placeholder="Any special requests or instructions for the vendor..." style="width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;min-height:80px;resize:vertical;font-family:inherit;"></textarea>
            </div>
            <div class="payment-options">
                <div class="payment-option" onclick="if(!window.processingPayment) processPaymentWithDiscount('online', '${type}', ${finalTotal}, ${discount}, '${appliedDiscount ? appliedDiscount.offer.title : ''}')">
                    <div class="option-icon">💳</div>
                    <div class="option-details">
                        <h4>Online Payment</h4>
                        <p>Pay now with card/UPI</p>
                    </div>
                </div>
                <div class="payment-option ${cashRestricted ? 'disabled' : ''}" ${cashRestricted ? '' : `onclick="if(!window.processingPayment) processPaymentWithDiscount('cash', '${type}', ${finalTotal}, ${discount}, '${appliedDiscount ? appliedDiscount.offer.title : ''}')")`}>
                    <div class="option-icon">💵</div>
                    <div class="option-details">
                        <h4>Cash on ${type === 'delivery' ? 'Delivery' : 'Pickup'}</h4>
                        <p>${cashRestricted ? 'Not available for orders above ₹200' : 'Pay when you receive'}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('modal-total').style.display = 'none';
}

// Enhanced payment processing with discount
function processPaymentWithDiscount(paymentType, deliveryType, total, discount = 0, offerTitle = '') {
    // Use the existing processPayment function but with discount parameters
    processPayment(paymentType, deliveryType, total, discount, offerTitle);
}

// Initialize discount functionality when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadVendorOffers();
    
    // Override the original openCart function
    window.openCart = openCartWithDiscount;
    window.proceedToBuy = proceedToBuyWithDiscount;
});