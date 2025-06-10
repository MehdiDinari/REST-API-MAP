import os

# Bind to the port that Render provides
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Worker configuration
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "route_finder"

# Timeout
timeout = 30
keepalive = 2

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190