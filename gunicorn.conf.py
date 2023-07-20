import multiprocessing

workers = multiprocessing.cpu_count()
bind = "0.0.0.0:80"
worker_class = "uvicorn.workers.UvicornWorker"
graceful_timeout = "300"
timeout = "300"
keepalive = "5"
accesslog = "-"
errorlog = "-"
forwarded_allow_ips = "*"
max_requests = 1000
max_requests_jitter = 50
log_file = "-"
