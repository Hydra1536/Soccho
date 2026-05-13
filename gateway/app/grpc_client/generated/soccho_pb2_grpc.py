import grpc


class AuthServiceStub:
    def __init__(self, channel: grpc.aio.Channel):
        self.ValidateToken = channel.unary_unary('/soccho.AuthService/ValidateToken')
        self.GetUserInfo = channel.unary_unary('/soccho.AuthService/GetUserInfo')


class SocialServiceStub:
    def __init__(self, channel: grpc.aio.Channel):
        self.CheckFriendship = channel.unary_unary('/soccho.SocialService/CheckFriendship')
        self.GetFriendList = channel.unary_unary('/soccho.SocialService/GetFriendList')


class TransactionServiceStub:
    def __init__(self, channel: grpc.aio.Channel):
        self.GetBalance = channel.unary_unary('/soccho.TransactionService/GetBalance')


class NotificationServiceStub:
    def __init__(self, channel: grpc.aio.Channel):
        self.SendNotification = channel.unary_unary('/soccho.NotificationService/SendNotification')


def add_AuthServiceServicer_to_server(servicer, server):
    raise NotImplementedError
