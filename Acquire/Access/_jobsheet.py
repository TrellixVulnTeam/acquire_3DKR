
__all__ = ["JobSheet"]


class JobSheet:
    """This class holds a complete record of a job that the access
       service has been asked to perform.
    """
    def __init__(self, job=None, authorisation=None):
        if job is not None:
            from Acquire.Identity import Authorisation as _Authorisation
            if not isinstance(authorisation, _Authorisation):
                raise TypeError("You can only authorise a reqeust with "
                                "a valid Authorisation object")
            authorisation.verify(job.fingerprint())
            from Acquire.ObjectStore import create_uuid as _create_uuid
            self._job = job
            self._authorisation = authorisation
            self._uid = _create_uuid()
        else:
            self._uid = None

    def is_null(self):
        """Return whether or not this JobSheet is null"""
        return self._uid is None

    def uid(self):
        """Return the UID of this JobSheet"""
        return self._uid

    def total_cost(self):
        """Return the total maximum quoted cost for this job. The
           total cost to run the job must not exceed this
        """
        if self.is_null():
            return 0
        else:
            return 10

    def job(self):
        """Return the original job request"""
        if self.is_null():
            return None
        else:
            return self._job

    def authorisation(self):
        """Return the original authorisation for this job"""
        if self.is_null():
            return None
        else:
            return self._authorisation

    def set_payment(self, cheque):
        """Pass in and cash that contains the source of value of
           paying for this job. This will cash the cheque and store
           the value within credit notes held in this job sheet
        """
        if self.is_null():
            from Acquire.Accounting import PaymentError
            raise PaymentError("You cannot try to pay for a null job!")

        from Acquire.Client import Cheque as _Cheque
        if not isinstance(cheque, _Cheque):
            raise TypeError("You must pass a valid Cheque as payment "
                            "for a job")

        try:
            credit_notes = cheque.cash(spend=self.total_cost(),
                                       resource=self.job().fingerprint())
        except Exception as e:
            from Acquire.Service import exception_to_string
            from Acquire.Accounting import PaymentError
            raise PaymentError(
                "Problem cashing the cheque used to pay for the calculation: "
                "\n\nCAUSE: %s" % exception_to_string(e))

        if credit_notes is None or len(credit_notes) == 0:
            from Acquire.Accounting import PaymentError
            raise PaymentError("Cannot be paid!")

        # save these credit_notes so that they are not lost
        self._credit_notes = credit_notes

        # save the the object store so we always have a record of this value
        self.save()

    def request_services(self):
        """Request all of the services needed to perform the job. This
           will contract a compute service and a storage service to run
           the job.

           The storage service will provide (1) a file upload PAR to enable
           the user to upload the input, and (2) a bucket write PAR to
           enable the compute service to write the output

           The compute service will be supplied with the bucket write PAR
           from the storage service and will supply a run calculation PAR
           to enable the user to trigger the start of the job

           This returns the upload PAR the user must use to upload the
           input, the run PAR that the user must call after uploading
           input to trigger the start of the calculation, and the expiry
           date when both of these PARs will become invalid (i.e. the user
           must trigger both of them before that date)
        """
        # make the requests, make the payments

        # save so we don't lost the debit notes or any value
        self.save()

        return ("upload_par", "run_par", "future")

    def save(self):
        """Save this JobSheet to the object store"""
        from Acquire.Service import assert_running_service \
            as _assert_running_service

        _assert_running_service()

        if self.is_null():
            return

        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        key = "jobsheets/%s" % self.uid()
        _ObjectStore.set_object_from_json(bucket, key, self.to_data())

    @staticmethod
    def load(uid):
        """Return the JobSheet with specified uid loaded from the
           ObjectStore
        """
        from Acquire.Service import assert_running_service \
            as _assert_running_service

        _assert_running_service()

        if uid is None:
            return

        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        key = "jobsheets/%s" % str(uid)
        data = _ObjectStore.get_object_from_json(bucket, key)
        return JobSheet.from_data(data)

    def to_data(self):
        """Return this converted to a json-serialisable dictionary"""
        data = {}

        if self.is_null():
            return data

        from Acquire.ObjectStore import list_to_string as _list_to_string

        data["uid"] = self.uid()
        data["job"] = self.job().to_data()
        data["authorisation"] = self.authorisation().to_data()
        data["credit_notes"] = _list_to_string(self._credit_notes)

        return data

    @staticmethod
    def from_data(data):
        """Return a JobSheet constructed from the passed json-deserialised
           dictionary
        """
        j = JobSheet()

        if (data and len(data) > 0):
            from Acquire.Access import RunRequest as _RunRequest
            from Acquire.Client import Authorisation as _Authorisation
            from Acquire.Accounting import CreditNote as _CreditNote
            from Acquire.ObjectStore import string_to_list \
                as _string_to_list

            j._uid = str(data["uid"])
            j._job = _RunRequest.from_data(data["job"])
            j._authorisation = _Authorisation.from_data(
                                            data["authorisation"])
            j._credit_notes = _string_to_list(data["credit_notes"],
                                              _CreditNote)

        return j
