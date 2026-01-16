/**
 * Food & Restaurant Page JavaScript
 */

class FoodRestaurantPage {
    constructor() {
        this.vendors = [
            {
                id: 1,
                name: "Raj's Chaat Corner",
                category: "street",
                rating: 4.5,
                reviews: 1200,
                distance: "1.2 km",
                image: "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=300&h=200&fit=crop",
                cuisine: "Street Food",
                priceRange: "₹100-300",
                deliveryTime: "15-25 min",
                isOpen: true
            },
            {
                id: 2,
                name: "Sharma Sweets & Snacks",
                category: "shop",
                rating: 4.3,
                reviews: 850,
                distance: "0.8 km",
                image: "https://images.unsplash.com/photo-1559181567-c3190ca9959b?w=300&h=200&fit=crop",
                cuisine: "Sweets & Snacks",
                priceRange: "₹50-200",
                deliveryTime: "10-20 min",
                isOpen: true
            },
            {
                id: 3,
                name: "Delhi Darbar Restaurant",
                category: "restaurant",
                rating: 4.7,
                reviews: 2100,
                distance: "2.1 km",
                image: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=300&h=200&fit=crop",
                cuisine: "North Indian",
                priceRange: "₹300-800",
                deliveryTime: "25-35 min",
                isOpen: true
            },
            {
                id: 4,
                name: "Momos Point",
                category: "street",
                rating: 4.2,
                reviews: 650,
                distance: "0.5 km",
                image: "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=300&h=200&fit=crop",
                cuisine: "Momos & Chinese",
                priceRange: "₹80-250",
                deliveryTime: "10-15 min",
                isOpen: false
            },
            {
                id: 5,
                name: "Fresh Fruits Corner",
                category: "shop",
                rating: 4.1,
                reviews: 320,
                distance: "1.5 km",
                image: "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=300&h=200&fit=crop",
                cuisine: "Fresh Fruits",
                priceRange: "₹30-150",
                deliveryTime: "5-15 min",
                isOpen: true
            },
            {
                id: 6,
                name: "Punjabi Dhaba",
                category: "restaurant",
                rating: 4.4,
                reviews: 1800,
                distance: "3.2 km",
                image: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=300&h=200&fit=crop",
                cuisine: "Punjabi",
                priceRange: "₹250-600",
                deliveryTime: "30-40 min",
                isOpen: true
            }
        ];

        this.filteredVendors = [...this.vendors];
        this.init();
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

        card.innerHTML = `
            <div class="vendor-image">
                <img src="${vendor.image}" alt="${vendor.name}" onerror="this.src='https://via.placeholder.com/300x200?text=No+Image'">
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