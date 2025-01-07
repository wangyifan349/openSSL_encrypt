import secrets

def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def mod_inverse(e, phi):
    d, x1, x2, y1 = 0, 0, 1, 1
    temp_phi = phi
    while e > 0:
        temp1, temp2 = temp_phi // e, temp_phi % e
        temp_phi, e = e, temp2
        x, y = x2 - temp1 * x1, d - temp1 * y1
        x2, x1, d, y1 = x1, x, y1, y
    if temp_phi == 1:
        return d + phi

def is_prime(num):
    if num <= 1:
        return False
    if num <= 3:
        return True
    if num % 2 == 0 or num % 3 == 0:
        return False
    i = 5
    while i * i <= num:
        if num % i == 0 or num % (i + 2) == 0:
            return False
        i += 6
    return True

def generate_large_prime(bits):
    while True:
        num = secrets.randbits(bits)
        if is_prime(num):
            return num

def generate_keys(bits=2048):
    print("Generating large prime numbers...")
    p = generate_large_prime(bits // 2)
    q = generate_large_prime(bits // 2)
    print(f"Prime p: {p}")
    print(f"Prime q: {q}")
    
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537  # 常用的公钥指数
    d = mod_inverse(e, phi)
    
    print(f"Modulus n: {n}")
    print(f"Euler's Totient phi: {phi}")
    print(f"Public exponent e: {e}")
    print(f"Private exponent d: {d}")
    
    return ((e, n), (d, n))

def encrypt(public_key, plaintext):
    e, n = public_key
    ciphertext = pow(plaintext, e, n)
    print(f"Encrypting message {plaintext} to ciphertext {ciphertext}")
    return ciphertext

def decrypt(private_key, ciphertext):
    d, n = private_key
    decrypted_message = pow(ciphertext, d, n)
    print(f"Decrypting ciphertext {ciphertext} to message {decrypted_message}")
    return decrypted_message

# 参数设置
key_size = 2048  # 密钥大小（位数）

# 生成密钥对
public_key, private_key = generate_keys(bits=key_size)

# 示例消息
message = 42

# 加密消息
ciphertext = encrypt(public_key, message)

# 解密消息
decrypted_message = decrypt(private_key, ciphertext)

# 输出结果
print("Original message:", message)
print("Encrypted message:", ciphertext)
print("Decrypted message:", decrypted_message)
