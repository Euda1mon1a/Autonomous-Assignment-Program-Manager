"""CSS styles for email templates."""

***REMOVED*** Main email stylesheet
EMAIL_STYLESHEET = """
/* Reset styles */
body, table, td, a {
    -webkit-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%;
}
table, td {
    mso-table-lspace: 0pt;
    mso-table-rspace: 0pt;
}
img {
    -ms-interpolation-mode: bicubic;
    border: 0;
    height: auto;
    line-height: 100%;
    outline: none;
    text-decoration: none;
}

/* Base styles */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: ***REMOVED***333333;
    background-color: ***REMOVED***f4f4f4;
    margin: 0;
    padding: 0;
    width: 100% !important;
}

/* Container */
.email-container {
    max-width: 600px;
    margin: 0 auto;
    background-color: ***REMOVED***ffffff;
}

/* Header */
.email-header {
    background-color: ***REMOVED***003366;
    color: ***REMOVED***ffffff;
    padding: 30px 20px;
    text-align: center;
}

.email-header h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
}

/* Content */
.email-content {
    padding: 30px 20px;
}

.email-content p {
    margin: 0 0 15px 0;
}

.email-content h2 {
    font-size: 20px;
    font-weight: 600;
    margin: 20px 0 10px 0;
    color: ***REMOVED***003366;
}

/* Priority indicators */
.priority-high {
    border-left: 4px solid ***REMOVED***dc3545;
    padding-left: 16px;
}

.priority-normal {
    border-left: 4px solid ***REMOVED***007bff;
    padding-left: 16px;
}

.priority-low {
    border-left: 4px solid ***REMOVED***6c757d;
    padding-left: 16px;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 12px 24px;
    background-color: ***REMOVED***003366;
    color: ***REMOVED***ffffff !important;
    text-decoration: none;
    border-radius: 4px;
    font-weight: 600;
    margin: 10px 0;
}

.btn:hover {
    background-color: ***REMOVED***002244;
}

.btn-danger {
    background-color: ***REMOVED***dc3545;
}

.btn-danger:hover {
    background-color: ***REMOVED***c82333;
}

/* Tables */
table.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

table.data-table td,
table.data-table th {
    padding: 10px;
    border-bottom: 1px solid ***REMOVED***e9ecef;
    text-align: left;
}

table.data-table th {
    font-weight: 600;
    background-color: ***REMOVED***f8f9fa;
}

/* Footer */
.email-footer {
    background-color: ***REMOVED***f8f9fa;
    padding: 20px;
    font-size: 14px;
    color: ***REMOVED***6c757d;
    text-align: center;
}

.email-footer a {
    color: ***REMOVED***007bff;
    text-decoration: none;
}

/* Responsive */
@media only screen and (max-width: 600px) {
    .email-container {
        width: 100% !important;
    }

    .email-content {
        padding: 20px 15px;
    }
}
"""

***REMOVED*** Dark mode support
DARK_MODE_STYLES = """
@media (prefers-color-scheme: dark) {
    body {
        background-color: ***REMOVED***1a1a1a !important;
        color: ***REMOVED***e0e0e0 !important;
    }

    .email-container {
        background-color: ***REMOVED***2a2a2a !important;
    }

    .email-content h2 {
        color: ***REMOVED***4a9eff !important;
    }

    table.data-table th {
        background-color: ***REMOVED***333333 !important;
    }

    table.data-table td,
    table.data-table th {
        border-bottom-color: ***REMOVED***444444 !important;
    }

    .email-footer {
        background-color: ***REMOVED***333333 !important;
        color: ***REMOVED***999999 !important;
    }
}
"""


def get_complete_stylesheet() -> str:
    """Get complete stylesheet with dark mode support."""
    return EMAIL_STYLESHEET + "\n" + DARK_MODE_STYLES
