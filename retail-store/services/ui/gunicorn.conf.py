"""
Gunicorn configuration for the UI Service.
Port 8080 by default (Nginx proxies to this).
"""
import multiprocessing, os

bind           = f"0.0.0.0:{os.getenv('GUNICORN_PORT', '8080')}"
workers        = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class   = "sync"
timeout        = int(os.getenv("GUNICORN_TIMEOUT", "30"))
keepalive      = 5
max_requests   = 1000
max_requests_jitter = 100
accesslog      = "-"
errorlog       = "-"
loglevel       = os.getenv("LOG_LEVEL", "info").lower()
proc_name      = "ui-service"
