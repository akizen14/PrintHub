"""
Constants for PrintHub application
Centralize all magic numbers and configuration values
"""

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT_SECONDS = 10

# Polling Configuration
ADMIN_POLL_INTERVAL_MS = 5000  # 5 seconds
ADMIN_FAST_POLL_INTERVAL_MS = 2000  # 2 seconds when actively working

# Order Status Constants
STATUS_PENDING = "Pending"
STATUS_QUEUED = "Queued"
STATUS_PRINTING = "Printing"
STATUS_READY = "Ready"
STATUS_COLLECTED = "Collected"
STATUS_CANCELLED = "Cancelled"
STATUS_ERROR = "Error"

# Payment Status Constants
PAYMENT_UNPAID = "unpaid"
PAYMENT_PAID = "paid"
PAYMENT_REFUNDED = "refunded"

# Queue Type Constants
QUEUE_URGENT = "urgent"
QUEUE_NORMAL = "normal"
QUEUE_BULK = "bulk"

# UI Constants
TABLE_ROW_HEIGHT = 50
BUTTON_FONT_SIZE = 18
BUTTON_PADDING = "25px 40px"
BUTTON_MIN_HEIGHT = 80

# Color Constants - Status Colors
COLOR_STATUS_PENDING = {"bg": "#fef3c7", "fg": "#92400e"}
COLOR_STATUS_QUEUED = {"bg": "#dbeafe", "fg": "#1e40af"}
COLOR_STATUS_PRINTING = {"bg": "#fed7aa", "fg": "#9a3412"}
COLOR_STATUS_READY = {"bg": "#d1fae5", "fg": "#065f46"}

# Color Constants - Buttons
COLOR_BUTTON_PRIMARY = {"normal": "#2563eb", "hover": "#1d4ed8", "disabled": "#cbd5e1"}
COLOR_BUTTON_SUCCESS = {"normal": "#16a34a", "hover": "#15803d", "disabled": "#cbd5e1"}
COLOR_BUTTON_DANGER = {"normal": "#dc2626", "hover": "#b91c1c", "disabled": "#cbd5e1"}
COLOR_BUTTON_NEUTRAL = {"normal": "#64748b", "hover": "#475569", "disabled": "#cbd5e1"}
COLOR_BUTTON_PURPLE = {"normal": "#7c3aed", "hover": "#6d28d9", "disabled": "#cbd5e1"}

# Temporary Directories
TEMP_PRINT_DIR = r"C:\PrintHub\TempPrint"

# Admin Authentication
DEFAULT_ADMIN_PASSWORD = "printhub2025"

# Hash Update Interval (for change detection)
HASH_UPDATE_CHECK_INTERVAL = 5000  # ms

# Performance Thresholds
SLOW_REQUEST_THRESHOLD_MS = 1000  # Log requests slower than 1 second
CACHE_DURATION_SECONDS = 60  # Cache rates/settings for 60 seconds
