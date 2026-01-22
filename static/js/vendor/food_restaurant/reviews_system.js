/**
 * Reviews System JavaScript
 * Handles filtering, responding to reviews, and marking as helpful
 */

document.addEventListener('DOMContentLoaded', () => {
    initializeFilters();
    initializeCharacterCounters();
    initializeResponseTemplates();
});

// Initialize Filter Functionality
function initializeFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    const reviewCards = document.querySelectorAll('.review-card');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            filterBtns.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            btn.classList.add('active');
            
            const filter = btn.getAttribute('data-filter');
            filterReviews(filter, reviewCards);
        });
    });
}

// Filter Reviews Function
function filterReviews(filter, reviewCards) {
    let visibleCount = 0;
    
    reviewCards.forEach(card => {
        const rating = parseInt(card.getAttribute('data-rating'));
        const responded = card.getAttribute('data-responded') === 'true';
        const helpful = card.getAttribute('data-helpful') === 'true';
        
        let shouldShow = false;
        
        switch(filter) {
            case 'all':
                shouldShow = true;
                break;
            case '5':
                shouldShow = (rating === 5);
                break;
            case '4':
                shouldShow = (rating === 4);
                break;
            case '3':
                shouldShow = (rating === 3);
                break;
            case '2':
                shouldShow = (rating === 2);
                break;
            case '1':
                shouldShow = (rating === 1);
                break;
            case 'pending':
                shouldShow = !responded;
                break;
            case 'responded':
                shouldShow = responded;
                break;
            default:
                shouldShow = true;
        }
        
        if (shouldShow) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show empty state if no reviews are visible
    updateEmptyState(visibleCount === 0, filter);
}

// Update Empty State
function updateEmptyState(isEmpty, filter) {
    const reviewsList = document.getElementById('reviewsList');
    let emptyState = reviewsList.querySelector('.empty-state');
    
    if (isEmpty && !emptyState) {
        emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        
        let message = 'No reviews found';
        let description = 'No reviews match the selected filter criteria.';
        
        switch(filter) {
            case '5':
                message = 'No 5-Star Reviews';
                description = 'You don\\'t have any 5-star reviews yet. Keep up the great work!';
                break;
            case '4':
                message = 'No 4-Star Reviews';
                description = 'You don\\'t have any 4-star reviews yet.';
                break;
            case '3':
                message = 'No 3-Star Reviews';
                description = 'You don\\'t have any 3-star reviews yet.';
                break;
            case '2':
                message = 'No 2-Star Reviews';
                description = 'You don\\'t have any 2-star reviews yet.';
                break;
            case '1':
                message = 'No 1-Star Reviews';
                description = 'You don\\'t have any 1-star reviews yet.';
                break;
            case 'pending':
                message = 'No Pending Reviews';
                description = 'All reviews have been responded to. Great job!';
                break;
            case 'responded':
                message = 'No Responded Reviews';
                description = 'You haven\\'t responded to any reviews yet.';
                break;
        }
        
        emptyState.innerHTML = `
            <i class="fa-solid fa-filter"></i>
            <h4>${message}</h4>
            <p>${description}</p>
        `;
        reviewsList.appendChild(emptyState);
    } else if (!isEmpty && emptyState) {
        emptyState.remove();
    }
}

// Open Response Box
function openResponseBox(reviewId) {
    const responseBox = document.getElementById(`responseBox${reviewId}`);
    const respondBtn = responseBox.previousElementSibling;
    
    // Hide the respond button and show the response box
    respondBtn.style.display = 'none';
    responseBox.style.display = 'block';
    
    // Focus on the textarea
    const textarea = document.getElementById(`responseText${reviewId}`);
    setTimeout(() => {
        textarea.focus();
    }, 100);
    
    // Auto-populate response based on rating
    const reviewCard = responseBox.closest('.review-card');
    const rating = parseInt(reviewCard.getAttribute('data-rating'));
    
    let autoResponse = '';
    if (rating >= 4) {
        autoResponse = "Thank you so much for your wonderful review! We're delighted that you enjoyed your experience with us. Your feedback means a lot to our team, and we look forward to serving you again soon!";
    } else if (rating === 3) {
        autoResponse = "Thank you for your honest feedback. We truly appreciate you taking the time to share your experience with us. We're always working to improve our service, and your comments help us do better.";
    } else {
        autoResponse = "We sincerely apologize for not meeting your expectations. Your feedback is very important to us, and we take all concerns seriously. We would love the opportunity to make things right.";
    }
    
    textarea.value = autoResponse;
    updateCharacterCount(reviewId, autoResponse.length);
}

// Close Response Box
function closeResponseBox(reviewId) {
    const responseBox = document.getElementById(`responseBox${reviewId}`);
    const respondBtn = responseBox.previousElementSibling;
    
    // Show the respond button and hide the response box
    respondBtn.style.display = 'flex';
    responseBox.style.display = 'none';
    
    // Clear the textarea
    const textarea = document.getElementById(`responseText${reviewId}`);
    textarea.value = '';
    updateCharacterCount(reviewId, 0);
}

// Submit Response
async function submitResponse(event, reviewId) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('.btn-submit-response');
    const originalText = submitBtn.innerHTML;
    const textarea = document.getElementById(`responseText${reviewId}`);
    const responseText = textarea.value.trim();
    
    if (!responseText) {
        showMessage('Please enter a response.', 'error');
        return;
    }
    
    if (responseText.length > 500) {
        showMessage('Response must be 500 characters or less.', 'error');
        return;
    }
    
    // Show loading state
    submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Sending...';
    submitBtn.disabled = true;
    
    try {
        // Simulate API call (replace with actual endpoint)
        const response = await fetch(`/api/reviews/${reviewId}/respond`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                response: responseText
            })
        });
        
        if (response.ok) {
            // Show success state
            submitBtn.innerHTML = '<i class="fa-solid fa-check"></i> Sent!';
            submitBtn.style.background = '#10b981';
            
            showMessage('Response sent successfully!', 'success');
            
            // Update the review card to show the response
            setTimeout(() => {
                updateReviewCardWithResponse(reviewId, responseText);
            }, 1000);
            
        } else {
            throw new Error('Failed to send response');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Failed to send response. Please try again.', 'error');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Update Review Card with Response
function updateReviewCardWithResponse(reviewId, responseText) {
    const reviewCard = document.querySelector(`[data-review-id="${reviewId}"]`);
    const pendingActions = reviewCard.querySelector('.pending-response-actions');
    
    // Update data attribute
    reviewCard.setAttribute('data-responded', 'true');
    
    // Create response HTML
    const responseHTML = `
        <div class="shop-response">
            <div class="response-header">
                <i class="fa-solid fa-reply"></i>
                <span class="response-label">Shop Response</span>
                <span class="response-date">${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
            </div>
            <div class="response-content">
                <p class="response-text">${responseText}</p>
            </div>
            <div class="response-actions">
                <button class="btn-edit-response" onclick="editResponse(${reviewId})">
                    <i class="fa-solid fa-pen"></i> Edit Response
                </button>
                <button class="btn-mark-helpful" onclick="markAsHelpful(${reviewId}, this)">
                    <i class="fa-regular fa-heart"></i> Mark as Helpful
                </button>
            </div>
        </div>
    `;
    
    // Replace pending actions with response
    pendingActions.outerHTML = responseHTML;
}

// Mark as Helpful
function markAsHelpful(reviewId, buttonElement) {
    const reviewCard = buttonElement.closest('.review-card');
    
    // Update data attribute
    reviewCard.setAttribute('data-helpful', 'true');
    
    // Replace button with helpful status
    const helpfulHTML = `
        <div class="helpful-status">
            <i class="fa-solid fa-heart"></i>
            <span>Thank you very much!</span>
        </div>
    `;
    
    buttonElement.outerHTML = helpfulHTML;
    
    // Show success message with heart emoji
    showMessage('❤️ Thank you! Review marked as helpful!', 'success');
    
    // Add a nice animation to the review card
    reviewCard.style.transform = 'scale(1.02)';
    reviewCard.style.boxShadow = '0 8px 30px rgba(220, 38, 38, 0.2)';
    
    setTimeout(() => {
        reviewCard.style.transform = '';
        reviewCard.style.boxShadow = '';
    }, 500);
}

// Edit Response (placeholder)
function editResponse(reviewId) {
    showMessage('Edit response functionality would be implemented here.', 'info');
}

// Use Template Response
function useTemplate(reviewId, templateType) {
    const textarea = document.getElementById(`responseText${reviewId}`);
    
    const templates = {
        thank: "Thank you so much for your wonderful review! We're delighted that you enjoyed your experience with us. Your feedback means a lot to our team, and we look forward to serving you again soon!",
        improve: "Thank you for your honest feedback. We truly appreciate you taking the time to share your experience with us. We're always working to improve our service, and your comments help us do better. We hope to have the opportunity to serve you again and provide you with an even better experience.",
        apologize: "We sincerely apologize for not meeting your expectations. Your feedback is very important to us, and we take all concerns seriously. We would love the opportunity to make things right and improve your experience. Please feel free to contact us directly so we can address your concerns properly."
    };
    
    if (templates[templateType]) {
        textarea.value = templates[templateType];
        updateCharacterCount(reviewId, templates[templateType].length);
        
        // Trigger input event to update character count styling
        textarea.dispatchEvent(new Event('input'));
    }
}

// Initialize Character Counters
function initializeCharacterCounters() {
    document.addEventListener('input', (e) => {
        if (e.target.classList.contains('response-input')) {
            const reviewId = e.target.id.replace('responseText', '');
            updateCharacterCount(reviewId, e.target.value.length);
        }
    });
}

// Update Character Count
function updateCharacterCount(reviewId, count) {
    const charCountElement = document.getElementById(`charCount${reviewId}`);
    if (charCountElement) {
        charCountElement.textContent = count;
        
        // Change color based on character count
        if (count > 450) {
            charCountElement.style.color = '#ef4444';
        } else if (count > 400) {
            charCountElement.style.color = '#f59e0b';
        } else {
            charCountElement.style.color = '#666';
        }
    }
}

// Initialize Response Templates
function initializeResponseTemplates() {
    // Template buttons are handled by onclick attributes in HTML
    // This function can be used for additional template initialization if needed
}

// Show Message
function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('messageContainer');
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    messageElement.textContent = message;
    
    messageContainer.appendChild(messageElement);
    
    // Animate in
    setTimeout(() => {
        messageElement.classList.add('show');
    }, 100);
    
    // Remove after 4 seconds
    setTimeout(() => {
        messageElement.classList.remove('show');
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 300);
    }, 4000);
}

// Utility function to format date
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}