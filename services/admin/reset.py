
import os

from Acquire.Service import get_this_service, get_service_account_bucket
from Acquire.Service import create_return_value

from Acquire.ObjectStore import ObjectStore


def run(args):
    """This function completely resets a service and deletes
       all data. This resets back to the original state.
       Obviously you should be really sure you want to do this!
    """

    status = 0
    message = "Resetting service..."

    bucket = get_service_account_bucket()

    ObjectStore.delete_all_objects(bucket)

    return {"status": status, "message": message}