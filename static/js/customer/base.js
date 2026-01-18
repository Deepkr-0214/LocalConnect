/**
 * LocalConnect Base JavaScript - Common functionality across all pages
 */

class LocalConnectBase {
    constructor() {
        this.initializeCommonElements();
        this.setupEventListeners();
    }

    // Initialize common DOM elements
    initializeCommonElements() {
        this.searchInput = document.getElementById('searchInput');
        this.chatBtn = document.getElementById('chatBtn') || document.querySelector('.chat-bot');
        this.logo = document.querySelector('.logo');
        this.profileIcon = document.getElementById('profileIcon');
        this.profileDropdown = document.getElementById('profileDropdown');
    }

    // Setup common event listeners
    setupEventListeners() {
        // Chat button functionality
        if (this.chatBtn) {
            this.chatBtn.addEventListener('click', this.showChatAlert);
        }

        // Logo click navigation
        if (this.logo) {
            this.logo.addEventListener('click', () => {
                window.location.href = '/customer/dashboard';
            });
        }

        // Profile dropdown functionality
        this.setupProfileDropdown();
        
        // Search toggle functionality
        this.setupSearchToggle();
    }

    // Common chat alert functionality
    showChatAlert() {
        alert("Chat loading... One of our LocalConnect assistants will be with you shortly!");
    }

    // Generate star rating HTML
    generateStars(rating, size = 12) {
        let stars = "";
        for(let i = 0; i < 5; i++) {
            const color = i < rating ? "#f1c40f" : "#e0e0e0";
            stars += `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="${color}" stroke="${color}">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>`;
        }
        return stars;
    }

    // Setup search functionality
    setupSearch(items, renderCallback, filterCallback) {
        if (!this.searchInput) return;
        
        this.searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = items.filter(filterCallback ? filterCallback(term) : 
                item => item.name.toLowerCase().includes(term));
            renderCallback(filtered);
        });
    }

    // Format distance string
    formatDistance(distance) {
        return distance.includes('km') ? distance : `${distance} km away`;
    }

    // Format rating number
    formatRating(rating) {
        return typeof rating === 'number' ? rating.toFixed(1) : rating;
    }

    // Common tab switching functionality
    setupTabs() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and content
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                const target = tab.getAttribute('data-target');
                const targetContent = document.getElementById(target);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }

    // Common filter functionality
    setupFilters() {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all filter buttons
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const target = btn.getAttribute('data-target');
                const container = document.getElementById('mainContainer');

                if (container) {
                    if (target === 'all') {
                        container.classList.remove('single-category');
                    } else {
                        container.classList.add('single-category');
                    }

                    // Show/hide columns based on filter
                    document.querySelectorAll('.column').forEach(col => {
                        const cat = col.getAttribute('data-category');
                        if (target === 'all' || target === cat) {
                            col.classList.remove('hidden');
                        } else {
                            col.classList.add('hidden');
                        }
                    });
                }
            });
        });
    }

    // Setup profile dropdown
    setupProfileDropdown() {
        if (this.profileIcon && this.profileDropdown) {
            this.profileIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                this.profileDropdown.classList.toggle('active');
            });
            
            document.addEventListener('click', () => {
                this.profileDropdown.classList.remove('active');
            });
        }
    }
    
    // Setup search toggle
    setupSearchToggle() {
        const searchWrapper = document.getElementById('searchWrapper');
        const searchIcon = document.querySelector('.search-icon');
        const searchInput = document.getElementById('searchInput');
        
        if (searchWrapper && searchIcon && searchInput) {
            searchWrapper.classList.add('collapsed');
            
            searchIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                searchWrapper.classList.toggle('collapsed');
                if (!searchWrapper.classList.contains('collapsed')) {
                    searchInput.focus();
                }
            });
            
            document.addEventListener('click', (e) => {
                if (!searchWrapper.contains(e.target)) {
                    searchWrapper.classList.add('collapsed');
                }
            });
        }
    }
}

// Initialize base functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LocalConnectBase();
});
// Global profile functions
function viewProfile() {
    window.location.href = '/customer/profile';
}

function editProfile() {
    alert('✏️ Edit Profile\n\nProfile editing feature will be available soon!\nYou will be able to update your personal information, preferences, and settings.');
}

function myOrders() {
    window.location.href = '/customer/orders';
}
function logout() {
    // Clear any local storage or session storage
    if (typeof(Storage) !== "undefined") {
        localStorage.clear();
        sessionStorage.clear();
    }
    
    // Redirect to logout endpoint
    window.location.href = '/logout';
}