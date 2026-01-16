/**
 * My Orders Page - extending LocalConnect Base
 */
class OrdersPage extends LocalConnectBase {
    constructor() {
        super();
        this.userId = window.userId || '';
        this.ordersKey = this.userId ? `user_${this.userId}_orders` : 'orders';
        this.orders = JSON.parse(localStorage.getItem(this.ordersKey) || '[]');
        this.init();
    }

    init() {
        this.renderOrdersList();
    }

    renderOrdersList() {
        const ordersList = document.getElementById('orders-list');
        const ordersContainer = document.querySelector('.orders-container');
        
        document.getElementById('order-details').classList.add('hidden');
        document.getElementById('orders-list').style.display = 'block';
        ordersContainer.style.display = 'block';
        
        this.orders = JSON.parse(localStorage.getItem(this.ordersKey) || '[]');
        
        if (this.orders.length === 0) {
            ordersList.innerHTML = '<div style="text-align:center;padding:60px 20px;color:#7f8c8d;"><i class="fa-solid fa-shopping-bag" style="font-size:48px;margin-bottom:20px;color:#27ae60;"></i><h3>No orders yet</h3><p>Your orders will appear here after you place them.</p></div>';
            return;
        }
        
        ordersList.innerHTML = this.orders.map(order => `
            <div class="order-card" onclick="ordersPage.showOrderDetails(${order.id})">
                <div class="order-header">
                    <div class="order-info">
                        <h4>Order #${order.id}</h4>
                        <p class="vendor-name">${order.vendor}</p>
                    </div>
                    <div class="order-status">
                        <span class="status-badge ${order.status}">${this.getStatusText(order.status)}</span>
                        <span class="order-total">₹${order.total}</span>
                    </div>
                </div>
                <div class="order-items">
                    <p>${order.items.map(i => `${i.name} x${i.qty}`).join(', ')}</p>
                </div>
                <div class="order-meta">
                    <span class="order-type">${order.deliveryType === 'delivery' ? '🚚 Delivery' : '🏪 Takeaway'}</span>
                    <span class="order-date">${order.date}</span>
                </div>
            </div>
        `).join('');
    }

    showOrderDetails(orderId) {
        const order = this.orders.find(o => o.id === orderId);
        if (!order) return;

        document.getElementById('orders-list').style.display = 'none';
        document.getElementById('order-details').classList.remove('hidden');
        document.getElementById('order-title').textContent = `Order #${orderId}`;

        const detailsContent = document.getElementById('details-content');
        const canReview = order.status === 'delivered' || order.status === 'ready';
        const hasReview = order.review;
        
        detailsContent.innerHTML = `
            <div class="order-summary">
                <h4>${order.vendor}</h4>
                <p class="order-date">${order.date}</p>
                <div class="status-info">
                    <span class="status-badge ${order.status}">${this.getStatusText(order.status)}</span>
                    <span class="order-type">${order.deliveryType === 'delivery' ? '🚚 Delivery' : '🏪 Takeaway'}</span>
                </div>
            </div>
            
            <div class="order-items-detail">
                <h5>Items Ordered:</h5>
                ${order.items.map(item => `<p>• ${item.name} x${item.qty} - ₹${item.price * item.qty}</p>`).join('')}
                <div class="total-amount">Total: ₹${order.total}</div>
            </div>
            
            ${hasReview ? `
                <div style="background:#f8f9fa;padding:20px;border-radius:10px;margin-top:20px;">
                    <h5 style="margin:0 0 10px 0;">Your Review</h5>
                    <div style="color:#f1c40f;margin-bottom:10px;">${'★'.repeat(order.review.rating)}${'☆'.repeat(5-order.review.rating)}</div>
                    <p style="margin:0;color:#2c3e50;">${order.review.comment}</p>
                    <p style="margin:10px 0 0 0;color:#7f8c8d;font-size:12px;">${order.review.date}</p>
                </div>
            ` : canReview ? `
                <div class="order-actions">
                    <button class="action-btn primary" onclick="ordersPage.openReviewModal(${order.id})" style="background:#f39c12;">
                        <i class="fa-solid fa-star"></i> Write Review
                    </button>
                </div>
            ` : ''}
            
            <div class="order-actions">
                ${this.getOrderActions(order)}
                ${order.status === 'preparing' ? `
                    <button class="action-btn" onclick="ordersPage.cancelOrder(${order.id})" style="background:#e74c3c;color:white;">
                        <i class="fa-solid fa-times-circle"></i> Cancel Order
                    </button>
                ` : ''}
                <p style="text-align:center;color:#7f8c8d;margin-top:15px;">Payment: ${order.paymentType === 'online' ? 'Online Payment' : 'Cash on ' + (order.deliveryType === 'delivery' ? 'Delivery' : 'Pickup')}</p>
            </div>
        `;
    }

    getOrderActions(order) {
        if (order.deliveryType === 'takeaway') {
            return `
                <button class="action-btn primary" onclick="ordersPage.viewMap(${order.id})">
                    <i class="fa-solid fa-map-marker-alt"></i> View Map
                </button>
            `;
        } else {
            return `
                <button class="action-btn primary" onclick="ordersPage.trackOrder(${order.id})">
                    <i class="fa-solid fa-truck"></i> Track Order
                </button>
            `;
        }
    }

    getStatusText(status) {
        const statusMap = {
            'preparing': 'Preparing',
            'ready': 'Ready for Pickup',
            'out_for_delivery': 'Out for Delivery',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled'
        };
        return statusMap[status] || status;
    }

    viewMap(orderId) {
        const order = this.orders.find(o => o.id === orderId);
        const detailsContent = document.getElementById('details-content');
        
        detailsContent.innerHTML = `
            <div class="map-section">
                <div class="map-header">
                    <button class="back-btn" onclick="ordersPage.showOrderDetails(${orderId})">← Back</button>
                    <h4>Vendor Location - ${order.vendor}</h4>
                </div>
                <div class="map-container">
                    <div class="map-placeholder">
                        <i class="fa-solid fa-map-marker-alt" style="font-size:48px;color:#27ae60;margin-bottom:20px;"></i>
                        <h3>${order.vendor}</h3>
                        <p>📍 Sector 15, Near Central Mall</p>
                        <p>📞 +91 98765 43210</p>
                        <p>🕒 Open: 10:30 AM - 11:00 PM</p>
                        <div class="directions" style="margin-top:20px;text-align:left;">
                            <p><strong>Directions:</strong></p>
                            <p>• Head north on Main Road for 0.5 km</p>
                            <p>• Turn right at Food Street</p>
                            <p>• Vendor will be on your left</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    trackOrder(orderId) {
        const order = this.orders.find(o => o.id === orderId);
        const detailsContent = document.getElementById('details-content');
        
        const trackingSteps = [
            { status: 'Order Placed', completed: true, time: new Date(order.id).toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'}) },
            { status: 'Preparing', completed: order.status !== 'preparing', time: order.status !== 'preparing' ? new Date(order.id + 600000).toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'}) : '' },
            { status: 'Out for Delivery', completed: order.status === 'delivered', time: order.status === 'delivered' ? new Date(order.id + 1200000).toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'}) : '' },
            { status: 'Delivered', completed: order.status === 'delivered', time: order.status === 'delivered' ? new Date(order.id + 1800000).toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'}) : '' }
        ];
        
        detailsContent.innerHTML = `
            <div class="tracking-section">
                <div class="tracking-header">
                    <button class="back-btn" onclick="ordersPage.showOrderDetails(${orderId})">← Back</button>
                    <h4>Track Order #${orderId}</h4>
                </div>
                <div class="tracking-info" style="background:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:20px;">
                    <p><strong>Estimated Delivery:</strong> 25-30 minutes</p>
                    <p><strong>Delivery Address:</strong> Your Location</p>
                </div>
                <div class="tracking-steps" style="display:flex;flex-direction:column;gap:20px;">
                    ${trackingSteps.map(step => `
                        <div class="tracking-step ${step.completed ? 'completed' : ''}" style="display:flex;gap:15px;align-items:flex-start;">
                            <div class="step-icon" style="width:40px;height:40px;border-radius:50%;background:${step.completed ? '#27ae60' : '#e0e0e0'};display:flex;align-items:center;justify-content:center;color:white;flex-shrink:0;">
                                <i class="fa-solid ${step.completed ? 'fa-check' : 'fa-clock'}"></i>
                            </div>
                            <div class="step-content">
                                <h5 style="margin:0 0 5px 0;color:${step.completed ? '#27ae60' : '#7f8c8d'};">${step.status}</h5>
                                ${step.time ? `<p style="margin:0;color:#7f8c8d;font-size:14px;">${step.time}</p>` : '<p style="margin:0;color:#7f8c8d;font-size:14px;">Pending</p>'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    openReviewModal(orderId) {
        const order = this.orders.find(o => o.id === orderId);
        const detailsContent = document.getElementById('details-content');
        
        detailsContent.innerHTML = `
            <div style="max-width:500px;margin:0 auto;">
                <button class="back-btn" onclick="ordersPage.showOrderDetails(${orderId})" style="margin-bottom:20px;">← Back</button>
                <h3 style="text-align:center;margin-bottom:30px;">Rate Your Experience</h3>
                <div style="text-align:center;margin-bottom:30px;">
                    <h4 style="margin-bottom:15px;">${order.vendor}</h4>
                    <div id="starRating" style="font-size:40px;cursor:pointer;">
                        <span onclick="ordersPage.setRating(1)" data-rating="1">☆</span>
                        <span onclick="ordersPage.setRating(2)" data-rating="2">☆</span>
                        <span onclick="ordersPage.setRating(3)" data-rating="3">☆</span>
                        <span onclick="ordersPage.setRating(4)" data-rating="4">☆</span>
                        <span onclick="ordersPage.setRating(5)" data-rating="5">☆</span>
                    </div>
                </div>
                <textarea id="reviewComment" placeholder="Share your experience with this vendor..." style="width:100%;padding:15px;border:1px solid #ddd;border-radius:10px;min-height:120px;resize:vertical;margin-bottom:20px;"></textarea>
                <button onclick="ordersPage.submitReview(${orderId})" style="width:100%;padding:15px;background:#27ae60;color:white;border:none;border-radius:10px;font-weight:600;cursor:pointer;">
                    <i class="fa-solid fa-paper-plane"></i> Submit Review
                </button>
            </div>
        `;
        this.currentRating = 0;
    }
    
    setRating(rating) {
        this.currentRating = rating;
        const stars = document.querySelectorAll('#starRating span');
        stars.forEach((star, idx) => {
            star.textContent = idx < rating ? '★' : '☆';
            star.style.color = idx < rating ? '#f1c40f' : '#ddd';
        });
    }
    
    submitReview(orderId) {
        if (!this.currentRating) {
            alert('Please select a rating');
            return;
        }
        
        const comment = document.getElementById('reviewComment').value.trim();
        if (!comment) {
            alert('Please write a comment');
            return;
        }
        
        const orderIndex = this.orders.findIndex(o => o.id === orderId);
        this.orders[orderIndex].review = {
            rating: this.currentRating,
            comment: comment,
            date: new Date().toLocaleString()
        };
        
        localStorage.setItem(this.ordersKey, JSON.stringify(this.orders));
        alert('Thank you for your review!');
        this.showOrderDetails(orderId);
    }
    
    cancelOrder(orderId) {
        if (!confirm('Are you sure you want to cancel this order?')) return;
        
        const orderIndex = this.orders.findIndex(o => o.id === orderId);
        this.orders[orderIndex].status = 'cancelled';
        localStorage.setItem(this.ordersKey, JSON.stringify(this.orders));
        alert('Order cancelled successfully');
        this.showOrderDetails(orderId);
    }
}

function showOrdersList() {
    ordersPage.renderOrdersList();
}

// Global instance
let ordersPage;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    ordersPage = new OrdersPage();
});