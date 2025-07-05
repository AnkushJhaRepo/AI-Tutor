import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Process naming
proc_name = "ai_tutor"
pythonpath = "."

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Server mechanics
daemon = False
pidfile = "ai_tutor.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Server hooks
def on_starting(server):
    """Log when server starts."""
    server.log.info("Starting AI Tutor server")

def on_exit(server):
    """Clean up when server exits."""
    server.log.info("Shutting down AI Tutor server")

def worker_int(worker):
    """Handle worker interrupt."""
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """Handle worker abort."""
    worker.log.info("Worker received SIGABRT signal")

# Ensure log directory exists
os.makedirs("logs", exist_ok=True) 