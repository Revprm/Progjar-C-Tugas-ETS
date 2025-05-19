import os
import time
import csv
from datetime import datetime
from file_client_processpool import stress_test

class StressTestAutomatorProcessPool:
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

    def run_single_test(self, operation, filename, client_workers):
        """Run a single stress test using ProcessPoolExecutor"""
        file_size = os.path.getsize(filename)
        print(f"\n{operation.upper()} | File: {filename} | Size: {file_size / 1024 / 1024:.2f} MB | Workers: {client_workers}")

        # execute stress test
        result = stress_test(
            self.server_ip,
            self.server_port,
            operation,
            filename,
            client_workers
        )

        # normalize and enrich result
        successes = result.get('successes', 0)
        failures = result.get('failures', 0)
        record = {
            'timestamp': datetime.now().isoformat(),
            'operation': result.get('operation'),
            'volume': f"{file_size // (1024*1024)} MB",
            'client_workers': result.get('num_workers'),
            'total_time': round(result.get('total_time', 0), 2),
            'throughput': round((result.get('throughput', 0) / (1024*1024)), 2),
            'client_success': successes,
            'client_fail': failures,
            'server_success': successes,  # Placeholder, replace with actual server metrics if available
            'server_fail': failures     # Placeholder, replace with actual server metrics if available
        }
        self.results.append(record)
        self.print_result_summary(record)
        return record

    def print_result_summary(self, result):
        """Print formatted test results"""
        print("\nTest Completed:")
        print(f"Operation:       {result['operation'].upper()}")
        print(f"File Volume:     {result['volume']}")
        print(f"Workers:         {result['client_workers']}")
        print(f"Total Time:      {result['total_time']} seconds")
        print(f"Throughput:      {result['throughput']} MB/s")
        print(f"Client Success:  {result['client_success']}")
        print(f"Client Fail:     {result['client_fail']}")
        print(f"Server Success:  {result['server_success']}")
        print(f"Server Fail:     {result['server_fail']}")

    def run_full_test_suite(self):
        """Run all test combinations"""
        if not self.prepare_test_files():
            return False

        operations = ['download', 'upload']
        volumes = ['small', 'medium', 'large']
        workers_list = [1, 5, 50]
        combo_num = 1
        total = len(operations) * len(volumes) * len(workers_list)

        for operation in operations:
            for volume in volumes:
                for workers in workers_list:
                    print(f"\nRunning test {combo_num}/{total} ...")
                    filename = self.test_files[volume]
                    self.run_single_test(operation, filename, workers)
                    time.sleep(5)
                    combo_num += 1
        return True

    def save_results_to_csv(self, filename="stress_test_results_processpool.csv"):
        """Save all results to CSV"""
        if not self.results:
            print("No results to save")
            return False

        fieldnames = [
            'timestamp', 'operation', 'volume', 'client_workers',
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
            print(f"Error saving results: {e}")
            return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ProcessPool-based Stress Test Automator")
    parser.add_argument("--server-ip", default="172.16.16.101", help="Server IP address")
    parser.add_argument("--server-port", type=int, default=6667, help="Server port")
    parser.add_argument("--single-test", action="store_true", help="Run single test")
    parser.add_argument("--operation", choices=["upload", "download"], help="Operation to test")
    parser.add_argument("--file-size", choices=["small", "medium", "large"], help="File size to test")
    parser.add_argument("--workers", type=int, help="Number of worker processes")
    parser.add_argument("--output", default="stress_test_results_processpool.csv", help="Output CSV filename")
    args = parser.parse_args()

    automator = StressTestAutomatorProcessPool(args.server_ip, args.server_port)

    if args.single_test:
        if not all([args.operation, args.file_size, args.workers]):
            print("Error: --operation, --file-size, and --workers required for single test")
            exit(1)
        filename = automator.test_files[args.file_size]
        automator.run_single_test(args.operation, filename, args.workers)
    else:
        print("Running full test suite with ProcessPool...")
        automator.run_full_test_suite()

    automator.save_results_to_csv(args.output)
