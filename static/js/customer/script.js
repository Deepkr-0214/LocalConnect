/**
 * Index Page - Dashboard functionality extending LocalConnect Base
 */
class DashboardPage extends LocalConnectBase {
    constructor() {
        // Inject header and chat button first
        HeaderManager.injectHeader({
            searchPlaceholder: 'Search for shops or services'
        });
        HeaderManager.injectChatButton();
        
        super();
        this.vendors = [
            { 
                name: "Wellness Pharmacy", 
                distance: "0.8 km away", 
                rating: 5, 
                image: "https://images.unsplash.com/photo-1586015555751-63bb77f4322a?auto=format&fit=crop&q=80&w=400" 
            },
            { 
                name: "Green Grocers", 
                distance: "1.2 km away", 
                rating: 5, 
                image: "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=400" 
            },
            { 
                name: "The Sugar Bloom", 
                distance: "2.5 km away", 
                rating: 4, 
                image: "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&q=80&w=400" 
            },
            { 
                name: "Harbor Bistro", 
                distance: "3.1 km away", 
                rating: 5, 
                image: "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&q=80&w=400" 
            },
            { 
                name: "AutoExpert Service", 
                distance: "4.3 km away", 
                rating: 4, 
                image: "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&q=80&w=400" 
            }
        ];
        
        this.vendorGrid = document.getElementById('vendor-grid');
        this.init();
    }

    init() {
        this.setupSearch(this.vendors, this.renderVendors.bind(this));
        this.renderVendors(this.vendors);
    }

    renderVendors(data) {
        this.vendorGrid.innerHTML = "";
        data.forEach(item => {
            const stars = this.generateStars(item.rating);
            
            this.vendorGrid.innerHTML += `
                <div class="vendor-card">
                    <div class="shop-image-container">
                        <img src="${item.image}" alt="${item.name}">
                    </div>
                    <div class="vendor-info">
                        <h4>${item.name}</h4>
                        <div class="rating">
                            ${stars}
                            <span class="distance">${this.formatDistance(item.distance)}</span>
                        </div>
                        <div class="btn-group">
                            <button class="pill-btn btn-takeaway">Takeaway</button>
                            <button class="pill-btn btn-delivery">Delivery</button>
                        </div>
                    </div>
                </div>
            `;
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DashboardPage();
});