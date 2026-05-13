from concurrent import futures
import signal
import threading
import time

import django
import grpc
from django.core.management.base import BaseCommand

from grpc_infra.generated import soccho_pb2_grpc
from grpc_infra.servicers import TransactionServicer


class Command(BaseCommand):
    help = 'Run Transaction gRPC server'

    def handle(self, *args, **options):
        django.setup()
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        soccho_pb2_grpc.add_TransactionServiceServicer_to_server(TransactionServicer(), server)
        server.add_insecure_port('0.0.0.0:8003')

        stop_event = threading.Event()

        def _stop(signum, frame):
            server.stop(grace=10)
            stop_event.set()

        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)

        self.stdout.write(self.style.SUCCESS('Transaction gRPC server started on 0.0.0.0:8003'))
        server.start()
        while not stop_event.is_set():
            time.sleep(0.5)
