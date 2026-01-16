/**
 * Menu Management JavaScript
 * Handles add, edit, delete, and toggle functionality for menu items
 */

let currentEditId = null;
let currentDeleteId = null;

document.addEventListener('DOMContentLoaded', () => {
    // File input preview functionality
    const fileInput = document.getElementById('itemImage');
    const imagePreview = document.getElementById('imagePreview');
    const fileText = document.querySelector('.file-text');

    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
                    fileText.textContent = file.name;
                };
                reader.readAsDataURL(file);
            } else {
                imagePreview.innerHTML = '';
                fileText.textContent = 'Choose photo from device';
            }
        });
    }

    // Form submission handling
    const itemForm = document.getElementById('itemForm');
    if (itemForm) {
        itemForm.addEventListener('submit', handleFormSubmit);
    }

    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        const modal = document.getElementById('itemModal');
        const deleteModal = document.getElementById('deleteModal');
        
        if (event.target === modal) {
            closeModal();
        }
        if (event.target === deleteModal) {
            closeDeleteModal();
        }
    });
});

// Open Add Modal
function openAddModal() {
    currentEditId = null;
    const modal = document.getElementById('itemModal');
    const form = document.getElementById('itemForm');
    const modalTitle = document.getElementById('modalTitle');
    const saveBtn = document.getElementById('saveBtn');
    
    // Reset form
    form.reset();
    form.action = '/add_item';
    
    // Update modal title and button
    modalTitle.textContent = 'Add New Menu Item';
    saveBtn.innerHTML = '<i class="fa-solid fa-plus"></i> Add Item';
    
    // Clear image preview
    document.getElementById('imagePreview').innerHTML = '';
    document.querySelector('.file-text').textContent = 'Choose photo from device';
    
    // Show modal
    modal.style.display = 'block';
    
    // Focus on first input
    setTimeout(() => {
        document.getElementById('itemName').focus();
    }, 100);
}

// Open Edit Modal
function openEditModal(itemId) {
    currentEditId = itemId;
    const modal = document.getElementById('itemModal');
    const form = document.getElementById('itemForm');
    const modalTitle = document.getElementById('modalTitle');
    const saveBtn = document.getElementById('saveBtn');
    
    // Try to find menu item card first (menu page)
    let itemCard = document.querySelector(`[data-item-id="${itemId}"]`);
    
    if (itemCard) {
        // Menu page - extract from card
        const itemName = itemCard.querySelector('.item-name').textContent.trim();
        const itemDescription = itemCard.querySelector('.item-description')?.textContent.trim() || '';
        const price = itemCard.querySelector('.price').textContent.replace('₹', '').trim();
        const categoryBadge = itemCard.querySelector('.category-badge');
        const category = categoryBadge ? getCategoryValue(categoryBadge.textContent.trim()) : '';
        
        // Populate form with item data
        document.getElementById('itemName').value = itemName;
        document.getElementById('itemDescription').value = itemDescription;
        document.getElementById('itemPrice').value = price;
        document.getElementById('itemCategory').value = category;
    } else {
        // Dashboard page - extract from table row
        const editButton = document.querySelector(`button[onclick="openEditModal(${itemId})"]`);
        const tableRow = editButton ? editButton.closest('tr') : null;
        
        if (tableRow) {
            const cells = tableRow.querySelectorAll('td');
            const itemName = cells[0].textContent.trim();
            const price = cells[1].textContent.replace('₹', '').trim();
            
            // Populate form with available data
            document.getElementById('itemName').value = itemName;
            document.getElementById('itemPrice').value = price;
            
            // Clear fields not available in dashboard table
            document.getElementById('itemDescription').value = '';
            document.getElementById('itemCategory').value = '';
        }
    }
    
    // Clear image preview
    document.getElementById('imagePreview').innerHTML = '';
    document.querySelector('.file-text').textContent = 'Choose photo from device';
    
    // Update form action and modal
    form.action = `/edit_item/${itemId}`;
    modalTitle.textContent = 'Edit Menu Item';
    saveBtn.innerHTML = '<i class="fa-solid fa-save"></i> Update Item';
    
    // Show modal
    modal.style.display = 'block';
    
    // Focus on first input
    setTimeout(() => {
        document.getElementById('itemName').focus();
    }, 100);
}

// Close Modal
function closeModal() {
    const modal = document.getElementById('itemModal');
    modal.style.display = 'none';
    currentEditId = null;
}

// Handle Form Submit
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const saveBtn = document.getElementById('saveBtn');
    const originalText = saveBtn.innerHTML;
    
    // Validate form
    const name = document.getElementById('itemName').value.trim();
    const category = document.getElementById('itemCategory').value;
    const price = document.getElementById('itemPrice').value;
    
    if (!name || !category || !price) {
        alert('Please fill in all required fields.');
        return;
    }
    
    // Show loading state
    saveBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Saving...';
    saveBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Show success message
            saveBtn.innerHTML = '<i class="fa-solid fa-check"></i> Saved!';
            saveBtn.style.background = '#10b981';
            
            // Close modal and reload page after short delay
            setTimeout(() => {
                closeModal();
                window.location.reload();
            }, 1000);
        } else {
            throw new Error('Failed to save item');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to save item. Please try again.');
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }
}

// Toggle Item Availability
async function toggleAvailability(itemId, checkbox) {
    const originalChecked = checkbox.checked;
    
    try {
        const response = await fetch(`/toggle_item/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            // Revert checkbox if request failed
            checkbox.checked = !originalChecked;
            throw new Error('Failed to update availability');
        }
        
        // Show visual feedback
        const itemCard = checkbox.closest('.menu-item-card');
        if (itemCard) {
            if (checkbox.checked) {
                itemCard.style.opacity = '1';
            } else {
                itemCard.style.opacity = '0.7';
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to update availability. Please try again.');
    }
}

// Delete Item Functions
function deleteItem(itemId) {
    currentDeleteId = itemId;
    const deleteModal = document.getElementById('deleteModal');
    deleteModal.style.display = 'block';
    
    // Set up delete confirmation
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    confirmBtn.onclick = () => confirmDelete(itemId);
}

function closeDeleteModal() {
    const deleteModal = document.getElementById('deleteModal');
    deleteModal.style.display = 'none';
    currentDeleteId = null;
}

async function confirmDelete(itemId) {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const originalText = confirmBtn.innerHTML;
    
    // Show loading state
    confirmBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Deleting...';
    confirmBtn.disabled = true;
    
    try {
        const response = await fetch(`/delete_item/${itemId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Show success state
            confirmBtn.innerHTML = '<i class="fa-solid fa-check"></i> Deleted!';
            confirmBtn.style.background = '#10b981';
            
            // Close modal and reload page
            setTimeout(() => {
                closeDeleteModal();
                window.location.reload();
            }, 1000);
        } else {
            throw new Error('Failed to delete item');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to delete item. Please try again.');
        confirmBtn.innerHTML = originalText;
        confirmBtn.disabled = false;
    }
}

// Helper function to get category value for select
function getCategoryValue(displayCategory) {
    const categoryMap = {
        'Veg': 'Veg',
        'Non-Veg': 'Non-Veg', 
        'Beverages': 'Beverages',
        'Desserts': 'Desserts',
        'Snacks': 'Snacks'
    };
    return categoryMap[displayCategory] || displayCategory;
}

// Helper function to get display category
function getDisplayCategory(value) {
    const displayMap = {
        'Veg': 'Vegetarian',
        'Non-Veg': 'Non-Vegetarian',
        'Beverages': 'Beverages',
        'Desserts': 'Desserts',
        'Snacks': 'Snacks'
    };
    return displayMap[value] || value;
}