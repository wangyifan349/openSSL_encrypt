def gcd(a, b):
    # 计算 a 和 b 的最大公约数
    while b != 0:
        a, b = b, a % b
    return a

def mod_inverse(e, phi):
    # 计算 e 关于 phi 的模逆
    d, x1, x2, y1 = 0, 0, 1, 1
    temp_phi = phi
    while e > 0:
        temp1, temp2 = temp_phi // e, temp_phi % e
        temp_phi, e = e, temp2
        x, y = x2 - temp1 * x1, d - temp1 * y1
        x2, x1, d, y1 = x1, x, y1, y
    if temp_phi == 1:
        return d + phi

def generate_keys(p, q, e):
    # 生成公钥和私钥
    n = p * q
    phi = (p - 1) * (q - 1)
    
    # 确保 e 和 phi 互质
    while gcd(e, phi) != 1:
        e += 1
    
    # 计算 d
    d = mod_inverse(e, phi)
    
    # 返回公钥和私钥
    return ((e, n), (d, n))

def encrypt(public_key, plaintext):
    # 使用公钥加密
    e, n = public_key
    return pow(plaintext, e, n)

def decrypt(private_key, ciphertext):
    # 使用私钥解密
    d, n = private_key
    return pow(ciphertext, d, n)

# 自定义参数
p = 61  # 选择一个大素数
q = 53  # 选择另一个大素数
e = 17  # 选择一个小整数作为公钥指数

# 生成密钥对
public_key, private_key = generate_keys(p, q, e)

# 示例消息
message = 42

# 加密消息
ciphertext = encrypt(public_key, message)

# 解密消息
decrypted_message = decrypt(private_key, ciphertext)

# 输出结果
print("Original:", message
