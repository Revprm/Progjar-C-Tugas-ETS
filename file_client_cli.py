import socket
import json
import base64
import logging
import os

server_address = ("0.0.0.0", 7777)


def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message ")
        sock.sendall((command_str + "\r\n\r\n").encode())
        data_received = "" 
        while True:
            data = sock.recv(16)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        json_response = data_received.split("\r\n\r\n")[0]
        hasil = json.loads(json_response)
        logging.warning("data received from server:")
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving: {str(e)}")
        return False


def remote_list():
    command_str = f"LIST"
    hasil = send_command(command_str)
    if hasil["status"] == "OK":
        print("daftar file : ")
        for nmfile in hasil["data"]:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False


def remote_get(filename=""):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil["status"] == "OK":
        # proses file dalam bentuk base64 ke bentuk bytes
        namafile = hasil["data_namafile"]
        isifile = base64.b64decode(hasil["data_file"])
        fp = open(namafile, "wb+")
        fp.write(isifile)
        fp.close()
        return True
    else:
        print("Gagal")
        return False


def remote_upload(filename=""):
    if not os.path.exists(filename):
        print("File tidak ditemukan.")
        return False
    with open(filename, "rb") as fp:
        encoded = base64.b64encode(fp.read()).decode()
    command_str = f"UPLOAD {filename} {encoded}"
    hasil = send_command(command_str)
    if hasil and hasil.get("status") == "OK":
        print(f"File '{filename}' berhasil diunggah.")
        return True
    else:
        print("Gagal:", hasil.get("data", "Unknown error"))
        return False


def remote_delete(filename=""):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if hasil and hasil.get("status") == "OK":
        print(f"File '{filename}' berhasil dihapus.")
        return True
    else:
        print("Gagal:", hasil.get("data", "Unknown error"))
        return False


if __name__ == "__main__":
    server_address = ("172.16.16.101", 6667)
    # remote_list()
    #remote_get("donalbebek.jpg")
    remote_upload("GCyuDhMaEAAlAby.jpg")
    #remote_delete("contoh.txt")
