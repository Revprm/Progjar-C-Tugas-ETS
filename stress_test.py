import os
import time
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from file_client_threadpool import FileClient  # Your existing client class

class StressTestAutomator:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.results = []
        self.test_files = {
            'small': 'test_10mb.dat',
            'medium': 'test_50mb.dat',
            'large': 'test_100mb.dat'
        }
        
    def prepare_test_files(self):
        """Ensure test files exist"""
        for size, filename in self.test_files.items():
            if not os.path.exists(filename):
                print(f"Error: Test file {filename} not found")
                return False
        return True
    
    def run_single_test(self, operation, filename, client_workers, server_workers):
        """Run a single stress test with specified client/server workers"""
        file_size = os.path.getsize(filename)
        print(f"\n{operation.upper()} | File: {filename} | Size: {file_size / 1024 / 1024:.2f} MB | Clients: {client_workers} | Server Pool: {server_workers}")
        
        client = FileClient(self.server_ip, self.server_port)

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=client_workers) as executor:
            futures = []
            for _ in range(client_workers):
                if operation == "upload":
                    futures.append(executor.submit(client.remote_upload, filename))
                else:
                    futures.append(executor.submit(client.remote_get, filename))

            results = [future.result() for future in futures]

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r[0])
        fail_count = client_workers - success_count
        total_bytes = sum(r[2] for r in results if r[0])
        throughput_bps = total_bytes / total_time if total_time > 0 else 0
        throughput_mbps = throughput_bps / (1024 * 1024)
        avg_time = sum(r[1] for r in results) / client_workers if client_workers > 0 else 0

        result = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'volume': f"{file_size // (1024*1024)} MB",
            'client_workers': client_workers,
            'server_workers': server_workers,
            'total_time': round(total_time, 2),
            'throughput': round(throughput_mbps, 2),  # MB/s
            'client_success': success_count,
            'client_fail': fail_count,
            'server_success': success_count,  # Placeholder, replace with actual server stats if available
            'server_fail': fail_count,     # Placeholder
        }
        self.results.append(result)
        self.print_result_summary(result)
        return result
    
    def print_result_summary(self, result):
        """Print formatted test results"""
        print("\nTest Completed:")
        print(f"Operation:       {result['operation'].upper()}")
        print(f"File Volume:     {result['volume']}")
        print(f"Client Workers:  {result['client_workers']}")
        print(f"Server Workers:  {result['server_workers']}")
        print(f"Total Time:      {result['total_time']} seconds")
        print(f"Throughput:      {result['throughput']} MB/s")
        print(f"Client Success:  {result['client_success']} / {result['client_workers']}")
        print(f"Client Fail:     {result['client_fail']}")
        print(f"Server Success:  {result['server_success']} / {result['server_success']}")
        print(f"Server Fail:     {result['server_fail']}")
    
    def run_full_test_suite(self):
        """Run all test combinations"""
        if not self.prepare_test_files():
            return False
        
        operations = ['download', 'upload']
        volumes = ['small', 'medium', 'large']
        client_workers_list = [1, 5, 50]
        server_workers_list = [1]
        
        combo_num = 1
        total_combinations = len(operations) * len(volumes) * len(client_workers_list) * len(server_workers_list)
        
        for operation in operations:
            for volume in volumes:
                for client_workers in client_workers_list:
                    for server_workers in server_workers_list:
                        print(f"\nRunning test {combo_num}/{total_combinations} ...")
                        filename = self.test_files[volume]
                        self.run_single_test(operation, filename, client_workers, server_workers)
                        time.sleep(5)  # brief pause between tests
                        combo_num += 1
        
        return True
    
    def save_results_to_csv(self, filename="stress_test_results.csv"):
        """Save all results to CSV file"""
        if not self.results:
            print("No results to save")
            return False
        
        fieldnames = [
            'timestamp', 'operation', 'volume', 'client_workers', 'server_workers',
            'total_time', 'throughput', 'client_success', 'client_fail',
            'server_success', 'server_fail'
        ]
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            print(f"\nResults saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving results: {str(e)}")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated File Server Stress Test")
    parser.add_argument("--server-ip", default="172.16.16.101", help="Server IP address")
    parser.add_argument("--server-port", type=int, default=6667, help="Server port")
    parser.add_argument("--single-test", action="store_true", help="Run single test")
    parser.add_argument("--operation", choices=["upload", "download"], help="Operation to test")
    parser.add_argument("--file-size", choices=["small", "medium", "large"], help="File size to test")
    parser.add_argument("--client-workers", type=int, help="Number of client worker threads")
    parser.add_argument("--server-workers", type=int, default=1, help="Number of server worker threads (informative)")
    parser.add_argument("--output", default="stress_test_results.csv", help="Output CSV filename")
    
    args = parser.parse_args()
    
    automator = StressTestAutomator(args.server_ip, args.server_port)
    
    if args.single_test:
        if not all([args.operation, args.file_size, args.client_workers]):
            print("Error: --operation, --file-size, and --client-workers required for single test")
            exit(1)
        
        filename = automator.test_files[args.file_size]
        automator.run_single_test(args.operation, filename, args.client_workers, args.server_workers)
    else:
        print("Running full test suite...")
        automator.run_full_test_suite()
    
    automator.save_results_to_csv(args.output)
