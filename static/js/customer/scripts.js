/**
 * Food & Restaurant Page JavaScript
 */

class FoodRestaurantPage {
    constructor() {
        this.vendors = this.loadVendors();
        this.filteredVendors = [...this.vendors];
        this.init();
    }

    loadVendors() {
        const categoryMap = {
            'Street Food': 'street',
            'Food Shop': 'shop',
            'Restaurant': 'restaurant',
            'Dhaba': 'restaurant'
        };
        
        return vendorsFromServer.map(v => ({
            id: v.id,
            name: v.name,
            category: categoryMap[v.category] || 'shop',
            rating: 4.5,
            reviews: Math.floor(Math.random() * 1000) + 100,
            distance: (Math.random() * 3 + 0.5).toFixed(1) + ' km',
            image: v.shop_image || '🏪',
            cuisine: v.category,
            priceRange: '₹100-300',
            deliveryTime: '15-25 min',
            isOpen: v.is_open
        }));
    }

    init() {
        this.renderVendors();
        this.setupFilters();
        this.setupSearch();
    }

    renderVendors() {
        const streetList = document.getElementById('street-food-list');
        const shopsList = document.getElementById('food-shops-list');
        const restaurantsList = document.getElementById('restaurants-list');

        if (streetList) streetList.innerHTML = '';
        if (shopsList) shopsList.innerHTML = '';
        if (restaurantsList) restaurantsList.innerHTML = '';

        this.filteredVendors.forEach(vendor => {
            const vendorCard = this.createVendorCard(vendor);
            
            switch(vendor.category) {
                case 'street':
                    if (streetList) streetList.appendChild(vendorCard);
                    break;
                case 'shop':
                    if (shopsList) shopsList.appendChild(vendorCard);
                    break;
                case 'restaurant':
                    if (restaurantsList) restaurantsList.appendChild(vendorCard);
                    break;
            }
        });
    }

    createVendorCard(vendor) {
        const card = document.createElement('div');
        card.className = 'vendor-card';
        card.onclick = () => this.viewVendorDetails(vendor.id);

        const isEmoji = /\p{Emoji}/u.test(vendor.image) && vendor.image.length < 10;
        const isBase64 = vendor.image && vendor.image.startsWith('data:image');
        
        let imageHtml;
        if (isEmoji) {
            imageHtml = `<div style="font-size:80px;display:flex;align-items:center;justify-content:center;height:100%;">${vendor.image}</div>`;
        } else if (isBase64) {
            imageHtml = `<img src="${vendor.image}" alt="${vendor.name}">`;
        } else {
            imageHtml = `<div style="font-size:80px;display:flex;align-items:center;justify-content:center;height:100%;">🏪</div>`;
        }

        card.innerHTML = `
            <div class="vendor-image">
                ${imageHtml}
                <div class="status-badge ${vendor.isOpen ? 'open' : 'closed'}">
                    ${vendor.isOpen ? 'Open' : 'Closed'}
                </div>
            </div>
            <div class="vendor-info">
                <h3>${vendor.name}</h3>
                <p class="cuisine">${vendor.cuisine}</p>
                <div class="vendor-meta">
                    <div class="rating">
                        <i class="fas fa-star"></i>
                        <span>${vendor.rating}</span>
                        <span class="reviews">(${vendor.reviews})</span>
                    </div>
                    <div class="distance">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${vendor.distance}</span>
                    </div>
                </div>
                <div class="vendor-details">
                    <span class="price-range">${vendor.priceRange}</span>
                    <span class="delivery-time">
                        <i class="fas fa-clock"></i>
                        ${vendor.deliveryTime}
                    </span>
                </div>
            </div>
        `;

        return card;
    }

    setupFilters() {
        const filterBtns = document.querySelectorAll('.filter-btn');
        const mainContainer = document.getElementById('mainContainer');

        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all buttons
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const target = btn.getAttribute('data-target');
                
                if (target === 'all') {
                    this.filteredVendors = [...this.vendors];
                    if (mainContainer) mainContainer.classList.remove('single-category');
                } else {
                    this.filteredVendors = this.vendors.filter(vendor => vendor.category === target);
                    if (mainContainer) mainContainer.classList.add('single-category');
                }

                // Show/hide columns
                document.querySelectorAll('.column').forEach(col => {
                    const cat = col.getAttribute('data-category');
                    if (target === 'all' || target === cat) {
                        col.classList.remove('hidden');
                    } else {
                        col.classList.add('hidden');
                    }
                });

                this.renderVendors();
            });
        });
    }

    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const term = e.target.value.toLowerCase();
                this.filteredVendors = this.vendors.filter(vendor => 
                    vendor.name.toLowerCase().includes(term) ||
                    vendor.cuisine.toLowerCase().includes(term)
                );
                this.renderVendors();
            });
        }
    }

    viewVendorDetails(vendorId) {
        window.location.href = `/customer/vendor/${vendorId}`;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FoodRestaurantPage();
});