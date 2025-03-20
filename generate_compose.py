import sys
import yaml
from copy import deepcopy

def generate_compose(input_file, output_file, num_clients):
    with open(input_file, 'r') as f:
        compose_data = yaml.safe_load(f)
    
    client_template = deepcopy(compose_data['services']['client1'])
    
    for i in range(2, num_clients + 1):
        new_client = deepcopy(client_template)
        new_client['container_name'] = f'client{i}'
        new_client['environment'] = [f'CLI_ID={i}', 'CLI_LOG_LEVEL=DEBUG']
        compose_data['services'][f'client{i}'] = new_client
    
    with open(output_file, 'w') as f:
        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False, indent=2)

def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_compose.py <output_filename> <number_of_clients>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    try:
        n_clients = int(sys.argv[2])
        if n_clients < 1:
            raise ValueError(f"{n_clients} is not a positive number.")
    except ValueError as e:
        print(f"Error parsing number of clients: {e}")
        print("The second argument must be a positive integer")
        sys.exit(1)
    
    generate_compose('docker-compose-dev.yaml', output_file, n_clients)
    print(f"Generated {output_file} with {n_clients} client services")

if __name__ == "__main__":
    main()
