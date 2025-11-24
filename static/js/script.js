// Simple JavaScript for enhancing user experience

document.addEventListener('DOMContentLoaded', function() {
    // Form validation for registration
    const registerForm = document.querySelector('form[action="/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            if (password && password.value.length < 6) {
                alert('Password must be at least 6 characters long');
                e.preventDefault();
            }
        });
    }
    
    // Form validation for login
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const email = document.getElementById('email');
            const password = document.getElementById('password');
            
            if (email && !email.value) {
                alert('Please enter your email');
                e.preventDefault();
                return;
            }
            
            if (password && !password.value) {
                alert('Please enter your password');
                e.preventDefault();
                return;
            }
        });
    }
    
    // Form validation for new voter application
    const applicationForm = document.querySelector('form[action="/voter/new_application"]');
    if (applicationForm) {
        applicationForm.addEventListener('submit', function(e) {
            const requiredFields = applicationForm.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = 'red';
                } else {
                    field.style.borderColor = '#ddd';
                }
            });
            
            if (!isValid) {
                alert('Please fill in all required fields');
                e.preventDefault();
            }
        });
    }
    
    // Form validation for update request
    const updateRequestForm = document.querySelector('form[action*="/voter/update_request"]');
    if (updateRequestForm) {
        updateRequestForm.addEventListener('submit', function(e) {
            const fieldSelect = document.getElementById('field_name');
            const newValue = document.getElementById('new_value');
            
            if (fieldSelect && !fieldSelect.value) {
                alert('Please select a field to update');
                e.preventDefault();
                return;
            }
            
            if (newValue && !newValue.value.trim()) {
                alert('Please enter a new value');
                e.preventDefault();
                return;
            }
        });
    }
    
    // Admin form validation
    const adminForms = document.querySelectorAll('form[action*="/admin/"]');
    adminForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const statusSelect = form.querySelector('select[name="status"]');
            if (statusSelect && !statusSelect.value) {
                alert('Please select a status');
                e.preventDefault();
            }
        });
    });
    
    // Add confirmation for status changes
    const statusForms = document.querySelectorAll('form[action*="/update_status"]');
    statusForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to update the status?')) {
                e.preventDefault();
            }
        });
    });
});