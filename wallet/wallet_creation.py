import json
from eth_account import Account
import getpass  # to hide your password input

# 1) Create or load your private key hex
acct = Account.create()
private_key = acct.key.hex()
address     = acct.address

# 2) Prompt for a password to encrypt it
password = getpass.getpass("Choose a password to encrypt your keystore: ")

# 3) Encrypt and write the keystore JSON
encrypted_keystore = Account.encrypt(private_key, password)
with open("keystore.json", "w") as f:
    json.dump(encrypted_keystore, f)
print("✔ Encrypted keystore saved to keystore.json")

# 4) Later, to unlock it:
password = getpass.getpass("Enter keystore password: ")
with open("keystore.json", "r") as f:
    keystore = json.load(f)
raw_key = Account.decrypt(keystore, password)
acct = Account.from_key(raw_key)
print("Unlocked address:", acct.address)
