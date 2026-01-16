/**
 * Localconnect Orders Management Logic
 * Handles real-time tab filtering and AJAX order actions
 */

document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const orderCards = document.querySelectorAll('.order-card');

    /**
     * --- 1. Tab Filtering Logic ---
     * Uses the data-status attribute to show/hide cards
     */
    function filterOrders() {
        const activeTab = document.querySelector('.tab-btn.active');
        const filterValue = activeTab.textContent.trim(); // "All", "Pending", "Completed", or "Rejected"

        orderCards.forEach(card => {
            if (card.classList.contains('empty-state')) return;

            // Get status directly from the data attribute
            const orderStatus = card.getAttribute('data-status');

            let shouldShow = false;
            
            if (filterValue === 'All') {
                shouldShow = true;
            } else if (filterValue === 'Pending') {
                shouldShow = (orderStatus === 'Pending');
            } else if (filterValue === 'Completed') {
                shouldShow = (orderStatus === 'Completed');
            } else if (filterValue === 'Rejected') {
                shouldShow = (orderStatus === 'Rejected');
            }
            
            card.style.display = shouldShow ? 'block' : 'none';
        });

        // Show empty state if no orders are visible
        const visibleCards = Array.from(orderCards).filter(card => 
            !card.classList.contains('empty-state') && card.style.display !== 'none'
        );
        
        const emptyState = document.querySelector('.empty-state');
        if (visibleCards.length === 0 && emptyState) {
            emptyState.style.display = 'block';
        } else if (emptyState) {
            emptyState.style.display = 'none';
        }
    }

    // Attach click events to tabs for instant switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            filterOrders();
        });
    });

    /**
     * --- 2. Action Button AJAX Submission ---
     * Updates database and UI without page refresh
     */
    const actionForms = document.querySelectorAll('.action-buttons-group form');
    actionForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault(); // Prevent default form submission

            const button = form.querySelector('button');
            const originalText = button.innerHTML;
            const statusValue = form.querySelector('input[name="status"]').value; // 'Accepted' or 'Rejected'
            const orderCard = form.closest('.order-card');
            const customerPhone = orderCard.querySelector('.btn-blue-call').getAttribute('href');

            // Show loading state
            button.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Processing...';
            button.disabled = true;
            button.style.opacity = '0.7';

            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    // 1. Update the data-status attribute based on the action
                    let newDataStatus;
                    if (statusValue === 'Accepted') {
                        newDataStatus = 'Completed';
                    } else if (statusValue === 'Rejected') {
                        newDataStatus = 'Rejected';
                    }
                    
                    orderCard.setAttribute('data-status', newDataStatus);

                    // 2. Replace buttons with the static status badge
                    const actionGroup = orderCard.querySelector('.action-buttons-group');
                    const statusClass = newDataStatus.toLowerCase();
                    const displayStatus = newDataStatus;
                    
                    actionGroup.innerHTML = `
                        <span class="status-badge-static ${statusClass}">${displayStatus}</span>
                        <a href="${customerPhone}" class="btn-blue-call">
                            <i class="fa-solid fa-phone"></i> Call
                        </a>
                    `;

                    // 3. Show success feedback with animation
                    orderCard.style.transform = 'scale(1.02)';
                    orderCard.style.boxShadow = '0 8px 25px rgba(16, 185, 129, 0.3)';
                    
                    setTimeout(() => {
                        orderCard.style.transform = '';
                        orderCard.style.boxShadow = '';
                    }, 500);
                    
                    // 4. Re-run filter after a short delay to update the view
                    setTimeout(() => {
                        filterOrders();
                    }, 800);

                } else {
                    throw new Error('Failed to update order');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to update order. Please try again.');
                button.innerHTML = originalText;
                button.disabled = false;
                button.style.opacity = '';
            }
        });
    });

    // Initial filter run on page load
    filterOrders();
});

// --- Modal Functions ---
function openRejectModal(orderId) {
    const modal = document.getElementById('rejectModal');
    const form = document.getElementById('rejectForm');
    
    // Set the form action to the correct order ID
    form.action = `/update_order/${orderId}`;
    
    // Clear previous rejection reason
    document.getElementById('rejectionReason').value = '';
    
    // Show modal
    modal.style.display = 'block';
    
    // Focus on textarea
    setTimeout(() => {
        document.getElementById('rejectionReason').focus();
    }, 100);
}

function closeRejectModal() {
    const modal = document.getElementById('rejectModal');
    modal.style.display = 'none';
}

// Handle rejection form submission
document.addEventListener('DOMContentLoaded', () => {
    const rejectForm = document.getElementById('rejectForm');
    if (rejectForm) {
        rejectForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = rejectForm.querySelector('.btn-reject-confirm');
            const originalText = submitBtn.innerHTML;
            const rejectionReason = document.getElementById('rejectionReason').value.trim();
            
            if (!rejectionReason) {
                alert('Please provide a reason for rejection.');
                return;
            }
            
            // Show loading state
            submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Rejecting...';
            submitBtn.disabled = true;
            
            try {
                const formData = new FormData(rejectForm);
                const response = await fetch(rejectForm.action, {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    // Find the order card and update it
                    const orderId = rejectForm.action.split('/').pop();
                    const orderCard = document.querySelector(`[data-order-id="${orderId}"]`) || 
                                    Array.from(document.querySelectorAll('.order-card')).find(card => 
                                        card.querySelector('form') && 
                                        card.querySelector('form').action.includes(orderId)
                                    );
                    
                    if (orderCard) {
                        // Update the data-status attribute
                        orderCard.setAttribute('data-status', 'Rejected');
                        
                        // Replace buttons with status badge
                        const actionGroup = orderCard.querySelector('.action-buttons-group');
                        const customerPhone = orderCard.querySelector('.btn-blue-call').getAttribute('href');
                        
                        actionGroup.innerHTML = `
                            <span class="status-badge-static rejected">
                                Rejected
                                <i class="fa-solid fa-info-circle rejection-info" title="${rejectionReason}"></i>
                            </span>
                            <a href="${customerPhone}" class="btn-blue-call">
                                <i class="fa-solid fa-phone"></i> Call
                            </a>
                        `;
                        
                        // Show success animation
                        orderCard.style.transform = 'scale(1.02)';
                        orderCard.style.boxShadow = '0 8px 25px rgba(239, 68, 68, 0.3)';
                        
                        setTimeout(() => {
                            orderCard.style.transform = '';
                            orderCard.style.boxShadow = '';
                        }, 500);
                    }
                    
                    // Close modal
                    closeRejectModal();
                    
                    // Re-run filter
                    setTimeout(() => {
                        const filterOrders = window.filterOrders;
                        if (typeof filterOrders === 'function') {
                            filterOrders();
                        }
                    }, 800);
                    
                } else {
                    throw new Error('Failed to reject order');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to reject order. Please try again.');
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        const modal = document.getElementById('rejectModal');
        if (event.target === modal) {
            closeRejectModal();
        }
    });
});