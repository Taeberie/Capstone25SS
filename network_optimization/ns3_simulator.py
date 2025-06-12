import subprocess
import os

def simulate_ns3_path(path):
    bin_path = os.path.join('build', 'route_simulation')
    print(f"[NS-3] simulate path: {path}")
    subprocess.run([bin_path, f"--path={path}"], check=True)

def simulate_allocation(allocation, paths):
    for srv, f in allocation.items():
        if f <= 0: continue
        path = paths[srv]
        print(f"[NS-3] Simulate {srv} flow={f}")
        simulate_ns3_path('-'.join(path))