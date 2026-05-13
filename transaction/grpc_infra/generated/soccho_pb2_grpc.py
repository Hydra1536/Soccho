import grpc


class TransactionServiceServicer:
    pass


class SocialServiceStub:
    def __init__(self, channel: grpc.aio.Channel):
        self.CheckFriendship = channel.unary_unary('/soccho.SocialService/CheckFriendship')



def add_TransactionServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'GetBalance': grpc.unary_unary_rpc_method_handler(servicer.GetBalance),
    }
    generic_handler = grpc.method_handlers_generic_handler('soccho.TransactionService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
