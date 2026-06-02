"""
Gunicorn configuration for the Orders Service.
Optimised for a containerised environment (Docker / k8s).
"""

import multiprocessing
import os

# ─── Server socket ────────────────────────────────────────────────────────────
bind = f"0.0.0.0:{os.getenv('PORT', '8003')}"
backlog = 2048

# ─── Workers ──────────────────────────────────────────────────────────────────
# (2 × CPU cores) + 1
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# ─── Logging ──────────────────────────────────────────────────────────────────
accesslog = "-"            # stdout
errorlog = "-"             # stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# ─── Process naming ───────────────────────────────────────────────────────────
proc_name = "orders-service"

# ─── Security ─────────────────────────────────────────────────────────────────
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190


# ─── Hooks ────────────────────────────────────────────────────────────────────
def on_starting(server):
    server.log.info("Orders Service starting up — PID %s", os.getpid())


def worker_exit(server, worker):
    server.log.info("Worker %s exiting", worker.pid)
