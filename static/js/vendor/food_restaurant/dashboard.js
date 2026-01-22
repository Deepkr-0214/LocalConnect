/**
 * Localconnect Dashboard Logic
 * Handles real-time order actions and menu toggles
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("Localconnect Dashboard Fully Loaded");
    
    // Initializing Order Card Animations for a smooth entrance
    const cards = document.querySelectorAll('.order-action-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });

    // Optional: Log hover events for the Edit tooltips
    const editIcons = document.querySelectorAll('.action-dots-wrapper');
    editIcons.forEach(icon => {
        icon.addEventListener('mouseenter', () => {
            console.log("User hovering over Edit action");
        });
    });
});

/**
 * Update Order Status (Accept/Reject)
 * Sends a request to the server and provides immediate UI feedback
 */
function updateOrderStatus(orderId, newStatus) {
    // Visual feedback for the console
    console.log(`Updating Order #${orderId} to ${newStatus}...`);

    fetch(`/update_order/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => {
        if (response.ok) {
            // Find the specific card to apply visual feedback
            const btn = window.event.target;
            const card = btn.closest('.order-action-card');
            
            // Fade out the card to show it has been processed
            if (card) {
                card.style.opacity = '0.5';
                card.style.pointerEvents = 'none';
                card.style.transition = '0.3s';
            }
            
            // Small notification to confirm success
            console.log(`Order #${orderId} ${newStatus} successfully.`);
        } else {
            alert("Failed to update order. Please try again.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("An error occurred. Check your connection.");
    });
}

/**
 * Toggle Menu Item Availability
 * Triggered when the switch in the Menu Management table is toggled
 */
function toggleItemAvailability(itemId, isChecked) {
    const statusLabel = isChecked ? 'Available' : 'Unavailable';
    
    fetch(`/toggle_menu/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ available: isChecked })
    })
    .then(response => {
        if (!response.ok) {
            // Revert switch if backend update fails
            window.event.target.checked = !isChecked;
            alert("Could not update availability.");
        } else {
            console.log(`Menu Item #${itemId} is now ${statusLabel}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Revert switch on network error
        window.event.target.checked = !isChecked;
    });
}

/**
 * Navigation Helper
 * Redirects user to specific pages from "View All" links
 */
function navigateTo(url) {
    window.location.href = url;
}