
__all__ = ["OTP"]


class OTP:
    """This class handles everything to do with obtaining and
       verifying a one-time-password"""
    def __init__(self, secret=None):
        """This creates a new one-time-password"""
        try:
            import pyotp as _pyotp
        except:
            from Acquire.Crypto import OTPError
            raise OTPError(
                "Cannot create a one-time-password as the "
                "pyotp module is not available. Please install and try again")

        if secret:
            self._secret = secret
        else:
            self._secret = _pyotp.random_base32()

    def __str__(self):
        """Return a string representation of this OTP"""
        return "OTP()"

    def __eq__(self, other):
        return self._secret == other._secret

    @staticmethod
    def decrypt(secret, key):
        """Construct a OTP from the passed encrypted secret
           that will be decrypted with the passed private key"""
        from Acquire.Crypto import PrivateKey as _PrivateKey
        if not isinstance(key, _PrivateKey):
            raise TypeError(
                "You can only encrypt a OTP using a valid "
                "PrivateKey - not using a %s" % key.__class__)

        otp = OTP()
        otp._secret = key.decrypt(secret)

        return otp

    def encrypt(self, key):
        """This uses the passed public key to encrypt and return the
           secret"""
        from Acquire.Crypto import PublicKey as _PublicKey
        if not isinstance(key, _PublicKey):
            raise TypeError(
                "You can only encrypt a OTP using a valid "
                "PublicKey - not using a %s" % key.__class__)

        return key.encrypt(self._secret)

    def _totp(self):
        """Return the time-based one-time-password based on this secret"""
        try:
            import pyotp as _pyotp
            return _pyotp.totp.TOTP(self._secret)
        except:
            from Acquire.Crypto import OTPError
            raise OTPError("You cannot get a null OTP - create one first!")

    def provisioning_uri(self, username, issuer="Acquire"):
        """Return the provisioning URI, assuming this secret is
           for the user called 'username' and is issued by 'issuer'"""
        return self._totp().provisioning_uri(username, issuer_name=issuer)

    def secret(self):
        """Return the otpsecret for this generator"""
        return self._secret

    @staticmethod
    def extract_secret(provisioning_uri):
        """Return the otpsecret extracted from the passed provisioning_url"""
        import re as _re
        try:
            return _re.search(r"secret=([\w\d+]+)&issuer",
                              provisioning_uri).groups()[0]
        except Exception as e:
            from Acquire.Crypto import OTPError
            raise OTPError(
                "Cannot extract the otp secret from the provisioning URL "
                "'%s': %s" % (provisioning_uri, str(e)))

    @staticmethod
    def from_provisioning_uri(provisioning_uri):
        """Construct and return an OTP from the passed provisioning URI"""
        return OTP(secret=OTP.extract_secret(provisioning_uri))

    def generate(self):
        """Generate and return the current OTP code"""
        totp = self._totp()
        return totp.now()

    def verify(self, code):
        """Verify that the passed code is correct. This raises an exception
           if the code is incorrect, or does nothing if the code is correct
        """
        # the OTP is valid for 1 minute. We will extend this so that
        # it is valid for 3 minutes (1 minute before and after). This
        # improves usability and tolerance for clock drift with only
        # minor increase in OTP validity time
        if not self._totp().verify(code, valid_window=1):
            from Acquire.Crypto import OTPError
            raise OTPError("The passed OTP code is incorrect")
