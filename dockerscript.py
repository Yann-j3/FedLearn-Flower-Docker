import subprocess
import sys

def run_command(command):
    """Helper function to run a shell command."""
    print(f"Running command: {command}")
    subprocess.run(command, shell=True, check=False)  # Use check=False to avoid throwing errors on failure

def stop_and_remove_all_containers():
    """Stop and remove all running containers."""
    # Stop all containers only if any are running
    containers = subprocess.run("docker ps -q", shell=True, capture_output=True, text=True)
    if containers.stdout.strip():  # If there are running containers
        run_command(f"docker stop {containers.stdout.strip()}")

    # Remove all containers only if any exist
    all_containers = subprocess.run("docker ps -a -q", shell=True, capture_output=True, text=True)
    if all_containers.stdout.strip():  # If there are containers to remove
        run_command(f"docker rm {all_containers.stdout.strip()}")

def create_flwr_network():
    """Create the Flower network if it doesn't exist."""
    run_command("docker network create --driver bridge flwr-network")

def start_superlink():
    run_command("docker run --rm -p 9091:9091 -p 9092:9092 -p 9093:9093 --network flwr-network --name superlink --detach flwr/superlink:1.14.0 --insecure --isolation process")

def start_supernode():
    """Start the SuperNode container if it isn't already running."""
    run_command("docker run --rm -p 9094:9094 --network flwr-network --name supernode-1 --detach flwr/supernode:1.14.0 --insecure --superlink superlink:9092 --node-config \"partition-id=0 num-partitions=1\" --clientappio-api-address 0.0.0.0:9094 --isolation process")

def build_and_run_server():
    """Build and run the server container."""
    run_command("docker build -f serverapp.Dockerfile -t flwr_serverapp:0.0.1 .")
    run_command("docker run --rm --network flwr-network --name serverapp --detach flwr_serverapp:0.0.1 --insecure --serverappio-api-address superlink:9091")

def build_and_run_clients(num_clients):
    """Build and run the specified number of client containers."""
    run_command("docker build -f clientapp.Dockerfile -t flwr_clientapp:0.0.1 .")
    
    # All clients will be assigned to supernode-1
    for i in range(1, num_clients + 1):
        try:
            run_command(f"docker ps -q -f name=clientapp-{i}")  # Check if the client container is already running
            print(f"Client container clientapp-{i} already running.")
        except subprocess.CalledProcessError:
            port = 9094 + i  # Port assignment for client
            run_command(f"docker run --rm --network flwr-network --name clientapp-{i} --detach flwr_clientapp:0.0.1 --insecure --clientappio-api-address supernode-1:9094")

def main(num_clients):
    """Main function to set up the entire federated learning environment."""
    stop_and_remove_all_containers()  # Stop and remove all containers before starting fresh
    create_flwr_network()
    start_superlink()

    # Start a single SuperNode
    start_supernode()

    # Build and run the server
    build_and_run_server()

    # Build and run the clients dynamically based on the number of clients
    build_and_run_clients(num_clients)

if __name__ == "__main__":
    # Default to 2 clients if no argument is provided
    num_clients = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    main(num_clients)
