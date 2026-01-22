"""
Category-specific labels and terminology for vendor dashboards.
This module provides a centralized way to get category-appropriate labels
for different vendor types (Food & Restaurant, Garage, Electronics, etc.)
"""

# Complete category labels mapping
CATEGORY_LABELS = {
    'Food & Restaurant': {
        'inventory': 'Menu',
        'inventory_plural': 'Menu Items',
        'item': 'Menu Item',
        'item_plural': 'Menu Items',
        'add_item': 'Add Menu Item',
        'edit_item': 'Edit Menu Item',
        'delete_item': 'Delete Menu Item',
        'category_field': 'Category',
        'categories': ['Veg', 'Non-Veg', 'Beverages', 'Desserts', 'Snacks'],
        'item_name_label': 'Item Name',
        'item_description_label': 'Description',
        'price_label': 'Price',
        'icon': 'fa-utensils',
        'dashboard_title': 'Restaurant Dashboard'
    },
    'Garage': {
        'inventory': 'Services',
        'inventory_plural': 'Services',
        'item': 'Service',
        'item_plural': 'Services',
        'add_item': 'Add Service',
        'edit_item': 'Edit Service',
        'delete_item': 'Delete Service',
        'category_field': 'Vehicle Type',
        'categories': ['2-Wheeler', '3-Wheeler', '4-Wheeler', 'General Service'],
        'item_name_label': 'Service Name',
        'item_description_label': 'Service Description',
        'price_label': 'Service Charge',
        'icon': 'fa-wrench',
        'dashboard_title': 'Garage Dashboard'
    },
    'Electronics': {
        'inventory': 'Products',
        'inventory_plural': 'Products',
        'item': 'Product',
        'item_plural': 'Products',
        'add_item': 'Add Product',
        'edit_item': 'Edit Product',
        'delete_item': 'Delete Product',
        'category_field': 'Product Type',
        'categories': ['Mobiles', 'Home Appliances', 'Kitchen Appliances', 'Accessories', 'Computers'],
        'item_name_label': 'Product Name',
        'item_description_label': 'Product Description',
        'price_label': 'Price',
        'icon': 'fa-mobile-screen-button',
        'dashboard_title': 'Electronics Dashboard'
    },
    'Fashion': {
        'inventory': 'Products',
        'inventory_plural': 'Products',
        'item': 'Product',
        'item_plural': 'Products',
        'add_item': 'Add Product',
        'edit_item': 'Edit Product',
        'delete_item': 'Delete Product',
        'category_field': 'Category',
        'categories': ['Ladies', 'Gents', 'Boy', 'Girl', 'Accessories'],
        'item_name_label': 'Product Name',
        'item_description_label': 'Product Description',
        'price_label': 'Price',
        'icon': 'fa-shirt',
        'dashboard_title': 'Fashion Store Dashboard'
    },
    'Grocery': {
        'inventory': 'Products',
        'inventory_plural': 'Products',
        'item': 'Product',
        'item_plural': 'Products',
        'add_item': 'Add Product',
        'edit_item': 'Edit Product',
        'delete_item': 'Delete Product',
        'category_field': 'Category',
        'categories': ['Vegetables', 'Fruits', 'Dairy & Eggs', 'General Store', 'Beverages'],
        'item_name_label': 'Product Name',
        'item_description_label': 'Product Description',
        'price_label': 'Price',
        'icon': 'fa-basket-shopping',
        'dashboard_title': 'Grocery Store Dashboard'
    },
    'Pharmacy': {
        'inventory': 'Medicines',
        'inventory_plural': 'Medicines',
        'item': 'Medicine',
        'item_plural': 'Medicines',
        'add_item': 'Add Medicine',
        'edit_item': 'Edit Medicine',
        'delete_item': 'Delete Medicine',
        'category_field': 'Medicine Type',
        'categories': ['Ayurvedic Medicine', 'Chemist & Drug Medicine', 'Baby Medicine', 'General Medicine'],
        'item_name_label': 'Medicine Name',
        'item_description_label': 'Medicine Description',
        'price_label': 'Price',
        'icon': 'fa-pills',
        'dashboard_title': 'Pharmacy Dashboard'
    }
}


def get_category_labels(category):
    """
    Get category-specific labels for a vendor category.
    
    Args:
        category (str): The vendor's business category
        
    Returns:
        dict: Dictionary containing all category-specific labels
    """
    # Default to Food & Restaurant if category not found
    return CATEGORY_LABELS.get(category, CATEGORY_LABELS['Food & Restaurant'])


def get_inventory_label(category):
    """Get the inventory label for a category (e.g., 'Menu', 'Services', 'Products')"""
    labels = get_category_labels(category)
    return labels['inventory']


def get_inventory_plural_label(category):
    """Get the plural inventory label for a category"""
    labels = get_category_labels(category)
    return labels['inventory_plural']


def get_item_label(category):
    """Get the singular item label for a category"""
    labels = get_category_labels(category)
    return labels['item']


def get_item_plural_label(category):
    """Get the plural item label for a category"""
    labels = get_category_labels(category)
    return labels['item_plural']


def get_categories_list(category):
    """Get the list of subcategories for a category"""
    labels = get_category_labels(category)
    return labels['categories']


def get_icon(category):
    """Get the Font Awesome icon class for a category"""
    labels = get_category_labels(category)
    return labels['icon']
