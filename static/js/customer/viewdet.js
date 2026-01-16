/**
 * Vendor Details Page - extending LocalConnect Base
 */
class VendorDetailsPage extends LocalConnectBase {
    constructor() {
        super();
        this.menuItems = [
            { id: 1, name: "Pani Puri", price: 60, qty: 0, desc: "Crispy tangy puris filled with flavored water.", img: "https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=400" },
            { id: 2, name: "Aloo Tikki", price: 80, qty: 0, desc: "Spiced potato patties with tamarind chutney.", img: "https://images.unsplash.com/photo-1601050690597-df056fbec7ad?w=400" },
            { id: 3, name: "Bhel Puri", price: 70, qty: 0, desc: "Crunchy puffed rice vegetable mix.", img: "https://images.unsplash.com/photo-1517244683847-7456b63c5969?w=400" },
            { id: 4, name: "Sev Puri", price: 90, qty: 0, desc: "Papdi topped with potatoes and sev.", img: "https://images.unsplash.com/photo-1606491956391-70868b5d0f47?w=400" }
        ];
        
        this.reviewsData = [
            { name: "Anjali Sharma", rating: 5, date: "2 days ago", text: "Best Pani Puri in the city! Perfectly spicy." },
            { name: "Rahul Verma", rating: 4, date: "1 week ago", text: "Great taste, but usually crowded." }
        ];
        
        this.menuGrid = document.getElementById('menu-grid');
        this.cartFooter = document.getElementById('cart-footer');
        this.searchWrapper = document.getElementById('searchWrapper');
        
        this.init();
    }

    init() {
        this.setupSearch(this.menuItems, this.renderMenu.bind(this), 
            (term) => (item) => item.name.toLowerCase().includes(term) || item.desc.toLowerCase().includes(term));
        this.setupTabs();
        this.setupCartModal();
        this.renderMenu();
        this.renderReviews();
    }

    renderMenu(items = this.menuItems) {
        if (items.length === 0) {
            LocalConnectUtils.showEmpty(this.menuGrid, "No dishes found matching your search.");
            return;
        }
        
        this.menuGrid.innerHTML = "";
        items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'menu-card';
            let action = item.qty > 0 ? `
                <div class="qty-selector" style="display:flex; align-items:center; background:var(--primary-green); color:white; border-radius:8px; padding:4px 8px; gap:10px;">
                    <button onclick="vendorPage.updateQty(${item.id}, -1)" style="background:none; border:none; color:white; cursor:pointer;">-</button>
                    <span style="font-weight:700;">${item.qty}</span>
                    <button onclick="vendorPage.updateQty(${item.id}, 1)" style="background:none; border:none; color:white; cursor:pointer;">+</button>
                </div>` : `<button class="btn-add" onclick="vendorPage.updateQty(${item.id}, 1)">Add</button>`;

            card.innerHTML = `<img src="${item.img}" class="item-img"><h4>${item.name}</h4><p style="font-size:0.8rem; color:#7f8c8d; margin:5px 0 15px; min-height:32px;">${item.desc}</p><div class="action-row" style="display:flex; justify-content:space-between; align-items:center; margin-top:auto;"><span class="price">${LocalConnectUtils.formatCurrency(item.price)}</span>${action}</div>`;
            this.menuGrid.appendChild(card);
        });
        this.updateCart();
    }

    updateQty(id, change) {
        const item = this.menuItems.find(i => i.id === id);
        item.qty = Math.max(0, item.qty + change);
        const term = this.searchInput.value.toLowerCase();
        this.renderMenu(this.menuItems.filter(i => i.name.toLowerCase().includes(term) || i.desc.toLowerCase().includes(term)));
    }

    updateCart() {
        const count = this.menuItems.reduce((s, i) => s + i.qty, 0);
        const total = this.menuItems.reduce((s, i) => s + (i.qty * i.price), 0);
        if(count > 0) {
            this.cartFooter.classList.remove('hidden');
            document.getElementById('cart-count').innerText = `${count} items`;
            document.getElementById('cart-total').innerText = LocalConnectUtils.formatCurrency(total);
        } else { 
            this.cartFooter.classList.add('hidden'); 
        }
    }

    renderReviews() {
        document.getElementById('reviews-list').innerHTML = this.reviewsData.map(rev => `
            <div class="review-card"><strong>${rev.name}</strong><small style="float:right">${rev.date}</small><p>${rev.text}</p></div>
        `).join('');
    }

    openCart() {
        const cartModal = document.getElementById('cart-modal');
        const cartItemsList = document.getElementById('cart-items-list');
        const modalTotal = document.getElementById('modal-total');
        
        const cartItems = this.menuItems.filter(item => item.qty > 0);
        const total = cartItems.reduce((s, i) => s + (i.qty * i.price), 0);
        
        if (cartItems.length === 0) {
            cartItemsList.innerHTML = `
                <div class="empty-cart">
                    <i class="fa-solid fa-shopping-cart"></i>
                    <h3>Your cart is empty</h3>
                    <p>Add some delicious items to get started!</p>
                </div>`;
            modalTotal.style.display = 'none';
        } else {
            cartItemsList.innerHTML = cartItems.map(item => `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <h4>${item.name}</h4>
                        <p>${LocalConnectUtils.formatCurrency(item.price)} each</p>
                    </div>
                    <div class="cart-item-controls">
                        <div class="qty-selector" style="display:flex; align-items:center; background:var(--primary-green); color:white; border-radius:8px; padding:4px 8px; gap:10px;">
                            <button onclick="vendorPage.updateQty(${item.id}, -1)" style="background:none; border:none; color:white; cursor:pointer; font-size:16px;">-</button>
                            <span style="font-weight:700; min-width:20px; text-align:center;">${item.qty}</span>
                            <button onclick="vendorPage.updateQty(${item.id}, 1)" style="background:none; border:none; color:white; cursor:pointer; font-size:16px;">+</button>
                        </div>
                        <span style="font-weight:600; color:var(--primary-green);">${LocalConnectUtils.formatCurrency(item.qty * item.price)}</span>
                    </div>
                </div>
            `).join('');
            modalTotal.innerHTML = `Total: ${LocalConnectUtils.formatCurrency(total)}`;
            modalTotal.style.display = 'block';
        }
        
        cartModal.classList.add('active');
    }

    closeCart() {
        document.getElementById('cart-modal').classList.remove('active');
    }

    proceedToBuy() {
        const cartItems = this.menuItems.filter(item => item.qty > 0);
        
        if (cartItems.length === 0) {
            alert('Your cart is empty!');
            return;
        }
        
        this.showDeliverySelection(cartItems);
    }

    showDeliverySelection(cartItems) {
        const cartItemsList = document.getElementById('cart-items-list');
        const modalTotal = document.getElementById('modal-total');
        const total = cartItems.reduce((s, i) => s + (i.qty * i.price), 0);
        
        cartItemsList.innerHTML = `
            <div class="order-step">
                <h3>Choose Delivery Option</h3>
                <div class="delivery-options">
                    <div class="delivery-option" onclick="vendorPage.selectDelivery('takeaway', ${total})">
                        <div class="option-icon">🏪</div>
                        <div class="option-details">
                            <h4>Takeaway</h4>
                            <p>Ready in 15-20 minutes</p>
                            <span class="price">Free</span>
                        </div>
                    </div>
                    <div class="delivery-option" onclick="vendorPage.selectDelivery('delivery', ${total})">
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
        modalTotal.innerHTML = `Subtotal: ${LocalConnectUtils.formatCurrency(total)}`;
    }

    selectDelivery(type, subtotal) {
        const deliveryFee = type === 'delivery' ? 30 : 0;
        const total = subtotal + deliveryFee;
        this.showPaymentOptions(type, total, subtotal, deliveryFee);
    }

    showPaymentOptions(deliveryType, total, subtotal, deliveryFee) {
        const cartItemsList = document.getElementById('cart-items-list');
        const modalTotal = document.getElementById('modal-total');
        
        cartItemsList.innerHTML = `
            <div class="order-step">
                <h3>Payment Method</h3>
                <div class="order-summary">
                    <div class="summary-row">
                        <span>Subtotal:</span>
                        <span>${LocalConnectUtils.formatCurrency(subtotal)}</span>
                    </div>
                    <div class="summary-row">
                        <span>${deliveryType === 'delivery' ? 'Delivery Fee:' : 'Takeaway:'}</span>
                        <span>${deliveryFee > 0 ? LocalConnectUtils.formatCurrency(deliveryFee) : 'Free'}</span>
                    </div>
                    <div class="summary-row total-row">
                        <span>Total:</span>
                        <span>${LocalConnectUtils.formatCurrency(total)}</span>
                    </div>
                </div>
                <div class="payment-options">
                    <div class="payment-option" onclick="vendorPage.processPayment('online', '${deliveryType}', ${total})">
                        <div class="option-icon">💳</div>
                        <div class="option-details">
                            <h4>Online Payment</h4>
                            <p>Pay now with card/UPI</p>
                        </div>
                    </div>
                    <div class="payment-option" onclick="vendorPage.processPayment('cash', '${deliveryType}', ${total})">
                        <div class="option-icon">💵</div>
                        <div class="option-details">
                            <h4>Cash on ${deliveryType === 'delivery' ? 'Delivery' : 'Pickup'}</h4>
                            <p>Pay when you receive</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        modalTotal.style.display = 'none';
    }

    processPayment(paymentType, deliveryType, total) {
        const paymentMethod = paymentType === 'online' ? 'Online Payment' : `Cash on ${deliveryType === 'delivery' ? 'Delivery' : 'Pickup'}`;
        
        this.menuItems.forEach(item => item.qty = 0);
        this.updateCart();
        this.closeCart();
        
        const timeEstimate = deliveryType === 'delivery' ? '25-30 minutes' : '15-20 minutes';
        alert(`🎉 Order placed successfully!\n\nDelivery: ${deliveryType === 'delivery' ? 'Home Delivery' : 'Takeaway'}\nPayment: ${paymentMethod}\nTotal: ${LocalConnectUtils.formatCurrency(total)}\n\nYour order will be ready in ${timeEstimate}.\nThank you for choosing Raj's Chaat Corner!`);
        
        const term = this.searchInput.value.toLowerCase();
        this.renderMenu(this.menuItems.filter(i => i.name.toLowerCase().includes(term) || i.desc.toLowerCase().includes(term)));
    }

    setupCartModal() {
        document.addEventListener('click', (e) => {
            const cartModal = document.getElementById('cart-modal');
            if (e.target === cartModal) {
                this.closeCart();
            }
        });
    }
}

// Global functions for HTML onclick handlers
function openCart() {
    vendorPage.openCart();
}

function closeCart() {
    vendorPage.closeCart();
}

function proceedToBuy() {
    vendorPage.proceedToBuy();
}

// Global instance
let vendorPage;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    vendorPage = new VendorDetailsPage();
});