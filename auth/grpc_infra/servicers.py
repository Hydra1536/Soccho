from concurrent import futures

import grpc
import jwt
from django.conf import settings

from apps.users.models import User
from .generated import soccho_pb2, soccho_pb2_grpc


class AuthServicer(soccho_pb2_grpc.AuthServiceServicer):
    def ValidateToken(self, request, context):
        token = request.token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub", "")
            if not user_id:
                return soccho_pb2.ValidateTokenResponse(valid=False, user_id="", error="invalid")
            return soccho_pb2.ValidateTokenResponse(valid=True, user_id=str(user_id), error="")
        except jwt.PyJWTError:
            return soccho_pb2.ValidateTokenResponse(valid=False, user_id="", error="invalid")

    def GetUserInfo(self, request, context):
        user_id = request.user_id
        try:
            user = User.objects.get(id=user_id)
            return soccho_pb2.GetUserInfoResponse(
                user_id=str(user.id),
                username=user.username,
                email=user.email,
                is_active=True,
            )
        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User not found")
            return soccho_pb2.GetUserInfoResponse()


def build_server(max_workers: int = 10):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    soccho_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)
    return server
