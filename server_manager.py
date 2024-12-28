#!/usr/bin/env python3

import subprocess
import socket
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import os
import signal

@dataclass
class ServerInfo:
    pid: int
    port: int
    name: str
    command: str

class ServerManager:
    def __init__(self):
        self.monitored_ports = [8000, 8002, 3000, 5000]  # Common development server ports

    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def get_process_by_port(self, port: int) -> Optional[ServerInfo]:
        """Get the process using a specific port using lsof."""
        try:
            # Run lsof command to get process information
            cmd = ['lsof', '-i', f':{port}', '-sTCP:LISTEN', '-n', '-P']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return None

            # Parse lsof output (skip header line)
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return None

            # Parse the first process line
            parts = lines[1].split()
            if len(parts) < 2:
                return None

            pid = int(parts[1])
            name = parts[0]

            # Get full command
            cmd = ['ps', '-p', str(pid), '-o', 'command=']
            result = subprocess.run(cmd, capture_output=True, text=True)
            command = result.stdout.strip()

            return ServerInfo(
                pid=pid,
                port=port,
                name=name,
                command=command
            )
        except (subprocess.SubprocessError, ValueError, IndexError):
            return None

    def get_running_servers(self) -> List[ServerInfo]:
        """Get information about all running servers on monitored ports."""
        servers = []
        for port in self.monitored_ports:
            if self.is_port_in_use(port):
                server_info = self.get_process_by_port(port)
                if server_info:
                    servers.append(server_info)
        return servers

    def stop_server(self, pid: int) -> bool:
        """Stop a server by its PID."""
        try:
            # First try SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            
            # Wait a bit to see if the process exits
            for _ in range(10):
                try:
                    os.kill(pid, 0)  # Check if process exists
                    subprocess.run(['sleep', '0.5'])
                except ProcessLookupError:
                    return True
            
            # If process still exists, force kill with SIGKILL
            try:
                os.kill(pid, signal.SIGKILL)
                return True
            except ProcessLookupError:
                return True  # Process already terminated
            
        except ProcessLookupError:
            return False
        except PermissionError:
            print(f"Permission denied when trying to stop process {pid}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Manage local development servers')
    parser.add_argument('--list', action='store_true', help='List all running servers')
    parser.add_argument('--stop', type=int, help='Stop server by PID')
    parser.add_argument('--stop-port', type=int, help='Stop server by port')
    parser.add_argument('--stop-all', action='store_true', help='Stop all running servers')

    args = parser.parse_args()
    manager = ServerManager()

    if args.list or (not any([args.stop, args.stop_port, args.stop_all])):
        servers = manager.get_running_servers()
        if not servers:
            print("No servers running on monitored ports.")
            return

        print("\nRunning Servers:")
        print("-" * 100)
        print(f"{'PID':<8} {'Port':<6} {'Name':<15} {'Command'}")
        print("-" * 100)
        
        for server in servers:
            print(f"{server.pid:<8} {server.port:<6} {server.name[:15]:<15} {server.command}")
        print()

    if args.stop:
        if manager.stop_server(args.stop):
            print(f"Successfully stopped server with PID {args.stop}")
        else:
            print(f"Failed to stop server with PID {args.stop}")

    if args.stop_port:
        server_info = manager.get_process_by_port(args.stop_port)
        if server_info and manager.stop_server(server_info.pid):
            print(f"Successfully stopped server on port {args.stop_port}")
        else:
            print(f"Failed to stop server on port {args.stop_port}")

    if args.stop_all:
        servers = manager.get_running_servers()
        for server in servers:
            if manager.stop_server(server.pid):
                print(f"Stopped server on port {server.port} (PID: {server.pid})")
            else:
                print(f"Failed to stop server on port {server.port} (PID: {server.pid})")

if __name__ == "__main__":
    main()
