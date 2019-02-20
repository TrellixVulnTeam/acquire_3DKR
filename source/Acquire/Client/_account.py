
import datetime as _datetime
import json as _json

__all__ = ["Account", "get_accounts", "create_account",
           "deposit", "withdraw"]


def _get_accounting_url():
    """Function to discover and return the default accounting url"""
    return "http://fn.acquire-aaai.com:8080/t/accounting"


def _get_accounting_service(accounting_url=None):
    """Function to return the accounting service for the system"""
    if accounting_url is None:
        accounting_url = _get_accounting_url()

    from Acquire.Client import Service as _Service
    service = _Service(accounting_url)

    if not service.is_accounting_service():
        from Acquire.Client import LoginError
        raise LoginError(
            "You can only use a valid accounting service to get account info! "
            "The service at '%s' is a '%s'" %
            (accounting_url, service.service_type()))

    if service.service_url() != accounting_url:
        service.update_service_url(accounting_url)

    return service


def _get_account_uid(user, account_name, accounting_service=None,
                     accounting_url=None):
    """Return the UID of the account called 'account_name' that
        belongs to passed user on the passed accounting_service
    """
    if account_name is None:
        # return the UID of the default account for this user
        account_name = "main"

    if accounting_service is None:
        service = _get_accounting_service(accounting_url)
    else:
        if not accounting_service.is_accounting_service():
            raise TypeError("You can only query accounts using "
                            "a valid accounting service")
        service = accounting_service

    args = {"user_uid": user.uid(),
            "account_name": str(account_name)}

    if user.is_logged_in():
        from Acquire.Client import Authorisation as _Authorisation
        auth = _Authorisation(user=user)
        args["authorisation"] = auth.to_data()

    result = service.call_function(function="get_account_uids", args=args)

    account_uids = result["account_uids"]

    for account_uid in account_uids:
        if account_uids[account_uid] == account_name:
            return account_uid

    from Acquire.Client import AccountError
    raise AccountError("There is no account called '%s' for '%s'" %
                       (account_name, str(user)))


def _get_account_uids(user, accounting_service=None, accounting_url=None):
    """Return the names and UIDs of all of the accounts that belong
        to the passed user on the passed accounting_service
    """
    if accounting_service is None:
        service = _get_accounting_service(accounting_url)
    else:
        if not accounting_service.is_accounting_service():
            raise TypeError("You can only query accounts using "
                            "a valid accounting service")
        service = accounting_service

    if not user.is_logged_in():
        raise PermissionError(
            "You can only get information about about a user's accounts "
            "if they have authenticated their login")

    from Acquire.Client import Authorisation as _Authorisation
    auth = _Authorisation(user=user)
    args = {"authorisation": auth.to_data()}

    result = service.call_function(function="get_account_uids", args=args)

    return result["account_uids"]


def get_accounts(user, accounting_service=None, accounting_url=None):
    """Return all of the accounts of the passed user. Note that the
    user must be authenticated to call this function
    """
    if accounting_service is None:
        service = _get_accounting_service(accounting_url)
    else:
        if not accounting_service.is_accounting_service():
            raise TypeError("You can only query account using "
                            "a valid accounting service")
        service = accounting_service

    account_uids = _get_account_uids(
                        user, accounting_service=service)

    accounts = []

    for uid in account_uids.keys():
        name = account_uids[uid]

        account = Account()
        account._account_name = name
        account._account_uid = uid
        account._user = user
        account._accounting_service = accounting_service

        accounts.append(account)

    return accounts


def create_account(user, account_name, description=None,
                   accounting_service=None, accounting_url=None):
    """Create an account on the accounting service for the passed
        user, calling the account 'account_name' and optionally
        passing in an account description. Note that the user must
        have authorised the login
    """
    if accounting_service is None:
        service = _get_accounting_service(accounting_url)
    else:
        if not accounting_service.is_accounting_service():
            raise TypeError("You can only query account using "
                            "a valid accounting service")
        service = accounting_service

    if not user.is_logged_in():
        raise PermissionError(
            "You cannot create an account called '%s' for user "
            "'%s' as the user login has not been authenticated." %
            (account_name, user.name()))

    from Acquire.Client import Authorisation as _Authorisation
    authorisation = _Authorisation(user=user)

    args = {"account_name": str(account_name),
            "authorisation": authorisation.to_data()}

    if description is None:
        args["description"] = "Account '%s' for '%s'" % \
                                (str(account_name), user.name())
    else:
        args["description"] = str(description)

    result = service.call_function(function="create_account", args=args)

    account_uid = result["account_uid"]

    account = Account()
    account._account_name = account_name
    account._account_uid = account_uid
    account._user = user
    account._accounting_service = accounting_service

    return account


def deposit(user, value, description=None,
            accounting_service=None, accounting_url=None):
    """Tell the system to allow the user to deposit 'value' from
       their (real) financial account to the system accounts
    """
    from Acquire.Client import Authorisation as _Authorisation
    authorisation = _Authorisation(user=user)

    if accounting_service is None:
        service = _get_accounting_service(accounting_url)
    else:
        if not accounting_service.is_accounting_service():
            raise TypeError("You can only deposit funds using an "
                            "accounting service!")
        service = accounting_service

    args = {"authorisation": authorisation.to_data()}

    if description is None:
        from Acquire.Accounting import create_decimal as _create_decimal
        args["value"] = str(_create_decimal(value))
    else:
        from Acquire.Accounting import Transaction as _Transaction
        args["transaction"] = _Transaction(value, description).to_data()

    result = service.call_function(function="deposit", args=args)

    return result


def withdraw(user, value, description=None,
             accounting_service=None, accounting_url=None):
    """Tell the system to allow the user to withdraw 'value' from
       the system accounts back to their (real) financial account
    """
    raise NotImplementedError("withdrawals are not yet implemented!")


class Account:
    """This is the client-side handle that is used to interact with
       an account on the service. If the account is created with a valid
       user login then you can perform tasks such as making payments,
       or issueing receipts or refunds. Otherwise, this is a simple
       interface that allows the account to be used as a receiver
       of value
    """
    def __init__(self, user=None, account_name=None, accounting_service=None,
                 accounting_url=None):
        """Construct the Account with the passed account_name, which is owned
           by the passed user. The account must already exist on the service,
           or else an exception will be raised
        """
        if user is not None:
            if account_name is None:
                self._account_name = "main"
            else:
                self._account_name = str(account_name)

            self._user = user

            if accounting_service is None:
                accounting_service = _get_accounting_service(accounting_url)

            self._accounting_service = accounting_service

            self._account_uid = _get_account_uid(user, account_name,
                                                 accounting_service)
        else:
            self._account_uid = None

        self._last_update = None
        self._description = None

    def __str__(self):
        if self.is_null():
            return "Account::null"
        else:
            return "Account(name='%s', uid=%s)" % (self.name(), self.uid())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._account_uid == other._account_uid
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_null(self):
        """Return whether or not this is a null account"""
        return self._account_uid is None

    def uid(self):
        """Return the UID of this account"""
        return self._account_uid

    def name(self):
        """Return the name of this account"""
        if self.is_null():
            return None
        else:
            return self._account_name

    def owner(self):
        """Return the user who owns this account"""
        if self.is_null():
            return None
        else:
            return self._user

    def user(self):
        """Synonym for owner"""
        return self.owner()

    def is_logged_in(self):
        """Return whether or not the user has an authenticated login
           to this account
        """
        try:
            return self._user.is_logged_in()
        except:
            return False

    def last_update_time(self):
        """Return the time of the last update of the balance"""
        return self._last_update

    def _refresh(self, force_update=False):
        """Refresh the current status of this account. This fetches
           the latest data, e.g. balance, limits etc. Note that this
           limits you to refreshing at most once every five seconds...
        """
        if self.is_null():
            from Acquire.Accounting import create_decimal as _create_decimal
            self._overdraft_limit = _create_decimal(0)
            self._balance = _create_decimal(0)
            self._liability = _create_decimal(0)
            self._receivable = _create_decimal(0)
            self._spent_today = _create_decimal(0)
            return

        if force_update:
            should_refresh = True
        else:
            should_refresh = False

            if self._last_update is None:
                should_refresh = True
            else:
                should_refresh = (_datetime.datetime.now() -
                                  self._last_update).seconds > 5

        if not should_refresh:
            return

        if not self.is_logged_in():
            raise PermissionError(
                "You cannot get information about this account "
                "until after the owner has successfully authenticated.")

        from Acquire.Client import Authorisation as _Authorisation
        from Acquire.Accounting import create_decimal as _create_decimal

        service = self.accounting_service()

        auth = _Authorisation(resource=self._account_uid, user=self._user)

        args = {"authorisation": auth.to_data(),
                "account_name": self.name()}

        result = service.call_function(function="get_info", args=args)

        self._overdraft_limit = _create_decimal(result["overdraft_limit"])
        self._balance = _create_decimal(result["balance"])
        self._liability = _create_decimal(result["liability"])
        self._receivable = _create_decimal(result["receivable"])
        self._spent_today = _create_decimal(result["spent_today"])
        self._description = result["description"]

        self._last_update = _datetime.datetime.now()

    def accounting_service(self):
        """Return the accounting service managing this account"""
        return self._accounting_service

    def description(self):
        """Return the description of this account"""
        if not self._description:
            self._refresh()

        return self._description

    def balance(self, force_update=False):
        """Return the current balance of this account"""
        self._refresh(force_update)
        return self._balance

    def liability(self, force_update=False):
        """Return the current total liability of this account"""
        self._refresh(force_update)
        return self._liability

    def receivable(self, force_update=False):
        """Return the current total accounts receivable of this account"""
        self._refresh(force_update)
        return self._receivable

    def spent_today(self, force_update=False):
        """Return the current amount spent today on this account"""
        self._refresh(force_update)
        return self._spent_today

    def overdraft_limit(self, force_update=False):
        """Return the overdraft limit of this account"""
        self._refresh(force_update)
        return self._overdraft_limit

    def is_beyond_overdraft_limit(self, force_update=False):
        """Return whether or not the current balance is beyond
           the overdraft limit
        """
        self._refresh(force_update)
        return (self._balance - self._liability) < -(self._overdraft_limit)

    def perform(self, transaction, credit_account, is_provisional=False):
        """Tell this accounting service to apply the transfer described
           in 'transaction' from this account to the passed account. Note
           that the user must have logged into this account so that they
           have authorised this transaction. This returns the record
           of this transaction
        """
        if not self.is_logged_in():
            raise PermissionError("You cannot transfer value from '%s' to "
                                  "'%s' because you have not authenticated "
                                  "the user who owns this account" %
                                  (str(self), str(credit_account)))

        from Acquire.Accounting import Transaction as _Transaction

        if not isinstance(transaction, _Transaction):
            raise TypeError("The passed transaction must be of type "
                            "Transaction")

        if not isinstance(credit_account, Account):
            raise TypeError("The passed credit account must be of type "
                            "Account")

        if transaction.is_null():
            return None

        from Acquire.Client import Authorisation as _Authorisation
        service = self.accounting_service()

        auth = _Authorisation(resource=self._account_uid, user=self._user)

        if is_provisional:
            is_provisional = True
        else:
            is_provisional = False

        args = {"transaction": transaction.to_data(),
                "debit_account_uid": str(self.uid()),
                "credit_account_uid": str(credit_account.uid()),
                "is_provisional": is_provisional,
                "authorisation": auth.to_data()}

        result = service.call_function(function="perform", args=args)

        return result["transaction_records"]

    def receipt(self, credit_note, receipted_value=None):
        """Receipt the passed credit note that contains a request to
           transfer value from another account to the passed account
        """
        if not self.is_logged_in():
            raise PermissionError("You cannot receipt a credit note as the "
                                  "user has not yet logged in!")

        if credit_note.account_uid() != self.uid():
            raise ValueError(
                "You cannot receipt a transaction from a different "
                "account! %s versus %s" % (credit_note.account_uid(),
                                           self.uid()))

        from Acquire.Client import Authorisation as _Authorisation
        from Acquire.Accounting import create_decimal as _create_decimal

        service = self.accounting_service()

        auth = _Authorisation(resource=self._account_uid, user=self._user)

        args = {"credit_note": credit_note.to_data(),
                "authorisation": auth.to_data()}

        if receipted_value is not None:
            args["receipted_value"] = str(_create_decimal(receipted_value))

        result = service.call_function(function="receipt", args=args)

        return result["transaction_record"]

    def refund(self, credit_note):
        """Refunds the passed credit note that contained a transfer of
           from another account to the passed account
        """
        if not self.is_logged_in():
            raise PermissionError("You cannot refund a credit note as the "
                                  "user has not yet logged in!")

        if credit_note.account_uid() != self.uid():
            raise ValueError(
                "You cannot refund a transaction from a different "
                "account! %s versus %s" % (credit_note.account_uid(),
                                           self.uid()))

        from Acquire.Client import Authorisation as _Authorisation
        from Acquire.Accounting import create_decimal as _create_decimal

        service = self.accounting_service()

        auth = _Authorisation(resource=self._account_uid, user=self._user)

        args = {"credit_note": credit_note.to_data(),
                "authorisation": auth.to_data()}

        result = service.call_function(function="refund", args=args)

        return result["transaction_record"]
