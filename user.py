from ecdsa import SigningKey, SECP256k1
import hashlib


class User:
    def __init__(self, name):
        self.name = name
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
        self.wallet_address = hashlib.sha256(self.public_key.to_string()).hexdigest()

    
    def get_wallet_address(self):
        return self.wallet_address