import os
from grpc_tools import protoc

# Define base paths
root_dir = "."  # Current directory (root of the project)
proto_dirs = [
    "microservices/transaction_verification/src",
    "microservices/fraud_detection/src",
    "microservices/suggestions/src"
]
output_base_dir = os.path.join(root_dir, "utils", "pb")  # Output directory for generated files

# Ensure the output base directory exists
os.makedirs(output_base_dir, exist_ok=True)

# Process each proto directory
for proto_dir in proto_dirs:
    full_proto_dir = os.path.join(root_dir, proto_dir)
    
    # Get all .proto files in the directory
    proto_files = [f for f in os.listdir(full_proto_dir) if f.endswith('.proto')]
    
    for proto_file in proto_files:
        print(f"Generating code for {proto_dir}/{proto_file}...")
        
        # Create a subdirectory for the service in the output directory
        service_name = os.path.basename(proto_dir)  # e.g., "fraud_detection"
        service_output_dir = os.path.join(output_base_dir, service_name)
        os.makedirs(service_output_dir, exist_ok=True)
        
        # Run protoc compiler
        protoc.main([
            'grpc_tools.protoc',
            f'-I={full_proto_dir}',  # Proto file directory
            f'--python_out={service_output_dir}',  # Output directory for _pb2.py
            f'--grpc_python_out={service_output_dir}',  # Output directory for _pb2_grpc.py
            os.path.join(full_proto_dir, proto_file)  # Path to the .proto file
        ])
        print(f"Generated pb2 and pb2_grpc files for {proto_file} in {service_output_dir}")

print("All protobuf files generated successfully!")