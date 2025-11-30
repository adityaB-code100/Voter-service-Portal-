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
    const applicationForm = document.querySelector('form[action="/voter/new_application"], form[action^="/voter/application/"]');
    if (applicationForm) {
        // Add change event listener to ID proof type dropdown
        const idProofType = document.getElementById('id_proof_type');
        const idProofNumber = document.getElementById('id_proof_number');
        
        if (idProofType && idProofNumber) {
            idProofType.addEventListener('change', function() {
                validateIdProofNumber(idProofType.value, idProofNumber.value);
            });
            
            idProofNumber.addEventListener('blur', function() {
                validateIdProofNumber(idProofType.value, idProofNumber.value);
            });
        }
        
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
            
            // Validate ID proof number
            if (idProofType && idProofNumber) {
                const validationError = validateIdProofNumber(idProofType.value, idProofNumber.value, true);
                if (validationError) {
                    alert(validationError);
                    isValid = false;
                }
            }
            
            if (!isValid) {
                alert('Please fill in all required fields correctly');
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

// Function to validate ID proof number based on ID proof type
function validateIdProofNumber(idProofType, idProofNumber, showAlert = false) {
    if (!idProofNumber) {
        if (showAlert) return "ID Proof Number is required";
        return null;
    }
    
    // Clean the input
    idProofNumber = idProofNumber.trim().toUpperCase();
    
    // Validation based on ID proof type
    let errorMessage = null;
    
    if (idProofType === "Aadhaar Card") {
        // Aadhaar card should be 12 digits
        if (!/^\d{12}$/.test(idProofNumber)) {
            errorMessage = "Aadhaar Card number must be 12 digits";
        }
    } else if (idProofType === "Pan Card") {
        // PAN card should be 10 characters: 5 letters + 4 digits + 1 letter
        if (!/^[A-Z]{5}\d{4}[A-Z]{1}$/.test(idProofNumber)) {
            errorMessage = "PAN Card number must be 10 characters (5 letters + 4 digits + 1 letter)";
        }
    } else if (idProofType === "Passport") {
        // Passport should start with a letter followed by digits, typically 6-9 characters
        if (!/^[A-Z]\d{5,8}$/.test(idProofNumber)) {
            errorMessage = "Passport number should start with a letter followed by 5-8 digits";
        }
    } else if (idProofType === "Driving License") {
        // Driving license format varies by state but typically 10-16 characters
        if (idProofNumber.length < 10 || idProofNumber.length > 16) {
            errorMessage = "Driving License number should be between 10-16 characters";
        }
    }
    
    if (errorMessage && showAlert) {
        return errorMessage;
    }
    
    return null; // Valid
}