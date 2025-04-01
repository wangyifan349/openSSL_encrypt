import socket
import threading
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization

# -------------------- AES-GCM加密函数 --------------------
def aes_gcm_encrypt(key, plaintext):
    nonce = os.urandom(12)  # 生成随机nonce
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return nonce + encryptor.tag + ciphertext  # 返回nonce、标签和密文

# -------------------- AES-GCM解密函数 --------------------
def aes_gcm_decrypt(key, ciphertext):
    nonce = ciphertext[:12]  # 提取nonce
    tag = ciphertext[12:28]  # 提取标签
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext[28:]) + decryptor.finalize()
    return plaintext

# -------------------- 生成AES密钥 --------------------
def generate_aes_key(private_key, peer_public_key, salt):
    # 生成共享密钥
    shared_key = private_key.exchange(peer_public_key)
    # 使用共享密钥派生AES密钥，使用对方发送的salt
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    return kdf.derive(shared_key)

# -------------------- 客户端代码 --------------------
def client():
    # 创建X25519密钥对
    client_private_key = x25519.X25519PrivateKey.generate()
    client_public_key = client_private_key.public_key()

    # TCP客户端
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 65432))
        # 接收服务器发送的公钥和salt（总共32+16=48字节）
        data = s.recv(48)
        if len(data) != 48:
            print("接收到的数据格式不正确")
            return
        # 分离公钥和salt
        server_public_key_bytes = data[:32]
        salt = data[32:48]
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
        server_public_key = X25519PublicKey.from_public_bytes(server_public_key_bytes)

        # 发送客户端公钥
        client_pub_bytes = client_public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        s.sendall(client_pub_bytes)

        # 生成AES密钥（双方使用同一salt）
        aes_key = generate_aes_key(client_private_key, server_public_key, salt)

        # 启动接收和发送数据的线程
        threading.Thread(target=receive_data, args=(s, aes_key), daemon=True).start()
        threading.Thread(target=send_data, args=(s, aes_key), daemon=True).start()

        # 主线程保持存活，防止子线程退出
        while True:
            pass

# -------------------- 发送数据的线程 --------------------
def send_data(conn, aes_key):
    message_counter = 0
    while True:
        try:
            message = input("客户端输入消息: ").encode('utf-8')  # 用户输入
            encrypted_message = aes_gcm_encrypt(aes_key, message)  # 加密消息
            # 发送加密后的消息
            conn.sendall(encrypted_message)
            message_counter += 1
        except Exception as e:
            print("发送错误:", e)

# -------------------- 接收数据的线程 --------------------
def receive_data(conn, aes_key):
    while True:
        try:
            encrypted_message = conn.recv(4096)  # 接收数据
            if not encrypted_message:
                print("连接关闭")
                break
            # 检查是否为重传请求（简化判断：以"RESEND"开头的消息不做解密处理）
            if encrypted_message.startswith(b"RESEND"):
                print("服务器请求重传：", encrypted_message.decode('utf-8'))
                continue
            decrypted_message = aes_gcm_decrypt(aes_key, encrypted_message)
            print("接收到:", decrypted_message.decode('utf-8'))
        except Exception as e:
            print("解密或接收错误:", e)
            try:
                conn.sendall(b"ERROR")
            except Exception as send_err:
                print("发送错误反馈失败:", send_err)

if __name__ == "__main__":
    client()


import socket
import threading
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization
# -------------------- AES-GCM加密函数 --------------------
def aes_gcm_encrypt(key, plaintext):
    nonce = os.urandom(12)  # 生成随机nonce
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return nonce + encryptor.tag + ciphertext  # 返回nonce、标签和密文
# -------------------- AES-GCM解密函数 --------------------
def aes_gcm_decrypt(key, ciphertext):
    nonce = ciphertext[:12]  # 提取nonce
    tag = ciphertext[12:28]  # 提取标签
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext[28:]) + decryptor.finalize()
    return plaintext
# -------------------- 生成AES密钥 --------------------
def generate_aes_key(private_key, peer_public_key, salt):
    # 生成共享密钥
    shared_key = private_key.exchange(peer_public_key)
    # 使用共享密钥派生AES密钥，确保双方使用同一salt
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    return kdf.derive(shared_key)
# -------------------- 服务器代码 --------------------
def server():
    # 创建X25519密钥对
    server_private_key = x25519.X25519PrivateKey.generate()
    server_public_key = server_private_key.public_key()
    # 预先生成一个salt，后续将一并发送给客户端
    salt = os.urandom(16)
    # TCP服务器
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 65432))
        s.listen()
        print("服务器正在监听...")
        conn, addr = s.accept()
        with conn:
            print('连接来自', addr)
            # 发送服务器公钥和salt（先发送长度固定的64字节数据：32字节公钥 + 16字节salt）
            server_pub_bytes = server_public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            # 按固定顺序发送：先发送公钥，再发送salt
            conn.sendall(server_pub_bytes + salt)
            # 接收客户端公钥（客户端发送32字节）
            client_public_key_bytes = conn.recv(32)
            if len(client_public_key_bytes) != 32:
                print("接收到的客户端公钥长度不正确")
                return
            from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
            client_public_key = X25519PublicKey.from_public_bytes(client_public_key_bytes)
            # 生成AES密钥（双方使用同一salt）
            aes_key = generate_aes_key(server_private_key, client_public_key, salt)
            # 启动接收和发送数据的线程
            threading.Thread(target=receive_data, args=(conn, aes_key), daemon=True).start()
            threading.Thread(target=send_data, args=(conn, aes_key), daemon=True).start()
            # 主线程保持存活，防止子线程退出
            while True:
                pass
# -------------------- 接收数据的线程 --------------------
def receive_data(conn, aes_key):
    message_counter = 0
    while True:
        try:
            encrypted_message = conn.recv(4096)  # 接收4096字节
            if not encrypted_message:
                print("连接关闭")
                break
            decrypted_message = aes_gcm_decrypt(aes_key, encrypted_message)
            print(f"接收到消息 {message_counter}:", decrypted_message.decode('utf-8'))
            message_counter += 1
        except Exception as e:
            print("解密或接收错误:", e)
            # 请求客户端重发当前消息（重发仅示例，不建议无限重试）
            error_message = f"RESEND {message_counter}".encode('utf-8')
            try:
                conn.sendall(error_message)
            except Exception as send_err:
                print("发送重传请求失败:", send_err)
# -------------------- 发送数据的线程 --------------------
def send_data(conn, aes_key):
    while True:
        try:
            message = input("服务器输入消息: ").encode('utf-8')  # 接收用户输入
            encrypted_message = aes_gcm_encrypt(aes_key, message)  # 加密消息
            conn.sendall(encrypted_message)  # 发送加密后的消息
        except Exception as e:
            print("发送错误:", e)
if __name__ == "__main__":
    server()



