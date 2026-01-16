/**
 * Food & Restaurant Page - extending LocalConnect Base
 */
class FoodRestaurantPage extends LocalConnectBase {
    constructor() {
        // Inject header and chat button first
        HeaderManager.injectHeader({
            searchPlaceholder: 'Search for vendors...'
        });
        HeaderManager.injectChatButton();
        
        super();
        this.vendors = [
            { category: "street", name: "Raj's Chaat Corner", rating: 4.5, dist: "1.2 km", tags: ["Chaat", "Snacks"], discount: "20% OFF", img: "https://images.unsplash.com/photo-1505253504418-4f944947593c?w=200" },
            { category: "street", name: "Tandoori Express", rating: 4.3, dist: "0.8 km", tags: ["Kebabs", "Grill"], img: "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=200" },
            { category: "shop", name: "Gupta Sweets", rating: 4.4, dist: "0.5 km", tags: ["Sweets", "Bakery"], discount: "15% OFF", img: "https://images.unsplash.com/photo-1589119908995-c6837fa14848?w=200" },
            { category: "shop", name: "Spice & Bites", rating: 4.2, dist: "1.1 km", tags: ["Spices"], img: "https://images.unsplash.com/photo-1512152272829-e3139592d56f?w=200" },
            { category: "restaurant", name: "Highway Dhaba", rating: 4.6, dist: "3.0 km", tags: ["North Indian"], discount: "10% OFF", img: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=200" },
            { category: "restaurant", name: "Sharma's Kitchen", rating: 4.7, dist: "1.2 km", tags: ["Punjabi"], img: "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=200" }
        ];
        this.init();
    }

    init() {
        this.setupFilters();
        this.setupSearch(this.vendors, this.renderFilteredVendors.bind(this));
        this.render();
    }

    setupSearch(items, renderCallback) {
        if (!this.searchInput) return;
        
        this.searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = items.filter(item => item.name.toLowerCase().includes(term));
            renderCallback(filtered);
        });
    }

    renderFilteredVendors(filteredVendors) {
        // Clear all lists first
        document.getElementById('street-food-list').innerHTML = '';
        document.getElementById('food-shops-list').innerHTML = '';
        document.getElementById('restaurants-list').innerHTML = '';
        
        // Render filtered vendors in their respective categories
        const streetVendors = filteredVendors.filter(v => v.category === 'street');
        const shopVendors = filteredVendors.filter(v => v.category === 'shop');
        const restaurantVendors = filteredVendors.filter(v => v.category === 'restaurant');
        
        document.getElementById('street-food-list').innerHTML = streetVendors.map(v => this.createCard(v)).join('');
        document.getElementById('food-shops-list').innerHTML = shopVendors.map(v => this.createCard(v)).join('');
        document.getElementById('restaurants-list').innerHTML = restaurantVendors.map(v => this.createCard(v)).join('');
    }

    createCard(v) {
        return `
            <div class="card">
                <img src="${v.img}" alt="${v.name}">
                <div class="card-content">
                    <h3>${v.name}</h3>
                    <div style="display: flex; align-items: center; gap: 5px; font-size: 0.85rem;">
                        <i class="fa fa-star" style="color: #f1c40f;"></i> 
                        <b>${this.formatRating(v.rating)}</b> 
                        <span style="color: #999;">• ${v.dist}</span>
                    </div>
                    <div class="separator"></div>
                    <div style="display: flex; gap: 5px;">
                        ${v.tags.map(t => `<span class="tag">${t}</span>`).join('')}
                    </div>
                    <button class="view-menu-btn" onclick="viewDetails('${encodeURIComponent(JSON.stringify(v))}')">View Details</button>
                </div>
            </div>`;
    }

    render() {
        document.getElementById('street-food-list').innerHTML = this.vendors.filter(v => v.category === 'street').map(v => this.createCard(v)).join('');
        document.getElementById('food-shops-list').innerHTML = this.vendors.filter(v => v.category === 'shop').map(v => this.createCard(v)).join('');
        document.getElementById('restaurants-list').innerHTML = this.vendors.filter(v => v.category === 'restaurant').map(v => this.createCard(v)).join('');
    }
}

// Global function for card click handler
function viewDetails(vendorData) {
    localStorage.setItem('selectedVendor', vendorData);
    window.location.href = 'veiwdet.html';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FoodRestaurantPage();
});