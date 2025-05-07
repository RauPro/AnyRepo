import os, json, getpass
from eth_account import Account

def load_latest_keystore(keystore_dir: str = ".", suffix: str = ".json") -> bytes:
    files = [
        os.path.join(keystore_dir, fn)
        for fn in os.listdir(keystore_dir)
        if fn.endswith(suffix)
    ]
    if not files:
        raise FileNotFoundError(f"No `{suffix}` files found in {keystore_dir}")
    latest = max(files, key=lambda f: os.path.getmtime(f))
    print(f"🔑 Loading keystore from: {latest}")
    with open(latest, "r") as f:
        keystore_json = json.load(f)
    pwd = getpass.getpass("Enter keystore password: ")
    raw_key = Account.decrypt(keystore_json, pwd)
    # raw_private_key = load_latest_keystore(keystore_dir="./wallet", suffix=".json")
    # PRIVATE_KEY = raw_private_key.hex()    # hex string, e.g. '0x4c0883...'
    # print(PRIVATE_KEY)
    return raw_key