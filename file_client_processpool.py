import socket
import json
import base64
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor
import argparse
from multiprocessing import Manager

class FileClient:
    def __init__(self, server_ip, server_port):
        self.server_address = (server_ip, server_port)
        self.timeout = 300  # 5 minutes timeout for large files

    def send_command(self, command_str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(self.server_address)
            sock.sendall((command_str + "\r\n\r\n").encode())
            
            data_received = ""
            while True:
                data = sock.recv(1024 * 1024)  # 64KB buffer
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            
            json_response = data_received.split("\r\n\r\n")[0]
            return json.loads(json_response)
        except Exception as e:
            return {"status": "ERROR", "data": str(e)}
        finally:
            sock.close()

    def remote_get(self, filename):
        start_time = time.time()
        result = self.send_command(f"GET {filename}")
        if result["status"] == "OK":
            try:
                namafile = result["data_namafile"]
                isifile = base64.b64decode(result["data_file"])
                with open(namafile, "wb+") as fp:
                    fp.write(isifile)
                elapsed = time.time() - start_time
                return True, elapsed, os.path.getsize(namafile)
            except Exception as e:
                return False, 0, 0
        return False, 0, 0

    def remote_upload(self, filename):
        start_time = time.time()
        if not os.path.exists(filename):
            return False, 0, 0
        
        try:
            with open(filename, "rb") as fp:
                file_size = os.path.getsize(filename)
                encoded = base64.b64encode(fp.read()).decode()
            
            result = self.send_command(f"UPLOAD {filename} {encoded}")
            elapsed = time.time() - start_time
            
            if result and result.get("status") == "OK":
                return True, elapsed, file_size
            return False, 0, 0
        except Exception as e:
            return False, 0, 0

def worker(server_ip, server_port, task):
    client = FileClient(server_ip, server_port)
    operation, filename = task
    if operation == "download":
        return client.remote_get(filename)
    elif operation == "upload":
        return client.remote_upload(filename)
    return False, 0, 0

def stress_test(server_ip, server_port, operation, filename, num_workers):
    tasks = [(operation, filename) for _ in range(num_workers)]
    
    start_time = time.time()
    results = []
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker, server_ip, server_port, task) for task in tasks]
        for future in futures:
            results.append(future.result())
    
    total_time = time.time() - start_time
    successes = sum(1 for result in results if result[0])
    failures = len(results) - successes
    
    # Calculate throughput
    if operation in ["download", "upload"] and successes > 0:
        total_bytes = sum(result[2] for result in results if result[0])
        throughput = total_bytes / total_time
    else:
        throughput = 0
    
    return {
        "operation": operation,
        "file_size": os.path.getsize(filename) if filename and os.path.exists(filename) else 0,
        "num_workers": num_workers,
        "total_time": total_time,
        "throughput": throughput,
        "successes": successes,
        "failures": failures
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", default="172.16.16.101")
    parser.add_argument("--server-port", type=int, default=6667)
    parser.add_argument("--operation", choices=["download", "upload"], required=True)
    parser.add_argument("--filename")
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()
    
    if args.operation in ["download", "upload"] and not args.filename:
        print("Filename is required for download/upload operations")
        exit(1)
    
    logging.basicConfig(level=logging.WARNING)
    result = stress_test(args.server_ip, args.server_port, args.operation, args.filename, args.workers)
    
    print("\nStress Test Results:")
    print(f"Operation: {result['operation']}")
    if args.operation in ["download", "upload"]:
        print(f"File Size: {result['file_size']/1024/1024:.2f} MB")
    print(f"Workers: {result['num_workers']}")
    print(f"Total Time: {result['total_time']:.2f} seconds")
    if args.operation in ["download", "upload"]:
        print(f"Throughput: {result['throughput']/1024/1024:.2f} MB/s")
    print(f"Successes: {result['successes']}")
    print(f"Failures: {result['failures']}")