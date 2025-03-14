from ecdsa import VerifyingKey, SECP256k1


class Transaction:
    def __init__(self, sender, receiver, amount, sender_private_key, signature):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        if not signature:
            self.signature = self.sign_transaction(sender_private_key)
        else:
            self.signature = signature


    def sign_transaction(self, private_key):
        message = f"{self.sender}{self.receiver}{self.amount}"
        return private_key.sign(message.encode())


    def verify_signature(self, sender, receiver, amount, signature, public_key):
        message = f"{sender}{receiver}{amount}".encode()
        try:
            verifying_key = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
            return verifying_key.verify(bytes.fromhex(signature), message)
        except:
            return False


    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "signature": self.signature
        }