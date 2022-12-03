from .registry import Registry


class UserDataRegistry(Registry):
    name = "api_user_data"

    def get_all_user_data(self, user, request) -> dict:
        """
        Collects the additional user data of all the registered user data type
        instances.

        :param user: The user that just authenticated.
        :type user: User
        :param request: The request when the user authenticated.
        :type request: Request
        :return: a dict containing all additional user data payload for all the
            registered instances.
        """

        return {
            key: value.get_user_data(user, request)
            for key, value in self.registry.items()
        }


user_data_registry = UserDataRegistry()


def jwt_response_payload_handler(token, user=None, request=None, issued_at=None):
    payload = {
        "token": token,
        # "user": UserSerializer(user, context={"request": request}).data,
    }

    # Update the payload with the additional user data that must be added. The
    # `user_data_registry` contains instances that want to add additional information
    # to this payload.
    payload.update(**user_data_registry.get_all_user_data(user, request))

    return payload
