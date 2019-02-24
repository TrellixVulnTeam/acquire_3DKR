"""
This script writes the login information (pem key etc.) that is needed
by the identity service to log onto the object store as the
identity admin user account
"""

import json
import sys
import os

from Acquire.Crypto import PrivateKey
from Acquire.ObjectStore import bytes_to_string

## Create a key to encrypt the config
config_key = PrivateKey()
secret_config = {}

## First create the login info to connect to the account

"""
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaavtaunkjmfj2uoouozmmojpix42kml72jy3nltu6srhipltnhv74q
fingerprint=b7:3e:01:9e:75:b3:68:75:29:69:bf:57:34:e5:e3:8b
key_file=~/.oci/oci_api_key.pem
pass_phrase=XXXXXX
tenancy=ocid1.tenancy.oc1..aaaaaaaa3eiex6fbfj626uwhs3dg24oygknrhhgfj4khqearluf4i74zdt2a
region=eu-frankfurt-1
"""

data = {}

# OCID for the user "acquire-storage-service"
data["user"] = "ocid1.user.oc1..aaaaaaaavtaunkjmfj2uoouozmmojpix42kml72jy3nltu6srhipltnhv74q"

# Fingerprint for the login keyfile
data["fingerprint"] = "b7:3e:01:9e:75:b3:68:75:29:69:bf:57:34:e5:e3:8b"

# The keyfile itself - we will now read the file and pull it into text
keyfile = sys.argv[1]
data["key_lines"] = open(sys.argv[1],"r").readlines()

# The tenancy in which this user and everything exists!
data["tenancy"] = "ocid1.tenancy.oc1..aaaaaaaa3eiex6fbfj626uwhs3dg24oygknrhhgfj4khqearluf4i74zdt2a"

# The passphrase to unlock the key - VERY SECRET!!!
data["pass_phrase"] = sys.argv[2]

# Make sure that this is the correct password...
privkey = PrivateKey.read(sys.argv[1],sys.argv[2])

# The region for this tenancy
data["region"] = "eu-frankfurt-1"

secret_config["LOGIN"] = data

## Now create the bucket info so we know where the bucket is
## that will store all data related to logging into accounts

data = {}
data["compartment"] = "ocid1.compartment.oc1..aaaaaaaat33j7w74mdyjenwoinyeawztxe7ri6qkfbm5oihqb5zteamvbpzq"
data["bucket"] = "acquire_storage"

secret_config["BUCKET"] = data
secret_config["STORAGE_COMPARTMENT"] = "ocid1.compartment.oc1..aaaaaaaatlvutbwbc6675hnhmueefnl6pvhlpugjixkjt27atmj2a4z3xjaq"

secret_config["PASSWORD"] = sys.argv[2]

config_data = bytes_to_string(config_key.encrypt(json.dumps(secret_config).encode("utf-8")))
secret_key = json.dumps(config_key.to_data(sys.argv[3]))

os.system("fn config app storage SECRET_CONFIG '%s'" % config_data)
os.system("fn config app storage SECRET_KEY '%s'" % secret_key)