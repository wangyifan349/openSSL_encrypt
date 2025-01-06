import os
import hashlib

# secp256k1 相关常量
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
A = 0
B = 7
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# 椭圆曲线点加法
def point_addition(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P
    if P == Q:
        # 计算斜率 lam = (3 * x^2 + a) / (2 * y) mod p
        lam = (3 * P[0] * P[0] * pow(2 * P[1], P - 2, P)) % P
    else:
        # 计算斜率 lam = (y2 - y1) / (x2 - x1) mod p
        lam = ((Q[1] - P[1]) * pow(Q[0] - P[0], P - 2, P)) % P
    # 计算 x3 和 y3
    x = (lam * lam - P[0] - Q[0]) % P
    y = (lam * (P[0] - x) - P[1]) % P
    return (x, y)

# 椭圆曲线点乘
def scalar_multiplication(k, P):
    R = None
    while k:
        if k & 1:
            R = point_addition(R, P)
        P = point_addition(P, P)
        k >>= 1
    return R

# 生成随机私钥
def generate_private_key():
    return int.from_bytes(os.urandom(32), 'big') % N

# 使用 secp256k1 曲线生成公钥
def private_key_to_public_key(private_key):
    return scalar_multiplication(private_key, (Gx, Gy))

# 计算公钥的哈希值
def hash_public_key(public_key):
    x, y = public_key
    # 将公钥转换为字节
    public_key_bytes = b'\x04' + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')
    # 计算 SHA-256 和 RIPEMD-160 哈希
    sha256 = hashlib.sha256(public_key_bytes).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()
    return ripemd160

# Bech32 编码
def bech32_polymod(values):
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = (chk >> 25)
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk

def bech32_hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def bech32_create_checksum(hrp, data):
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]

def bech32_encode(hrp, data):
    CHARSET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
    combined = data + bech32_create_checksum(hrp, data)
    return hrp + '1' + ''.join([CHARSET[d] for d in combined])

def convertbits(data, frombits, tobits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret

# 生成 BIP84 地址
def generate_bip84_address(public_key):
    ripemd160 = hash_public_key(public_key)
    data = convertbits(ripemd160, 8, 5)
    return bech32_encode("bc", [0] + data)

# 主函数
def main():
    private_key = generate_private_key()
    public_key = private_key_to_public_key(private_key)
    address = generate_bip84_address(public_key)
    
    print("Private Key:", hex(private_key))
    print("Public Key:", f"({hex(public_key[0])}, {hex(public_key[1])})")
    print("BIP84 Address:", address)

if __name__ == "__main__":
    main()
