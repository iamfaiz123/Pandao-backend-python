import time
import hashlib
import hmac

def generate_secure_signature(secret, expire):
    k, m = secret, str(expire).encode('utf-8')
    if not isinstance(k, (bytes, bytearray)):
        k = k.encode('utf-8')

    return hmac.new(k, m, hashlib.sha256).hexdigest()


def generate_signature():
    # Expire in 30 minutes
    expire = int(time.time()) + 60 * 30
    # Secret key of your project
    constant = '5bfd4441dfb2a488a946'
    # Generate the signature
    signature = generate_secure_signature(constant, expire)
    return {
        'signature': signature,
        'expire': expire
    }


