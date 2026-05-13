import grpc


class NotificationServiceServicer:
    pass


def add_NotificationServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'SendNotification': grpc.unary_unary_rpc_method_handler(servicer.SendNotification),
    }
    generic_handler = grpc.method_handlers_generic_handler('soccho.NotificationService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
