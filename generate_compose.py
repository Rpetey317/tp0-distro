import sys
from copy import deepcopy

# this is so overkill

def read_compose_file(filename: str) -> dict:
    with open(filename, 'r') as f:
        lines = f.readlines()

    result = {}
    current_dict = result
    indent_stack = [(0, current_dict)]
    in_array = False
    current_array = []
    array_indent = 0
    
    for line in lines:
        if not line.strip() or line.strip().startswith('#'):
            continue
            
        indent = len(line) - len(line.lstrip())
        line = line.strip()
        
        if line == '-':
            in_array = True
            array_indent = indent
            continue
            
        if line.startswith('- '):
            in_array = True
            array_indent = indent
            line = line[2:]
            current_array.append(line)
            continue

        if in_array and indent == array_indent:
            current_array.append(line)
            continue
            
        if in_array and indent < array_indent:
            in_array = False
            current_dict[list(current_dict.keys())[-1]] = current_array
            current_array = []
            
        if ':' in line:
            key, value = [x.strip() for x in line.split(':', 1)]
            
            while indent_stack and indent <= indent_stack[-1][0]:
                indent_stack.pop()
                
            current_dict = indent_stack[-1][1] if len(indent_stack) > 0 else result

            if value:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
            
            if not value:
                current_dict[key] = {}
                indent_stack.append((indent, current_dict[key]))
            else:
                current_dict[key] = value

    if in_array:
        current_dict[list(current_dict.keys())[-1]] = current_array
                
    print(result)
    return result

def write_compose_file(services, output_file, num_clients):
    def write_dict(f, d, indent=0):
        for key, value in d.items():
            if isinstance(value, dict):
                f.write(" " * indent + f"{key}:\n")
                write_dict(f, value, indent + 2)
            elif isinstance(value, list):
                f.write(" " * indent + f"{key}:\n")
                for item in value:
                    f.write(" " * (indent+2) + f"- {item}\n")
            else:
                if isinstance(value, str) and (" " in value or ":" in value):
                    f.write(" " * indent + f'{key}: "{value}"\n')
                else:
                    f.write(" " * indent + f"{key}: {value}\n")

    with open(output_file, 'w') as f:
        if "name" in services:
            f.write(f"name: {services['name']}\n")
        
        f.write("services:\n")
        
        services["services"]["server"]["environment"] = [x for x in services["services"]["server"]["environment"] if not x.startswith("N_AGENCIES")]
        services["services"]["server"]["environment"].append(f"N_AGENCIES={num_clients}")
        
        f.write("  server:\n")
        write_dict(f, services["services"]["server"], 4)
        f.write("\n")
        
        client_template = services["services"]["client1"]
        for i in range(1, num_clients + 1):
            client = deepcopy(client_template)
            client["container_name"] = f"client{i}"
            client["environment"] = [x for x in client["environment"] if not x.startswith("CLI_ID")]
            client["environment"].append(f"CLI_ID={i}")
            client["volumes"].pop()
            client["volumes"].append(f"./.data/agency-{i}.csv:/data.csv")
            
            f.write(f"  client{i}:\n")
            write_dict(f, client, 4)
            f.write("\n")
            
        f.write("networks:\n")
        write_dict(f, services["networks"], 2)

def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_compose.py <output_filename> <number_of_clients>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    try:
        n_clients = int(sys.argv[2])
        if n_clients < 0:
            raise ValueError(f"{n_clients} is a negative number.")
    except ValueError as e:
        print(f"Error parsing number of clients: {e}")
        print("The second argument must be a non-negative integer")
        sys.exit(1)
    
    compose_dict = read_compose_file('docker-compose-dev.yaml')
    write_compose_file(compose_dict, output_file, n_clients)
    print(f"Generated {output_file} with {n_clients} client services")

if __name__ == "__main__":
    main()
