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

        // Chat Elements
        this.chatWindow = document.getElementById('chatWindow');
        this.chatCloseBtn = document.getElementById('chatCloseBtn');
        this.chatSendBtn = document.getElementById('chatSendBtn');
        this.chatInput = document.getElementById('chatInput');
        this.chatMessages = document.getElementById('chatMessages');
    }

    // Setup common event listeners
    setupEventListeners() {
        // Chat functionality
        if (this.chatBtn) {
            this.chatBtn.addEventListener('click', () => this.toggleChat());
        }

        if (this.chatCloseBtn) {
            this.chatCloseBtn.addEventListener('click', () => this.toggleChat());
        }

        if (this.chatSendBtn) {
            this.chatSendBtn.addEventListener('click', () => this.sendMessage());
        }

        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
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

    // Toggle Chat Window
    toggleChat() {
        if (this.chatWindow) {
            this.chatWindow.classList.toggle('active');
            if (this.chatWindow.classList.contains('active')) {
                if (this.chatInput) this.chatInput.focus();
                // Placeholder is visible by default via CSS/HTML
            }
        } else {
            alert("Chat feature is initializing...");
        }
    }

    // Send Message
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;

        // Display User Message
        this.displayMessage('user', message);
        this.chatInput.value = '';

        // Show typing indicator (optional, or just wait)

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            // Display Bot Response
            // Display Bot Response
            if (data.reply) {
                this.displayMessage('bot', data.reply, data.buttons);
            }

            // Handle Payment Requirement from Chatbot
            if (data.payment_required && data.order_id) {
                this.initiateRazorpayPayment(data.order_id);
            }

            // Check for Agent Handoff
            if (data.handoff) {
                setTimeout(() => {
                    // Close custom chat
                    this.toggleChat();

                    // Hide LocalConnect Button (Clean Swap) - DISABLED to prevent vanishing
                    // if (this.chatBtn) this.chatBtn.style.display = 'none';

                    // Start Dynamic Load of Tawk
                    if (typeof startTawkSupport === 'function') {
                        startTawkSupport();
                    } else {
                        // Fallback if function missing
                        if (window.Tawk_API) {
                            window.Tawk_API.maximize();
                        } else {
                            alert("⚠️ Support system updating. Please reload.");
                            if (this.restoreChatAfterHandoff) this.restoreChatAfterHandoff();
                        }
                    }
                }, 1500); // Small delay to let user read the message
            }

            if (data.error) {
                this.displayMessage('bot', 'Sorry, something went wrong: ' + data.error);
            }

        } catch (error) {
            console.error('Chat Error:', error);
            this.displayMessage('bot', 'Sorry, I am having trouble connecting right now. Please try again.');
        }
    }

    // Send Silent Message (System Commands)
    async sendSilentMessage(message) {
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            const data = await response.json();

            // Display Bot Response only (User msg is hidden)
            if (data.reply) {
                this.displayMessage('bot', data.reply, data.buttons);
            }
        } catch (error) {
            console.error('Silent Chat Error:', error);
        }
    }

    // Display Message
    displayMessage(sender, text, buttons = null) {
        if (!this.chatMessages) return;

        // Hide placeholder if present
        const placeholder = document.getElementById('chatPlaceholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }

        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message');
        msgDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        msgDiv.innerHTML = text; // Allow HTML for bolding/lists

        this.chatMessages.appendChild(msgDiv);

        // Render Buttons if available
        if (sender === 'bot' && buttons && buttons.length > 0) {
            const btnContainer = document.createElement('div');
            btnContainer.classList.add('chat-options');

            buttons.forEach(btn => {
                const button = document.createElement('button');
                button.classList.add('chat-option-btn');
                button.innerText = btn.text;
                button.onclick = () => {
                    this.chatInput.value = btn.value;
                    this.sendMessage();
                };
                btnContainer.appendChild(button);
            });
            this.chatMessages.appendChild(btnContainer);
        }

        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    // Generate star rating HTML
    generateStars(rating, size = 12) {
        let stars = "";
        for (let i = 0; i < 5; i++) {
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
    // Initiate Razorpay Payment from Chatbot
    async initiateRazorpayPayment(orderId) {
        try {
            // Get Razorpay Options
            const response = await fetch('/api/payment/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_id: orderId })
            });

            const paymentData = await response.json();
            if (paymentData.error) {
                this.displayMessage('bot', '❌ Error initiating payment: ' + paymentData.error);
                return;
            }

            // Define options
            const options = {
                "key": paymentData.razorpay_key_id,
                "amount": paymentData.amount,
                "currency": "INR",
                "name": "LocalConnect",
                "description": "Chat Order Payment",
                "order_id": paymentData.razorpay_order_id,
                "handler": async (response) => {
                    // Verify payment
                    try {
                        const verifyRes = await fetch('/api/payment/verify', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                order_id: orderId,
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_signature: response.razorpay_signature
                            })
                        });
                        const verifyData = await verifyRes.json();

                        if (verifyData.success) {
                            this.displayMessage('bot', '✅ Payment Successful! Your order has been placed.');
                        } else {
                            this.displayMessage('bot', '❌ Payment Verification Failed: ' + (verifyData.error || 'Unknown error'));
                        }
                    } catch (e) {
                        this.displayMessage('bot', '❌ Error verifying payment: ' + e.message);
                    }
                },
                "prefill": {
                    "name": paymentData.customer_name,
                    "email": paymentData.customer_email,
                    "contact": paymentData.customer_phone
                },
                "theme": { "color": "#27ae60" },
                "modal": {
                    "ondismiss": () => {
                        this.displayMessage('bot', 'ℹ️ Payment cancelled. You can retry from My Orders.');
                    }
                }
            };

            const rzp = new Razorpay(options);
            rzp.open();

        } catch (error) {
            console.error("Payment Error:", error);
            this.displayMessage('bot', '❌ Failed to start payment process.');
        }
    }

    // Restore chat after handoff
    restoreChatAfterHandoff() {
        if (this.chatWindow) {
            // Force open
            this.chatWindow.classList.add('active');
            if (this.chatInput) this.chatInput.focus();

            // Add Thank You Message
            this.displayMessage('bot', 'Thank you for using Local Connect Chatbot! 👋<br>How else can I help you today?');

            // Ensure button is visible (redundancy)
            if (this.chatBtn) this.chatBtn.style.display = 'flex';
        }
    }
}

// Initialize base functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.localConnect = new LocalConnectBase();
});

// Global functions (Legacy support & access)
function viewProfile() {
    window.location.href = '/customer/profile';
}
function changePassword() {
    window.location.href = '/customer/change-password';
}
function editProfile() {
    alert('✏️ Edit Profile\n\nProfile editing feature will be available soon!\nYou will be able to update your personal information, preferences, and settings.');
}
function myOrders() {
    window.location.href = '/customer/orders';
}
function logout() {
    if (typeof (Storage) !== "undefined") {
        localStorage.clear();
        sessionStorage.clear();
    }
    window.location.href = '/logout';
}