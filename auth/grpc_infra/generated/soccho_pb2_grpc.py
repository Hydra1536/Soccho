import grpc


class AuthServiceServicer:
    pass


def add_AuthServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "ValidateToken": grpc.unary_unary_rpc_method_handler(servicer.ValidateToken),
        "GetUserInfo": grpc.unary_unary_rpc_method_handler(servicer.GetUserInfo),
    }
    generic_handler = grpc.method_handlers_generic_handler("soccho.AuthService", rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
