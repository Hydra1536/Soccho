from concurrent import futures
import signal
import threading
import time

import django
import grpc
from django.core.management.base import BaseCommand

from grpc_infra.generated import soccho_pb2_grpc
from grpc_infra.servicers import SocialServicer


class Command(BaseCommand):
    help = 'Run Social gRPC server'

    def handle(self, *args, **options):
        django.setup()
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        soccho_pb2_grpc.add_SocialServiceServicer_to_server(SocialServicer(), server)
        server.add_insecure_port('0.0.0.0:8002')

        stop_event = threading.Event()

        def _stop(signum, frame):
            server.stop(grace=10)
            stop_event.set()

        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)

        self.stdout.write(self.style.SUCCESS('Social gRPC server started on 0.0.0.0:8002'))
        server.start()

        while not stop_event.is_set():
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS('Social gRPC server stopped'))
