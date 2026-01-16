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

        // Initialize vendors with "Getting location..." message
        const vendors = vendorsFromServer.map(v => ({
            id: v.id,
            name: v.name,
            category: categoryMap[v.category] || 'shop',
            rating: 4.5,
            reviews: Math.floor(Math.random() * 1000) + 100,
            distance: 'Getting location...',
            image: v.shop_image || '🏪',
            cuisine: v.category,
            priceRange: `₹${v.min_price}-${v.max_price}`,
            deliveryTime: '15-25 min',
            isOpen: v.is_open,
            latitude: v.latitude,
            longitude: v.longitude
        }));

        // Function to calculate and display distances
        const calculateDistances = (userLat, userLon) => {
            console.log('User location:', userLat, userLon);
            vendors.forEach(vendor => {
                console.log(`Vendor ${vendor.name}:`, vendor.latitude, vendor.longitude);
                if (vendor.latitude && vendor.longitude) {
                    const distance = this.calculateDistance(
                        userLat, userLon,
                        vendor.latitude, vendor.longitude
                    );
                    vendor.distance = distance.toFixed(1) + ' km';
                    console.log(`Distance to ${vendor.name}: ${vendor.distance}`);
                } else {
                    vendor.distance = 'N/A';
                    console.log(`${vendor.name} has no coordinates`);
                }
            });

            // Sort by distance (closest first)
            vendors.sort((a, b) => {
                const distA = parseFloat(a.distance) || 999;
                const distB = parseFloat(b.distance) || 999;
                return distA - distB;
            });

            this.vendors = vendors;
            this.filteredVendors = [...this.vendors];
            this.renderVendors();
        };

        // Check if we have stored customer coordinates
        if (customerStoredLat && customerStoredLon) {
            console.log('Using stored customer location');
            calculateDistances(customerStoredLat, customerStoredLon);
        }
        
        // Always try to get live browser location for real-time distance
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    console.log('Using live browser location');
                    const userLat = position.coords.latitude;
                    const userLon = position.coords.longitude;
                    calculateDistances(userLat, userLon);
                },
                (error) => {
                    console.warn('Geolocation error:', error);
                    if (!customerStoredLat && !customerStoredLon) {
                        vendors.forEach(vendor => {
                            vendor.distance = 'Location disabled';
                        });
                        this.vendors = vendors;
                        this.filteredVendors = [...this.vendors];
                        this.renderVendors();
                    }
                }
            );
        } else if (!customerStoredLat && !customerStoredLon) {
            vendors.forEach(vendor => {
                vendor.distance = 'Location unavailable';
            });
            this.vendors = vendors;
            this.filteredVendors = [...this.vendors];
            this.renderVendors();
        }

        return vendors;
    }

    // Haversine formula to calculate distance between two coordinates
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Radius of Earth in kilometers
        const dLat = this.toRadians(lat2 - lat1);
        const dLon = this.toRadians(lon2 - lon1);

        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);

        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distance = R * c;

        return distance;
    }

    toRadians(degrees) {
        return degrees * (Math.PI / 180);
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

        // Separate vendors by category
        const streetVendors = this.filteredVendors.filter(v => v.category === 'street');
        const shopVendors = this.filteredVendors.filter(v => v.category === 'shop');
        const restaurantVendors = this.filteredVendors.filter(v => v.category === 'restaurant');

        // Sort each category by distance
        const sortByDistance = (a, b) => {
            const distA = parseFloat(a.distance) || 999;
            const distB = parseFloat(b.distance) || 999;
            return distA - distB;
        };

        streetVendors.sort(sortByDistance);
        shopVendors.sort(sortByDistance);
        restaurantVendors.sort(sortByDistance);

        // Render sorted vendors
        streetVendors.forEach(vendor => {
            if (streetList) streetList.appendChild(this.createVendorCard(vendor));
        });

        shopVendors.forEach(vendor => {
            if (shopsList) shopsList.appendChild(this.createVendorCard(vendor));
        });

        restaurantVendors.forEach(vendor => {
            if (restaurantsList) restaurantsList.appendChild(this.createVendorCard(vendor));
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