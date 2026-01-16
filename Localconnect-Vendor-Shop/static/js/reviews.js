document.addEventListener('DOMContentLoaded', () => {
    // No initialization needed for simple functionality
});

// Toggle response box
function toggleResponseBox(reviewId) {
    const responseBox = document.getElementById('responseBox' + reviewId);
    const isVisible = responseBox.style.display === 'block';
    
    if (isVisible) {
        responseBox.style.display = 'none';
        document.getElementById('responseText' + reviewId).value = '';
    } else {
        responseBox.style.display = 'block';
        setTimeout(() => {
            document.getElementById('responseText' + reviewId).focus();
        }, 100);
    }
}

// Submit response
function submitResponse(event, reviewId) {
    event.preventDefault();
    const textarea = document.getElementById('responseText' + reviewId);
    const responseText = textarea.value.trim();
    
    if (!responseText) {
        alert('Please enter a response.');
        return;
    }
    
    const formData = new FormData();
    formData.append('response', responseText);
    
    fetch(`/respond_review/${reviewId}`, {
        method: 'POST',
        body: formData
    }).then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Failed to send response. Please try again.');
        }
    }).catch(error => {
        console.error('Error:', error);
        alert('Failed to send response. Please try again.');
    });
}

// Use template response
function useTemplate(reviewId, type) {
    const textarea = document.getElementById('responseText' + reviewId);
    const templates = {
        thank: "Thank you so much for your wonderful review! We're delighted that you enjoyed your experience with us.",
        improve: "Thank you for your feedback. We're always working to improve our service and your comments help us do better.",
        apologize: "We sincerely apologize for not meeting your expectations. We would love the opportunity to make things right."
    };
    
    if (templates[type]) {
        textarea.value = templates[type];
        textarea.focus();
    }
}

// Edit response (fully functional)
function editResponse(reviewId) {
    const responseContent = document.getElementById('responseContent' + reviewId);
    const editForm = document.getElementById('editForm' + reviewId);
    const textarea = document.getElementById('editText' + reviewId);
    
    responseContent.style.display = 'none';
    editForm.style.display = 'block';
    textarea.focus();
}

// Cancel edit
function cancelEdit(reviewId) {
    const responseContent = document.getElementById('responseContent' + reviewId);
    const editForm = document.getElementById('editForm' + reviewId);
    const textarea = document.getElementById('editText' + reviewId);
    const originalText = responseContent.querySelector('.response-text').textContent;
    
    textarea.value = originalText;
    editForm.style.display = 'none';
    responseContent.style.display = 'block';
}

// Save edit
function saveEdit(reviewId) {
    const textarea = document.getElementById('editText' + reviewId);
    const newResponse = textarea.value.trim();
    
    if (!newResponse) {
        alert('Response cannot be empty.');
        return;
    }
    
    const formData = new FormData();
    formData.append('response', newResponse);
    
    fetch(`/edit_response/${reviewId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the displayed response
            const responseText = document.querySelector(`#responseContent${reviewId} .response-text`);
            const responseDate = document.querySelector(`#responseContent${reviewId}`).closest('.shop-response').querySelector('.response-date');
            
            responseText.textContent = data.response;
            responseDate.textContent = data.date;
            
            // Hide edit form and show response
            document.getElementById('editForm' + reviewId).style.display = 'none';
            document.getElementById('responseContent' + reviewId).style.display = 'block';
        } else {
            alert('Failed to update response. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to update response. Please try again.');
    });
}

// Mark as helpful (placeholder function)
function markHelpful(reviewId) {
    const button = event.target.closest('.btn-helpful');
    button.innerHTML = '<i class="fa-solid fa-heart"></i> Thank you!';
    button.style.background = '#dc2626';
    button.style.color = 'white';
    button.disabled = true;
}