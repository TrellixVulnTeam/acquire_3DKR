
import os

from Acquire.Service import get_this_service
from Acquire.Service import create_return_value


def run(args):
    status = 0
    message = "TEST"

    service = get_this_service(need_private_access=True)

    user = service.login_service_user()

    return_value = create_return_value(status, message)
    return_value["service_user"] = str(user)

    return return_value
