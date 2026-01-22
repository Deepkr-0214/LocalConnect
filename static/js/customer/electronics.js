/**
 * Electronics Page JavaScript
 */

class ElectronicsPage {
    constructor() {
        this.vendors = this.loadVendors();
        this.filteredVendors = [...this.vendors];
        this.init();
    }

    loadVendors() {
        const categoryMap = {
            'Mobiles': 'mobiles',
            'Home Appliances': 'home-appliances',
            'Kitchen Appliances': 'kitchen-appliances',
        };

        const vendors = vendorsFromServer.map(v => ({
            id: v.id,
            name: v.name,
            category: categoryMap[v.subcategory] || 'mobiles',
            rating: v.rating || 0,
            reviews: v.review_count || 0,
            distance: 'Getting location...',
            image: v.shop_image || '📱',
            cuisine: v.subcategory,
            priceRange: `₹${v.min_price}-${v.max_price}`,
            deliveryTime: '15-30 min',
            isOpen: v.is_open,
            latitude: v.latitude,
            longitude: v.longitude
        }));

        const calculateDistances = (userLat, userLon) => {
            vendors.forEach(vendor => {
                if (vendor.latitude && vendor.longitude) {
                    const distance = this.calculateDistance(userLat, userLon, vendor.latitude, vendor.longitude);
                    vendor.distance = distance.toFixed(1) + ' km';
                } else {
                    vendor.distance = 'N/A';
                }
            });
            vendors.sort((a, b) => {
                const distA = parseFloat(a.distance) || 999;
                const distB = parseFloat(b.distance) || 999;
                return distA - distB;
            });
            this.vendors = vendors;
            this.filteredVendors = [...this.vendors];
            this.renderVendors();
        };

        if (customerStoredLat && customerStoredLon) {
            calculateDistances(customerStoredLat, customerStoredLon);
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    calculateDistances(position.coords.latitude, position.coords.longitude);
                },
                (error) => {
                    if (!customerStoredLat && !customerStoredLon) {
                        vendors.forEach(vendor => { vendor.distance = 'Location disabled'; });
                        this.vendors = vendors;
                        this.filteredVendors = [...this.vendors];
                        this.renderVendors();
                    }
                }
            );
        } else if (!customerStoredLat && !customerStoredLon) {
            vendors.forEach(vendor => { vendor.distance = 'Location unavailable'; });
            this.vendors = vendors;
            this.filteredVendors = [...this.vendors];
            this.renderVendors();
        }

        return vendors;
    }

    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = this.toRadians(lat2 - lat1);
        const dLon = this.toRadians(lon2 - lon1);
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    toRadians(degrees) { return degrees * (Math.PI / 180); }

    init() {
        this.renderVendors();
        this.setupFilters();
        this.setupSearch();
    }

    renderVendors() {
        const mobilesList = document.getElementById('mobiles-list');
        const home_appliancesList = document.getElementById('home-appliances-list');
        const kitchen_appliancesList = document.getElementById('kitchen-appliances-list');

        if (mobilesList) mobilesList.innerHTML = '';
        if (home_appliancesList) home_appliancesList.innerHTML = '';
        if (kitchen_appliancesList) kitchen_appliancesList.innerHTML = '';

        const mobilesVendors = this.filteredVendors.filter(v => v.category === 'mobiles');
        const home_appliancesVendors = this.filteredVendors.filter(v => v.category === 'home-appliances');
        const kitchen_appliancesVendors = this.filteredVendors.filter(v => v.category === 'kitchen-appliances');

        const sortByDistance = (a, b) => {
            const distA = parseFloat(a.distance) || 999;
            const distB = parseFloat(b.distance) || 999;
            return distA - distB;
        };

        mobilesVendors.sort(sortByDistance);
        home_appliancesVendors.sort(sortByDistance);
        kitchen_appliancesVendors.sort(sortByDistance);

        mobilesVendors.forEach(vendor => {
            if (mobilesList) mobilesList.appendChild(this.createVendorCard(vendor));
        });
        home_appliancesVendors.forEach(vendor => {
            if (home_appliancesList) home_appliancesList.appendChild(this.createVendorCard(vendor));
        });
        kitchen_appliancesVendors.forEach(vendor => {
            if (kitchen_appliancesList) kitchen_appliancesList.appendChild(this.createVendorCard(vendor));
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
            imageHtml = `<div style="font-size:80px;display:flex;align-items:center;justify-content:center;height:100%;">📱</div>`;
        }

        let matchingDishesHtml = '';
        if (vendor.matching_dishes && vendor.matching_dishes.length > 0) {
            const dishList = vendor.matching_dishes.slice(0, 3).join(', ');
            const moreText = vendor.matching_dishes.length > 3 ? ` +${vendor.matching_dishes.length - 3} more` : '';
            matchingDishesHtml = `<div class="matching-dishes"><i class="fas fa-utensils"></i> ${dishList}${moreText}</div>`;
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
                ${matchingDishesHtml}
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
        if (!searchInput) return;

        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.trim().toLowerCase();

            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                this.performSearch(term);
            }, 300);
        });
    }

    async performSearch(searchTerm) {
        if (!searchTerm) {
            this.filteredVendors = [...this.vendors];
            this.renderVendors();
            return;
        }

        const localMatches = this.vendors.filter(vendor =>
            vendor.name.toLowerCase().includes(searchTerm) ||
            vendor.cuisine.toLowerCase().includes(searchTerm)
        );

        if (localMatches.length > 0) {
            this.filteredVendors = localMatches;
            this.renderVendors();
        }

        try {
            const response = await fetch(`/api/search/vendors?q=${encodeURIComponent(searchTerm)}`);
            if (response.ok) {
                const apiResults = await response.json();

                const categoryMap = {
                    'Mobiles': 'mobiles',
                    'Home Appliances': 'home-appliances',
                    'Kitchen Appliances': 'kitchen-appliances',
                };

                const mergedResults = apiResults
                    .filter(v => v.category === 'Electronics')
                    .map(apiVendor => {
                        const localVendor = this.vendors.find(v => v.id === apiVendor.id);
                        return {
                            ...apiVendor,
                            category: categoryMap[apiVendor.subcategory] || 'mobiles',
                            distance: localVendor ? localVendor.distance : 'N/A'
                        };
                    });

                this.filteredVendors = mergedResults;
                this.renderVendors();
            }
        } catch (error) {
            console.error('Search API failed:', error);
        }
    }

    viewVendorDetails(vendorId) {
        window.location.href = `/customer/vendor/${vendorId}`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ElectronicsPage();
});
