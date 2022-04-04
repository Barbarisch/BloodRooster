import enum


class UAC_FLAGS(enum.IntFlag):
	SCRIPT = 0x00000001  # The logon script is executed.
	ACCOUNTDISABLE = 0x00000002  # The user account is disabled.
	HOMEDIR_REQUIRED = 0x00000008  # The home directory is required.
	LOCKOUT = 0x00000010  # The account is currently locked out.
	PASSWD_NOTREQD = 0x00000020  # No password is required.
	PASSWD_CANT_CHANGE = 0x00000040  # The user cannot change the password.
	ENCRYPTED_TEXT_PASSWORD_ALLOWED = 0x00000080  # The user can send an encrypted password.
	TEMP_DUPLICATE_ACCOUNT = 0x00000100  # This is an account for users whose primary account is in another domain. This account provides user access to this domain, but not to any domain that trusts this domain. Also known as a local user account.
	NORMAL_ACCOUNT = 0x00000200  # This is a default account type that represe	nts a typical user.
	INTERDOMAIN_TRUST_ACCOUNT = 0x00000800  # This is a permit to trust account for a system domain that trusts other domains.
	WORKSTATION_TRUST_ACCOUNT = 0x00001000  # This is a computer account for a computer that is a member of this domain.
	SERVER_TRUST_ACCOUNT = 0x00002000  # This is a computer account for a system backup domain controller that is a member of this domain.
	NA_1 = 0x00004000  # Not used.
	NA_2 = 0x00008000  # Not used.
	DONT_EXPIRE_PASSWD = 0x00010000  # The password for this account will never expire.
	MNS_LOGON_ACCOUNT = 0x00020000  # This is an MNS logon account.
	SMARTCARD_REQUIRED = 0x00040000  # The user must log on using a smart card.
	TRUSTED_FOR_DELEGATION = 0x00080000  # The service account (user or computer account), under which a service runs, is trusted for Kerberos delegation. Any such service can impersonate a client requesting the service.
	NOT_DELEGATED = 0x00100000  # The security context of the user will not be delegated to a service even if the service account is set as trusted for Kerberos delegation.
	USE_DES_KEY_ONLY = 0x00200000  # Restrict this principal to use only Data Encryption Standard (DES) encryption types for keys.
	DONT_REQUIRE_PREAUTH = 0x00400000  # This account does not require Kerberos pre-authentication for logon.
	PASSWORD_EXPIRED = 0x00800000  # The user password has expired. This flag is created by the system using data from the [Pwd-Last-Set](a-pwdlastset.md) attribute and the domain policy.
	TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION = 0x01000000  # The account is enabled for delegation. This is a security-sensitive setting; accounts with this option enabled should be strictly controlled. This setting enables a service running under the account to assume a client identity and authenticate 	as that user to other remote servers on the network.


def calc_uac_flags(obj):
	try:
		int(obj.userAccountControl)
	except:
		return
	
	flags = UAC_FLAGS(int(obj.userAccountControl))
	obj.UAC_SCRIPT = bool(flags & UAC_FLAGS.SCRIPT)
	obj.UAC_ACCOUNTDISABLE = bool(flags & UAC_FLAGS.ACCOUNTDISABLE)
	obj.UAC_HOMEDIR_REQUIRED = bool(flags & UAC_FLAGS.HOMEDIR_REQUIRED)
	obj.UAC_LOCKOUT = bool(flags & UAC_FLAGS.LOCKOUT)
	obj.UAC_PASSWD_NOTREQD = bool(flags & UAC_FLAGS.PASSWD_NOTREQD)
	obj.UAC_PASSWD_CANT_CHANGE = bool(flags & UAC_FLAGS.PASSWD_CANT_CHANGE)
	obj.UAC_ENCRYPTED_TEXT_PASSWORD_ALLOWED = bool(flags & UAC_FLAGS.ENCRYPTED_TEXT_PASSWORD_ALLOWED)
	obj.UAC_TEMP_DUPLICATE_ACCOUNT = bool(flags & UAC_FLAGS.TEMP_DUPLICATE_ACCOUNT)
	obj.UAC_NORMAL_ACCOUNT = bool(flags & UAC_FLAGS.NORMAL_ACCOUNT)
	obj.UAC_INTERDOMAIN_TRUST_ACCOUNT = bool(flags & UAC_FLAGS.INTERDOMAIN_TRUST_ACCOUNT)
	obj.UAC_WORKSTATION_TRUST_ACCOUNT = bool(flags & UAC_FLAGS.WORKSTATION_TRUST_ACCOUNT)
	obj.UAC_SERVER_TRUST_ACCOUNT = bool(flags & UAC_FLAGS.SERVER_TRUST_ACCOUNT)
	obj.UAC_NA_1 = bool(flags & UAC_FLAGS.NA_1)
	obj.UAC_NA_2 = bool(flags & UAC_FLAGS.NA_2)
	obj.UAC_DONT_EXPIRE_PASSWD = bool(flags & UAC_FLAGS.DONT_EXPIRE_PASSWD)
	obj.UAC_MNS_LOGON_ACCOUNT = bool(flags & UAC_FLAGS.MNS_LOGON_ACCOUNT)
	obj.UAC_SMARTCARD_REQUIRED = bool(flags & UAC_FLAGS.SMARTCARD_REQUIRED)
	obj.UAC_TRUSTED_FOR_DELEGATION = bool(flags & UAC_FLAGS.TRUSTED_FOR_DELEGATION)
	obj.UAC_NOT_DELEGATED = bool(flags & UAC_FLAGS.NOT_DELEGATED)
	obj.UAC_USE_DES_KEY_ONLY = bool(flags & UAC_FLAGS.USE_DES_KEY_ONLY)
	obj.UAC_DONT_REQUIRE_PREAUTH = bool(flags & UAC_FLAGS.DONT_REQUIRE_PREAUTH)
	obj.UAC_PASSWORD_EXPIRED = bool(flags & UAC_FLAGS.PASSWORD_EXPIRED)
	obj.UAC_TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION = bool(flags & UAC_FLAGS.TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION)
	return
