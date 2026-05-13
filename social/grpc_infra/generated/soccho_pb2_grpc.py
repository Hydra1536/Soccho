import grpc


class SocialServiceServicer:
    pass


class AuthServiceStub:
    def __init__(self, channel: grpc.aio.Channel):
        self.GetUserInfo = channel.unary_unary('/soccho.AuthService/GetUserInfo')


class TransactionServiceStub:
    def __init__(self, channel: grpc.aio.Channel):
        self.GetBalance = channel.unary_unary('/soccho.TransactionService/GetBalance')


def add_SocialServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'CheckFriendship': grpc.unary_unary_rpc_method_handler(servicer.CheckFriendship),
        'GetFriendList': grpc.unary_unary_rpc_method_handler(servicer.GetFriendList),
    }
    generic_handler = grpc.method_handlers_generic_handler('soccho.SocialService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
