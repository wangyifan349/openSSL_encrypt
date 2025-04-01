import socket
import threading
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

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
def generate_aes_key(private_key, peer_public_key):
    # 生成共享密钥
    shared_key = private_key.exchange(peer_public_key)
    
    # 使用共享密钥派生AES密钥
    kdf = Scrypt(
        salt=os.urandom(16),
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
        # 接收服务器公钥
        server_public_key_bytes = s.recv(32)
        server_public_key = x25519.X25519PublicKey.from_public_bytes(server_public_key_bytes)

        # 发送公钥
        s.send(client_public_key.public_bytes())
        # 生成AES密钥
        aes_key = generate_aes_key(client_private_key, server_public_key)

        # 启动接收和发送数据的线程
        threading.Thread(target=receive_data, args=(s, aes_key)).start()
        threading.Thread(target=send_data, args=(s, aes_key)).start()

# -------------------- 发送数据的线程 --------------------
def send_data(conn, aes_key):
    message_counter = 0
    while True:
        message = input("客户端输入消息: ").encode('utf-8')  # 接收用户输入
        encrypted_message = aes_gcm_encrypt(aes_key, message)  # 加密消息
        while True:
            try:
                conn.sendall(encrypted_message)  # 发送加密后的消息
                response = conn.recv(4096).decode('utf-8')
                if response.startswith("RESEND"):
                    resend_index = int(response.split()[1])
                    if resend_index == message_counter:
                        print(f"重发消息 {message_counter}...")
                        continue  # 如果请求重发当前消息，重发
                break
            except Exception as e:
                print("发送错误:", e)
                continue  # 发生错误时重试
        message_counter += 1

# -------------------- 接收数据的线程 --------------------
def receive_data(conn, aes_key):
    while True:
        try:
            encrypted_message = conn.recv(4096)  # 接收4096字节
            if not encrypted_message:
                break
            decrypted_message = aes_gcm_decrypt(aes_key, encrypted_message)
            print("接收到:", decrypted_message.decode('utf-8'))
        except Exception as e:
            print("解密或接收错误:", e)
            conn.sendall(b"ERROR")  # 发送错误信号请求重发

if __name__ == "__main__":
    client()






import socket
import threading
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
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
def generate_aes_key(private_key, peer_public_key):
    # 生成共享密钥
    shared_key = private_key.exchange(peer_public_key)
    # 使用共享密钥派生AES密钥
    kdf = Scrypt(
        salt=os.urandom(16),
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
    # TCP服务器
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 65432))
        s.listen()
        print("服务器正在监听...")
        conn, addr = s.accept()
        with conn:
            print('连接来自', addr)
            # 发送公钥
            conn.send(server_public_key.public_bytes())
            # 接收客户端公钥
            client_public_key_bytes = conn.recv(32)
            client_public_key = x25519.X25519PublicKey.from_public_bytes(client_public_key_bytes)

            # 生成AES密钥
            aes_key = generate_aes_key(server_private_key, client_public_key)

            # 启动接收和发送数据的线程
            threading.Thread(target=receive_data, args=(conn, aes_key)).start()
            threading.Thread(target=send_data, args=(conn, aes_key)).start()

# -------------------- 接收数据的线程 --------------------
def receive_data(conn, aes_key):
    message_counter = 0
    while True:
        try:
            encrypted_message = conn.recv(4096)  # 接收4096字节
            if not encrypted_message:
                break
            decrypted_message = aes_gcm_decrypt(aes_key, encrypted_message)
            print(f"接收到消息 {message_counter}:", decrypted_message.decode('utf-8'))
            message_counter += 1
        except Exception as e:
            print("解密或接收错误:", e)
            error_message = f"RESEND {message_counter}".encode('utf-8')
            conn.sendall(error_message)  # 请求重发当前消息
# -------------------- 发送数据的线程 --------------------
def send_data(conn, aes_key):
    while True:
        message = input("服务器输入消息: ").encode('utf-8')  # 接收用户输入
        encrypted_message = aes_gcm_encrypt(aes_key, message)  # 加密消息
        conn.sendall(encrypted_message)  # 发送加密后的消息

if __name__ == "__main__":
    server()



