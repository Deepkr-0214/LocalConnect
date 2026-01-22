"""
Script to generate JavaScript files for all vendor categories
"""

categories = {
    'electronics': {
        'subcategories': ['mobiles', 'home-appliances', 'kitchen-appliances'],
        'subcategory_map': {
            'Mobiles': 'mobiles',
            'Home Appliances': 'home-appliances',
            'Kitchen Appliances': 'kitchen-appliances'
        },
        'default_emoji': '📱',
        'class_name': 'ElectronicsPage'
    },
    'fashion': {
        'subcategories': ['ladies', 'gents', 'boy', 'girl'],
        'subcategory_map': {
            'Ladies': 'ladies',
            'Gents': 'gents',
            'Boy': 'boy',
            'Girl': 'girl'
        },
        'default_emoji': '👗',
        'class_name': 'FashionPage'
    },
    'grocery': {
        'subcategories': ['vegetables', 'dairy-eggs', 'general-store', 'fruits'],
        'subcategory_map': {
            'Vegetables': 'vegetables',
            'Dairy & Eggs': 'dairy-eggs',
            'General Store': 'general-store',
            'Fruits': 'fruits'
        },
        'default_emoji': '🛒',
        'class_name': 'GroceryPage'
    },
    'pharmacy': {
        'subcategories': ['ayurvedic', 'chemist', 'baby'],
        'subcategory_map': {
            'Ayurvedic Medicine': 'ayurvedic',
            'Chemist & Drug Medicine': 'chemist',
            'Baby Medicine': 'baby'
        },
        'default_emoji': '💊',
        'class_name': 'PharmacyPage'
    }
}

js_template = """/**
 * {title} Page JavaScript
 */

class {class_name} {{
    constructor() {{
        this.vendors = this.loadVendors();
        this.filteredVendors = [...this.vendors];
        this.init();
    }}

    loadVendors() {{
        const categoryMap = {category_map};

        const vendors = vendorsFromServer.map(v => ({{
            id: v.id,
            name: v.name,
            category: categoryMap[v.subcategory] || '{default_subcategory}',
            rating: v.rating || 0,
            reviews: v.review_count || 0,
            distance: 'Getting location...',
            image: v.shop_image || '{default_emoji}',
            cuisine: v.subcategory,
            priceRange: `₹${{v.min_price}}-${{v.max_price}}`,
            deliveryTime: '15-30 min',
            isOpen: v.is_open,
            latitude: v.latitude,
            longitude: v.longitude
        }}));

        const calculateDistances = (userLat, userLon) => {{
            vendors.forEach(vendor => {{
                if (vendor.latitude && vendor.longitude) {{
                    const distance = this.calculateDistance(userLat, userLon, vendor.latitude, vendor.longitude);
                    vendor.distance = distance.toFixed(1) + ' km';
                }} else {{
                    vendor.distance = 'N/A';
                }}
            }});
            vendors.sort((a, b) => {{
                const distA = parseFloat(a.distance) || 999;
                const distB = parseFloat(b.distance) || 999;
                return distA - distB;
            }});
            this.vendors = vendors;
            this.filteredVendors = [...this.vendors];
            this.renderVendors();
        }};

        if (customerStoredLat && customerStoredLon) {{
            calculateDistances(customerStoredLat, customerStoredLon);
        }}

        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    calculateDistances(position.coords.latitude, position.coords.longitude);
                }},
                (error) => {{
                    if (!customerStoredLat && !customerStoredLon) {{
                        vendors.forEach(vendor => {{ vendor.distance = 'Location disabled'; }});
                        this.vendors = vendors;
                        this.filteredVendors = [...this.vendors];
                        this.renderVendors();
                    }}
                }}
            );
        }} else if (!customerStoredLat && !customerStoredLon) {{
            vendors.forEach(vendor => {{ vendor.distance = 'Location unavailable'; }});
            this.vendors = vendors;
            this.filteredVendors = [...this.vendors];
            this.renderVendors();
        }}

        return vendors;
    }}

    calculateDistance(lat1, lon1, lat2, lon2) {{
        const R = 6371;
        const dLat = this.toRadians(lat2 - lat1);
        const dLon = this.toRadians(lon2 - lon1);
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }}

    toRadians(degrees) {{ return degrees * (Math.PI / 180); }}

    init() {{
        this.renderVendors();
        this.setupFilters();
        this.setupSearch();
    }}

    renderVendors() {{
{render_lists}
        const sortByDistance = (a, b) => {{
            const distA = parseFloat(a.distance) || 999;
            const distB = parseFloat(b.distance) || 999;
            return distA - distB;
        }};

{sort_and_render}
    }}

    createVendorCard(vendor) {{
        const card = document.createElement('div');
        card.className = 'vendor-card';
        card.onclick = () => this.viewVendorDetails(vendor.id);

        const isEmoji = /\\p{{Emoji}}/u.test(vendor.image) && vendor.image.length < 10;
        const isBase64 = vendor.image && vendor.image.startsWith('data:image');

        let imageHtml;
        if (isEmoji) {{
            imageHtml = `<div style="font-size:80px;display:flex;align-items:center;justify-content:center;height:100%;">${{vendor.image}}</div>`;
        }} else if (isBase64) {{
            imageHtml = `<img src="${{vendor.image}}" alt="${{vendor.name}}">`;
        }} else {{
            imageHtml = `<div style="font-size:80px;display:flex;align-items:center;justify-content:center;height:100%;">{default_emoji}</div>`;
        }}

        card.innerHTML = `
            <div class="vendor-image">
                ${{imageHtml}}
                <div class="status-badge ${{vendor.isOpen ? 'open' : 'closed'}}">
                    ${{vendor.isOpen ? 'Open' : 'Closed'}}
                </div>
            </div>
            <div class="vendor-info">
                <h3>${{vendor.name}}</h3>
                <p class="cuisine">${{vendor.cuisine}}</p>
                <div class="vendor-meta">
                    <div class="rating">
                        <i class="fas fa-star"></i>
                        <span>${{vendor.rating}}</span>
                        <span class="reviews">(${{vendor.reviews}})</span>
                    </div>
                    <div class="distance">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${{vendor.distance}}</span>
                    </div>
                </div>
                <div class="vendor-details">
                    <span class="price-range">${{vendor.priceRange}}</span>
                    <span class="delivery-time">
                        <i class="fas fa-clock"></i>
                        ${{vendor.deliveryTime}}
                    </span>
                </div>
            </div>
        `;
        return card;
    }}

    setupFilters() {{
        const filterBtns = document.querySelectorAll('.filter-btn');
        const mainContainer = document.getElementById('mainContainer');

        filterBtns.forEach(btn => {{
            btn.addEventListener('click', () => {{
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const target = btn.getAttribute('data-target');

                if (target === 'all') {{
                    this.filteredVendors = [...this.vendors];
                    if (mainContainer) mainContainer.classList.remove('single-category');
                }} else {{
                    this.filteredVendors = this.vendors.filter(vendor => vendor.category === target);
                    if (mainContainer) mainContainer.classList.add('single-category');
                }}

                document.querySelectorAll('.column').forEach(col => {{
                    const cat = col.getAttribute('data-category');
                    if (target === 'all' || target === cat) {{
                        col.classList.remove('hidden');
                    }} else {{
                        col.classList.add('hidden');
                    }}
                }});

                this.renderVendors();
            }});
        }});
    }}

    setupSearch() {{
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {{
            searchInput.addEventListener('input', (e) => {{
                const term = e.target.value.toLowerCase();
                this.filteredVendors = this.vendors.filter(vendor =>
                    vendor.name.toLowerCase().includes(term) ||
                    vendor.cuisine.toLowerCase().includes(term)
                );
                this.renderVendors();
            }});
        }}
    }}

    viewVendorDetails(vendorId) {{
        window.location.href = `/customer/vendor/${{vendorId}}`;
    }}
}}

document.addEventListener('DOMContentLoaded', () => {{
    new {class_name}();
}});
"""

for category, config in categories.items():
    # Build category map
    category_map_str = "{\n"
    for key, value in config['subcategory_map'].items():
        category_map_str += f"            '{key}': '{value}',\n"
    category_map_str += "        }"

    # Build render lists
    render_lists = ""
    for subcat in config['subcategories']:
        var_name = subcat.replace('-', '_')
        render_lists += f"        const {var_name}List = document.getElementById('{subcat}-list');\n"
    
    render_lists += "\n"
    for subcat in config['subcategories']:
        var_name = subcat.replace('-', '_')
        render_lists += f"        if ({var_name}List) {var_name}List.innerHTML = '';\n"
    
    render_lists += "\n"
    for subcat in config['subcategories']:
        var_name = subcat.replace('-', '_')
        render_lists += f"        const {var_name}Vendors = this.filteredVendors.filter(v => v.category === '{subcat}');\n"

    # Build sort and render
    sort_and_render = ""
    for subcat in config['subcategories']:
        var_name = subcat.replace('-', '_')
        sort_and_render += f"        {var_name}Vendors.sort(sortByDistance);\n"
    
    sort_and_render += "\n"
    for subcat in config['subcategories']:
        var_name = subcat.replace('-', '_')
        sort_and_render += f"        {var_name}Vendors.forEach(vendor => {{\n"
        sort_and_render += f"            if ({var_name}List) {var_name}List.appendChild(this.createVendorCard(vendor));\n"
        sort_and_render += f"        }});\n"

    # Generate JS content
    js_content = js_template.format(
        title=category.capitalize(),
        class_name=config['class_name'],
        category_map=category_map_str,
        default_subcategory=config['subcategories'][0],
        default_emoji=config['default_emoji'],
        render_lists=render_lists,
        sort_and_render=sort_and_render
    )

    # Write to file
    with open(f'd:/Hackathon/LocalConnect/static/js/customer/{category}.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"Created {category}.js")

print("All JavaScript files created successfully!")
