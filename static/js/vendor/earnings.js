/**
 * Enhanced Earnings Page JavaScript
 * Handles charts, filtering, and interactive features
 */

let earningsChart = null;
let categoryChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    initializeFilters();
    initializeInteractions();
});

// Initialize Charts
function initializeCharts() {
    // Main Earnings Chart
    const earningsCtx = document.getElementById('earningsChart');
    if (earningsCtx && chartData.labels && chartData.values) {
        earningsChart = new Chart(earningsCtx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Earnings (₹)',
                    data: chartData.values,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#10b981',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `₹${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#666'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            color: '#666',
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    // Category Pie Chart
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx && chartData.categoryLabels && chartData.categoryValues) {
        const colors = [
            '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6',
            '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
        ];
        
        categoryChart = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: chartData.categoryLabels,
                datasets: [{
                    data: chartData.categoryValues,
                    backgroundColor: colors.slice(0, chartData.categoryLabels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#10b981',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ₹${context.parsed.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }
}

// Initialize Filters
function initializeFilters() {
    // Chart period filter
    const chartPeriod = document.getElementById('chartPeriod');
    if (chartPeriod) {
        chartPeriod.addEventListener('change', function() {
            updateChartPeriod(this.value);
        });
    }

    // Status filter for earnings table
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            filterEarningsTable(this.value);
        });
    }
}

// Initialize Interactive Features
function initializeInteractions() {
    // Add hover effects to overview cards
    const overviewCards = document.querySelectorAll('.overview-card');
    overviewCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(-5px)';
        });
    });

    // Add click effects to stat items
    const statItems = document.querySelectorAll('.stat-item');
    statItems.forEach(item => {
        item.addEventListener('click', function() {
            // Add a subtle animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
}

// Update Chart Period
function updateChartPeriod(period) {
    // This would typically make an AJAX call to get new data
    // For now, we'll just show a loading state
    if (earningsChart) {
        // Show loading state
        const canvas = earningsChart.canvas;
        const ctx = canvas.getContext('2d');
        
        // You would implement actual data fetching here
        console.log(`Updating chart for period: ${period} days`);
        
        // Placeholder for actual implementation
        // fetchEarningsData(period).then(data => {
        //     earningsChart.data.labels = data.labels;
        //     earningsChart.data.datasets[0].data = data.values;
        //     earningsChart.update();
        // });
    }
}

// Filter Earnings Table
function filterEarningsTable(status) {
    const rows = document.querySelectorAll('.order-row');
    
    rows.forEach(row => {
        const rowStatus = row.getAttribute('data-status');
        
        if (status === 'all' || rowStatus === status) {
            row.style.display = 'table-row';
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update visible count
    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
    console.log(`Showing ${visibleRows.length} orders`);
}

// Export Earnings Data
function exportEarnings() {
    // Get table data
    const table = document.getElementById('earningsTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    let csvContent = '';
    
    // Add headers
    const headers = table.querySelectorAll('th');
    const headerRow = Array.from(headers).map(th => th.textContent.trim()).join(',');
    csvContent += headerRow + '\n';
    
    // Add data rows (skip header row)
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        if (row.style.display === 'none') continue; // Skip filtered rows
        
        const cells = row.querySelectorAll('td');
        const rowData = Array.from(cells).map(td => {
            // Clean up cell content
            return td.textContent.trim().replace(/,/g, ';');
        }).join(',');
        
        csvContent += rowData + '\n';
    }
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `earnings_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    // Show success message
    showNotification('Earnings data exported successfully!', 'success');
}

// View Order Details
function viewOrderDetails(orderId) {
    // This would typically open a modal or navigate to order details
    console.log(`Viewing details for order #${orderId}`);
    
    // Placeholder for actual implementation
    showNotification(`Viewing details for Order #${orderId}`, 'info');
}

// Show Notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '12px 20px',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '600',
        zIndex: '10000',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease'
    });
    
    // Set background color based on type
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Utility function to format currency
function formatCurrency(amount) {
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Utility function to format percentage
function formatPercentage(value) {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
}