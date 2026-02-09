// Utility JavaScript functions

// Helper for CSRF token
function getCsrfToken() {
    const token = document.querySelector('input[name="csrf_token"]');
    return token ? token.value : '';
}

// Confirm delete
function confirmDelete(message = 'Are you sure you want to delete this?') {
    return confirm(message);
}

// Show notification
function showNotification(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show m-3`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(alertDiv, main.firstChild);
    }
}

// Form validation helper
document.addEventListener('DOMContentLoaded', function() {
    // Add any form validation or event listeners as needed
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Disable submit button to prevent double submission
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
            }
        });
    });
});
