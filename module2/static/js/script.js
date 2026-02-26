// Library Management System - Main JavaScript

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Add loading spinner for AJAX requests
    $(document).ajaxStart(function() {
        showLoadingSpinner();
    }).ajaxStop(function() {
        hideLoadingSpinner();
    });

    // Form validation
    $('form').on('submit', function(e) {
        if (!$(this).hasClass('no-validate')) {
            if (!validateForm($(this))) {
                e.preventDefault();
                showNotification('Please fill all required fields correctly!', 'error');
            }
        }
    });

    // Real-time form validation
    $('form input, form select, form textarea').on('blur', function() {
        validateField($(this));
    });

    // Search functionality
    let searchTimeout;
    $('#searchInput, .search-input').on('keyup', function() {
        clearTimeout(searchTimeout);
        const query = $(this).val();
        const searchType = $(this).data('search-type') || 'users';
        
        searchTimeout = setTimeout(function() {
            if (query.length >= 2 || query.length === 0) {
                performSearch(query, searchType);
            }
        }, 500);
    });

    // Delete confirmation
    $('.delete-btn, [data-action="delete"]').on('click', function(e) {
        e.preventDefault();
        const deleteUrl = $(this).attr('href') || $(this).data('url');
        const itemName = $(this).data('item-name') || 'item';
        
        showConfirmationDialog(
            `Delete ${itemName}?`,
            'This action cannot be undone!',
            function() {
                window.location.href = deleteUrl;
            }
        );
    });

    // Export functionality
    $('#exportBtn, .export-btn').on('click', function() {
        const exportType = $(this).data('export-type') || 'csv';
        exportData(exportType);
    });

    // Refresh data
    $('#refreshBtn, .refresh-btn').on('click', function() {
        refreshData();
    });

    // Print functionality
    $('#printBtn, .print-btn').on('click', function() {
        window.print();
    });

    // Toggle sidebar
    $('#sidebarToggle').on('click', function() {
        $('.sidebar').toggleClass('collapsed');
        $('.main-content').toggleClass('expanded');
    });

    // Dark mode toggle
    $('#darkModeToggle').on('click', function() {
        $('body').toggleClass('dark-mode');
        localStorage.setItem('darkMode', $('body').hasClass('dark-mode'));
    });

    // Check for saved dark mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        $('body').addClass('dark-mode');
    }

    // Initialize data tables
    if ($('#dataTable').length > 0) {
        initializeDataTable();
    }

    // Handle responsive tables
    $('.table-responsive').on('scroll', function() {
        $(this).addClass('scrolling');
    });
});

// Form validation function
function validateForm(form) {
    let isValid = true;
    
    // Check required fields
    form.find('[required]').each(function() {
        if (!validateField($(this))) {
            isValid = false;
        }
    });
    
    // Check email fields
    form.find('input[type="email"]').each(function() {
        const email = $(this).val();
        if (email && !isValidEmail(email)) {
            markFieldInvalid($(this), 'Please enter a valid email address');
            isValid = false;
        }
    });
    
    // Check phone fields
    form.find('input[type="tel"]').each(function() {
        const phone = $(this).val();
        if (phone && !isValidPhone(phone)) {
            markFieldInvalid($(this), 'Please enter a valid phone number');
            isValid = false;
        }
    });
    
    return isValid;
}

// Validate individual field
function validateField(field) {
    const value = field.val();
    const fieldName = field.attr('name');
    let isValid = true;
    let errorMessage = '';
    
    // Remove existing error
    field.removeClass('is-invalid');
    field.next('.invalid-feedback').remove();
    
    // Check if required and empty
    if (field.prop('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Check minlength
    const minlength = field.attr('minlength');
    if (minlength && value && value.length < parseInt(minlength)) {
        isValid = false;
        errorMessage = `Minimum ${minlength} characters required`;
    }
    
    // Check maxlength
    const maxlength = field.attr('maxlength');
    if (maxlength && value && value.length > parseInt(maxlength)) {
        isValid = false;
        errorMessage = `Maximum ${maxlength} characters allowed`;
    }
    
    // Check pattern
    const pattern = field.attr('pattern');
    if (pattern && value) {
        const regex = new RegExp(pattern);
        if (!regex.test(value)) {
            isValid = false;
            errorMessage = field.data('pattern-error') || 'Invalid format';
        }
    }
    
    if (!isValid) {
        markFieldInvalid(field, errorMessage);
    }
    
    return isValid;
}

// Mark field as invalid
function markFieldInvalid(field, message) {
    field.addClass('is-invalid');
    field.after(`<div class="invalid-feedback">${message}</div>`);
}

// Email validation helper
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Phone validation helper
function isValidPhone(phone) {
    const re = /^[\d\s\+\-\(\)]{10,}$/;
    return re.test(phone);
}

// Show loading spinner
function showLoadingSpinner() {
    if ($('#loadingSpinner').length === 0) {
        $('body').append(`
            <div id="loadingSpinner" class="spinner-overlay">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-2 text-primary">Loading...</div>
            </div>
        `);
    }
}

// Hide loading spinner
function hideLoadingSpinner() {
    $('#loadingSpinner').fadeOut('slow', function() {
        $(this).remove();
    });
}

// Show notification
function showNotification(message, type = 'success') {
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 
                 type === 'warning' ? 'exclamation-triangle' : 'info-circle';
    
    const bgClass = type === 'success' ? 'bg-success' : 
                    type === 'error' ? 'bg-danger' : 
                    type === 'warning' ? 'bg-warning' : 'bg-info';
    
    const notification = `
        <div class="alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3 animate__animated animate__fadeInRight" 
             style="z-index: 9999; min-width: 300px;" role="alert">
            <i class="fas fa-${icon} me-2"></i>
            <strong>${type.charAt(0).toUpperCase() + type.slice(1)}!</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('body').append(notification);
    
    setTimeout(function() {
        $('.alert').last().fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
}

// Show confirmation dialog
function showConfirmationDialog(title, message, onConfirm) {
    const modalId = 'confirmationModal';
    
    // Remove existing modal if any
    $('#' + modalId).remove();
    
    // Create modal
    const modal = `
        <div class="modal fade" id="${modalId}" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            ${title}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-0">${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-2"></i>Cancel
                        </button>
                        <button type="button" class="btn btn-danger" id="confirmAction">
                            <i class="fas fa-check me-2"></i>Confirm
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(modal);
    
    // Show modal
    const modalInstance = new bootstrap.Modal(document.getElementById(modalId));
    modalInstance.show();
    
    // Handle confirmation
    $('#confirmAction').on('click', function() {
        modalInstance.hide();
        setTimeout(onConfirm, 300);
    });
}

// Perform search
function performSearch(query, type = 'users') {
    if (!query || query.length < 2) {
        if (query.length === 0) {
            // Load all items when search is cleared
            loadSearchResults('', type);
        }
        return;
    }
    
    showLoadingSpinner();
    
    $.ajax({
        url: `/api/search/${type}`,
        method: 'GET',
        data: { q: query },
        success: function(response) {
            displaySearchResults(response.data, type);
        },
        error: function(xhr, status, error) {
            showNotification('Search failed: ' + error, 'error');
        },
        complete: function() {
            hideLoadingSpinner();
        }
    });
}

// Display search results
function displaySearchResults(results, type) {
    const resultsContainer = $('#searchResults');
    if (!resultsContainer.length) return;
    
    resultsContainer.empty();
    
    if (results && results.length > 0) {
        results.forEach(function(item) {
            resultsContainer.append(createResultItem(item, type));
        });
    } else {
        resultsContainer.html(`
            <div class="text-center py-4">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <p class="text-muted">No results found</p>
            </div>
        `);
    }
}

// Create result item
function createResultItem(item, type) {
    switch(type) {
        case 'users':
            return `
                <div class="list-group-item list-group-item-action">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${item.name}</h6>
                            <small class="text-muted">${item.email}</small>
                        </div>
                        <span class="badge bg-${item.status === 'Active' ? 'success' : 'secondary'}">${item.status}</span>
                    </div>
                </div>
            `;
        case 'books':
            return `
                <div class="list-group-item list-group-item-action">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${item.title}</h6>
                            <small class="text-muted">by ${item.author}</small>
                        </div>
                        <span class="badge bg-info">${item.available} available</span>
                    </div>
                </div>
            `;
        default:
            return `<div class="list-group-item">${JSON.stringify(item)}</div>`;
    }
}

// Load search results
function loadSearchResults(query, type) {
    // Implement based on your needs
    console.log('Loading search results for:', query, type);
}

// Export data
function exportData(format = 'csv') {
    showNotification(`Exporting data as ${format.toUpperCase()}...`, 'info');
    
    // Simulate export delay
    setTimeout(function() {
        showNotification('Export completed successfully!', 'success');
    }, 2000);
}

// Refresh data
function refreshData() {
    showLoadingSpinner();
    
    // Simulate refresh
    setTimeout(function() {
        location.reload();
    }, 1000);
}

// Initialize DataTable
function initializeDataTable() {
    $('#dataTable').DataTable({
        responsive: true,
        pageLength: 10,
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
        language: {
            search: "_INPUT_",
            searchPlaceholder: "Search...",
            lengthMenu: "Show _MENU_ entries",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            infoEmpty: "Showing 0 to 0 of 0 entries",
            infoFiltered: "(filtered from _MAX_ total entries)"
        }
    });
}

// Handle AJAX errors globally
$(document).ajaxError(function(event, jqxhr, settings, error) {
    if (jqxhr.status === 401) {
        window.location.href = '/login';
    } else if (jqxhr.status === 403) {
        showNotification('You do not have permission to perform this action', 'error');
    } else if (jqxhr.status === 404) {
        showNotification('Resource not found', 'error');
    } else if (jqxhr.status === 500) {
        showNotification('Server error occurred', 'error');
    }
});

// Handle window resize
$(window).on('resize', function() {
    // Adjust UI elements on resize
    if ($(window).width() < 768) {
        $('.sidebar').addClass('collapsed');
    } else {
        $('.sidebar').removeClass('collapsed');
    }
});

// Keyboard shortcuts
$(document).on('keydown', function(e) {
    // Ctrl/Cmd + F for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        $('#searchInput').focus();
    }
    
    // Ctrl/Cmd + N for new item
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        $('.btn-primary[href*="add"]').click();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        $('.modal').modal('hide');
    }
});