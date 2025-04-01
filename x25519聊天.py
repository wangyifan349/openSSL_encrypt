#!/usr/bin/env python3
import socket
import threading
import os
import time
import logging
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("server.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

SERVER_ADDRESS = ('', 65432)

# AES-GCM加密函数
def aes_gcm_encrypt(key, plaintext):
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    logging.debug("【加密】生成nonce、tag和密文")
    return nonce + encryptor.tag + ciphertext

# AES-GCM解密函数
def aes_gcm_decrypt(key, ciphertext):
    nonce = ciphertext[:12]
    tag = ciphertext[12:28]
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext[28:]) + decryptor.finalize()
    logging.debug("【解密】数据解密成功")
    return plaintext

# 生成AES密钥（使用双方共享的salt）
def generate_aes_key(private_key, peer_public_key, salt):
    shared_key = private_key.exchange(peer_public_key)
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    aes_key = kdf.derive(shared_key)
    logging.debug("【密钥】AES密钥生成成功")
    return aes_key

# 处理单个连接（会话处理函数）
def handle_connection(conn, addr):
    logging.info(f"建立新会话，连接来自：{addr}")
    try:
        # 每次会话为独立的，生成各自的密钥对和salt
        server_private_key = x25519.X25519PrivateKey.generate()
        server_public_key = server_private_key.public_key()
        salt = os.urandom(16)
        logging.debug("生成salt成功")
        # 发送服务器公钥和salt（公钥32字节 + salt 16字节）
        server_pub_bytes = server_public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        conn.sendall(server_pub_bytes + salt)
        logging.debug("发送服务器公钥和salt成功")

        # 等待接收客户端公钥（32字节）
        client_public_key_bytes = conn.recv(32)
        if len(client_public_key_bytes) != 32:
            logging.error("客户端公钥长度错误")
            conn.close()
            return
        client_public_key = x25519.X25519PublicKey.from_public_bytes(client_public_key_bytes)
        logging.info("接收到客户端公钥，开始生成AES密钥")
        aes_key = generate_aes_key(server_private_key, client_public_key, salt)
        
        # 启动发送与接收线程
        recv_thread = threading.Thread(target=server_receive, args=(conn, aes_key), daemon=True)
        send_thread = threading.Thread(target=server_send, args=(conn, aes_key), daemon=True)
        recv_thread.start()
        send_thread.start()
        # 等待两个线程终止（断线或异常时跳出）
        recv_thread.join()
        send_thread.join()
    except Exception as e:
        logging.exception(f"处理连接异常：{e}")
    finally:
        try:
            conn.close()
        except:
            pass
        logging.info("会话结束，等待新连接。")

# 接收数据线程（服务器端）
def server_receive(conn, aes_key):
    message_counter = 0
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                logging.warning("【接收】连接可能已断开（数据为空）")
                break
            # 检查是否为重传请求或错误反馈
            if data.startswith(b"RESEND") or data.startswith(b"ERROR"):
                logging.warning("【接收】收到客户端错误反馈：" + data.decode('utf-8'))
                continue
            try:
                plaintext = aes_gcm_decrypt(aes_key, data)
                logging.info(f"【接收】消息 {message_counter} 收到：{plaintext.decode('utf-8')}")
            except Exception as de:
                logging.error(f"【接收】消息 {message_counter} 解密失败：{de}")
                try:
                    conn.sendall(f"RESEND {message_counter}".encode('utf-8'))
                    logging.info(f"【发送】发送重传请求：RESEND {message_counter}")
                except Exception as send_err:
                    logging.error(f"【发送】重传请求发送失败：{send_err}")
                continue
            message_counter += 1
        except Exception as e:
            logging.error(f"【接收】recv线程异常：{e}")
            break

# 发送数据线程（服务器端）
def server_send(conn, aes_key):
    while True:
        try:
            msg = input("服务器输入消息：").encode('utf-8')
            encrypted = aes_gcm_encrypt(aes_key, msg)
            conn.sendall(encrypted)
            logging.info("【发送】消息发送成功")
        except Exception as e:
            logging.error(f"【发送】发送线程异常：{e}")
            break

def server_main():
    logging.info("服务器启动，开始监听")
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # 允许重用地址，便于迅速重启
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(SERVER_ADDRESS)
                s.listen(5)
                logging.info("正在监听端口 65432...")
                # 阻塞等待客户端连接
                conn, addr = s.accept()
                # 处理新连接，若会话结束后，跳出后重新监听
                handle_connection(conn, addr)
        except Exception as e:
            logging.exception(f"服务器主流程异常：{e}")
            time.sleep(3)  # 异常等待后继续监听

if __name__ == "__main__":
    server_main()




#!/usr/bin/env python3
import socket
import threading
import os
import time
import logging
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("client.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

SERVER_ADDRESS = ('localhost', 65432)

# AES-GCM加密函数
def aes_gcm_encrypt(key, plaintext):
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    logging.debug("【加密】生成nonce、tag和密文")
    return nonce + encryptor.tag + ciphertext

# AES-GCM解密函数
def aes_gcm_decrypt(key, ciphertext):
    nonce = ciphertext[:12]
    tag = ciphertext[12:28]
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext[28:]) + decryptor.finalize()
    logging.debug("【解密】数据解密成功")
    return plaintext

# 生成AES密钥
def generate_aes_key(private_key, peer_public_key, salt):
    shared_key = private_key.exchange(peer_public_key)
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    aes_key = kdf.derive(shared_key)
    logging.debug("【密钥】AES密钥生成成功")
    return aes_key

# 重连并建立会话
def connect_to_server():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(SERVER_ADDRESS)
            logging.info("已连接到服务器")
            return s
        except Exception as e:
            logging.error(f"连接服务器失败：{e}，重试中...")
            time.sleep(3)

# 接收数据线程（客户端）
def client_receive(s, aes_key):
    while True:
        try:
            data = s.recv(4096)
            if not data:
                logging.warning("【接收】连接已断开（空数据）")
                break
            # 判断是否为重传请求或错误反馈消息
            if data.startswith(b"RESEND") or data.startswith(b"ERROR"):
                logging.warning("【接收】收到服务器反馈：" + data.decode('utf-8'))
                continue
            try:
                plaintext = aes_gcm_decrypt(aes_key, data)
                logging.info("【接收】接收到消息：" + plaintext.decode('utf-8'))
            except Exception as de:
                logging.error(f"【接收】解密失败：{de}")
                try:
                    s.sendall(b"ERROR")
                    logging.info("【发送】发送错误反馈：ERROR")
                except Exception as send_err:
                    logging.error(f"【发送】错误反馈发送异常：{send_err}")
        except Exception as e:
            logging.error(f"【接收】recv异常：{e}")
            break

# 发送数据线程（客户端）
def client_send(s, aes_key):
    message_counter = 0
    while True:
        try:
            msg = input("客户端输入消息：").encode('utf-8')
            encrypted = aes_gcm_encrypt(aes_key, msg)
            s.sendall(encrypted)
            logging.info(f"【发送】消息 {message_counter} 发送成功")
            message_counter += 1
        except Exception as e:
            logging.error(f"【发送】发送线程异常：{e}")
            break

def client_main():
    # 会话恢复相关数据可以存储在此（如未确认消息、序号等）
    while True:
        try:
            s = connect_to_server()
            # 建立新的会话：生成临时密钥对进行密钥协商
            client_private_key = x25519.X25519PrivateKey.generate()
            client_public_key = client_private_key.public_key()
            logging.info("生成客户端X25519密钥对")
            # 接收服务器发送的公钥与salt（48字节）
            data = s.recv(48)
            if len(data) != 48:
                logging.error("【会话】服务器数据格式不正确")
                s.close()
                continue
            server_public_key_bytes = data[:32]
            salt = data[32:48]
            logging.debug("收到服务器公钥和salt")
            server_public_key = x25519.X25519PublicKey.from_public_bytes(server_public_key_bytes)
            # 发送客户端公钥
            client_pub_bytes = client_public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            s.sendall(client_pub_bytes)
            logging.debug("发送客户端公钥成功")
            # 生成AES密钥，建立安全会话
            aes_key = generate_aes_key(client_private_key, server_public_key, salt)
            # 启动发送和接收线程
            recv_thread = threading.Thread(target=client_receive, args=(s, aes_key), daemon=True)
            send_thread = threading.Thread(target=client_send, args=(s, aes_key), daemon=True)
            recv_thread.start()
            send_thread.start()
            # 等待线程结束后，认为连接中断，进入重连流程
            recv_thread.join()
            send_thread.join()
            logging.info("会话断开，准备重连")
            s.close()
            time.sleep(3)
        except Exception as e:
            logging.exception(f"客户端主流程异常：{e}")
            time.sleep(3)
            continue

if __name__ == "__main__":
    client_main()


