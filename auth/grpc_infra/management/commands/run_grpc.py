import signal
import threading
import time

import django
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run Auth gRPC server"

    def handle(self, *args, **options):
        django.setup()

        from grpc_infra.servicers import build_server

        server = build_server()
        server.add_insecure_port("0.0.0.0:8001")

        stop_event = threading.Event()

        def _graceful_shutdown(signum, frame):
            self.stdout.write(self.style.WARNING(f"Received signal {signum}. Stopping gRPC server..."))
            server.stop(grace=10)
            stop_event.set()

        signal.signal(signal.SIGTERM, _graceful_shutdown)
        signal.signal(signal.SIGINT, _graceful_shutdown)

        self.stdout.write(self.style.SUCCESS("Starting Auth gRPC server on 0.0.0.0:8001"))
        server.start()

        try:
            while not stop_event.is_set():
                time.sleep(0.5)
        finally:
            server.stop(grace=10)
            self.stdout.write(self.style.SUCCESS("Auth gRPC server stopped"))
