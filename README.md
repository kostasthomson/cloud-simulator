# Cloud Simulator - Traditional Provisioning Schema

A Python-based cloud infrastructure simulator implementing the traditional provisioning approach for resource allocation and task scheduling.

## Features

- **Traditional Provisioning Schema**
  - Polling-based resource monitoring
  - First-fit allocation strategy
  - FIFO task queue management
  - All-or-nothing deployment

- **Resource Management**
  - CPU, Memory, Storage, and Accelerator tracking
  - Network bandwidth management
  - Power consumption modeling

- **Metrics & Statistics**
  - Task acceptance/rejection rates
  - Resource utilization
  - Power consumption
  - Task waiting and response times

## Project Structure

```
cloud-sim-python/
├── src/
│   └── cloud_simulator/
│       ├── __init__.py
│       ├── resource.py          # Resource management
│       ├── network.py           # Network bandwidth management
│       ├── task.py              # Task/workload representation
│       ├── statistics.py        # Metrics tracking
│       ├── traditional_broker.py # Traditional provisioning logic
│       ├── cell.py              # Datacenter cell
│       └── simulator.py         # Main simulation orchestration
├── config/
│   └── example_config.json      # Example configuration
├── output/                      # Simulation results
├── tests/                       # Unit tests
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Installation

```bash
python -m pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the simulator with the example configuration:

```bash
python main.py
```

### Custom Configuration

```bash
python main.py --config path/to/config.json --output path/to/output.json
```

### Command Line Options

- `--config`: Path to configuration JSON file (default: `config/example_config.json`)
- `--output`: Path to output results JSON file (default: `output/simulation_results.json`)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)

## Configuration

The configuration file is a JSON document that defines all simulation parameters. Here's a detailed breakdown of each section:

### 1. Simulation Parameters

```json
"simulation": {
  "max_time": 1000,
  "update_interval": 1
}
```

- **max_time**: Maximum simulation time in time units. Simulation stops when this time is reached or all tasks complete
- **update_interval**: Time between simulation timesteps. Smaller values provide finer granularity but slower execution

### 2. Broker Configuration

```json
"broker": {
  "poll_interval": 5
}
```

- **poll_interval**: How frequently (in time units) the broker updates its view of resource availability
- Between polls, the broker uses cached resource states
- Trade-off: Longer intervals are more efficient but less accurate; shorter intervals are more responsive but add overhead

### 3. Network Configuration

```json
"network": {
  "total_bandwidth": 10000.0
}
```

- **total_bandwidth**: Total network bandwidth available in the datacenter (arbitrary units)
- This bandwidth is shared across all deployed tasks
- Tasks are rejected if insufficient network bandwidth is available

### 4. Resource Types

Define different classes of servers in your datacenter. Each resource type has:

```json
{
  "type": 0,
  "num_resources": 10,
  "total_processors": 16.0,
  "total_memory": 64.0,
  "total_storage": 500.0,
  "total_accelerators": 0,
  "comp_cap_per_proc": 1000000000.0,
  "comp_cap_per_acc": 0.0,
  "overcommitment_processors": 2.0,
  "power": {
    "idle_power": 50.0,
    "peak_power_cpu": 200.0,
    "peak_power_acc": 0.0
  }
}
```

**Resource Specifications:**
- **type**: Unique identifier for this resource type (integer)
- **num_resources**: Number of identical servers of this type
- **total_processors**: Number of vCPUs per server
- **total_memory**: RAM in GB per server
- **total_storage**: Disk storage in GB per server
- **total_accelerators**: Number of GPUs/accelerators per server

**Performance Characteristics:**
- **comp_cap_per_proc**: Computing capacity per processor in instructions/second (e.g., 1000000000.0 = 1 GHz)
- **comp_cap_per_acc**: Computing capacity per accelerator in instructions/second
- **overcommitment_processors**: CPU oversubscription ratio (e.g., 2.0 allows allocating 32 vCPUs on 16 physical CPUs)

**Power Model:**
- **idle_power**: Power consumption in Watts when server is idle
- **peak_power_cpu**: Power consumption in Watts at 100% CPU utilization
- **peak_power_acc**: Power consumption in Watts per accelerator at full utilization

**Example Resource Types:**
- **Type 0 (Standard)**: 10 servers, 16 vCPUs, 64 GB RAM, no GPUs, 2.0x overcommit
- **Type 1 (High-Performance)**: 5 servers, 32 vCPUs, 128 GB RAM, 2 GPUs, 1.5x overcommit

### 5. Tasks (Workloads)

Define the workloads to simulate. Each task has:

```json
{
  "processors_per_vm": 2.0,
  "memory_per_vm": 8.0,
  "network_bandwidth": 100.0,
  "storage_per_vm": 50.0,
  "accelerators_per_vm": 0,
  "num_vms": 1,
  "total_instructions": 10000000000.0,
  "processor_utilization": 0.7,
  "memory_utilization": 0.6,
  "storage_utilization": 0.1,
  "accelerator_utilization": 0.0,
  "available_implementations": [0, 1],
  "arrival_time": 0
}
```

**Resource Requirements (per VM):**
- **processors_per_vm**: Number of vCPUs to allocate per VM
- **memory_per_vm**: RAM in GB to allocate per VM
- **network_bandwidth**: Total network bandwidth required (not per VM)
- **storage_per_vm**: Storage in GB to allocate per VM
- **accelerators_per_vm**: Number of GPUs/accelerators to allocate per VM

**Deployment Configuration:**
- **num_vms**: Number of VMs required for this task (for distributed workloads)
- **available_implementations**: List of resource types that can run this task
  - `[0, 1]`: Can run on Type 0 OR Type 1
  - `[0]`: Must run on Type 0 only
  - `[1]`: Must run on Type 1 only (e.g., requires GPUs)

**Workload Characteristics:**
- **total_instructions**: Total number of instructions to complete the task
- **processor_utilization**: Fraction of allocated CPUs actually used (0.0-1.0)
  - Example: 0.7 means using 70% of allocated CPUs (1.4 out of 2.0 vCPUs)
- **memory_utilization**: Fraction of allocated memory actually used (0.0-1.0)
- **storage_utilization**: Fraction of allocated storage actually used (0.0-1.0)
- **accelerator_utilization**: Fraction of accelerator capacity actually used (0.0-1.0)

**Timing:**
- **arrival_time**: When the task arrives in the system (time units from start)

### Configuration Examples

**Small CPU-bound task:**
```json
{
  "processors_per_vm": 2.0,
  "memory_per_vm": 8.0,
  "num_vms": 1,
  "total_instructions": 10000000000.0,
  "processor_utilization": 0.7,
  "available_implementations": [0, 1],
  "arrival_time": 0
}
```

**GPU-accelerated multi-VM task:**
```json
{
  "processors_per_vm": 4.0,
  "memory_per_vm": 16.0,
  "accelerators_per_vm": 1,
  "num_vms": 2,
  "total_instructions": 50000000000.0,
  "accelerator_utilization": 0.5,
  "available_implementations": [1],
  "arrival_time": 10
}
```

**Large distributed batch job:**
```json
{
  "processors_per_vm": 2.0,
  "memory_per_vm": 8.0,
  "num_vms": 5,
  "total_instructions": 20000000000.0,
  "processor_utilization": 0.6,
  "available_implementations": [0, 1],
  "arrival_time": 100
}
```

### Key Concepts

**Allocation vs Utilization:**
- **Allocation**: Resources reserved/requested for the task
- **Utilization**: Percentage of allocated resources actually used
- Lower utilization means wasted resources but provides headroom for bursts

**Overcommitment:**
- Allows allocating more virtual resources than physical capacity
- Example: 2.0x overcommit = can allocate 32 vCPUs on 16 physical CPUs
- Performance degrades when overcommitted resources are heavily utilized
- Higher utilization under overcommitment causes more performance degradation

**First-Fit Allocation:**
- The traditional broker searches resources in order (ID 0, 1, 2, ...)
- Allocates to the first resource with sufficient capacity
- No optimization for load balancing or energy efficiency

**All-or-Nothing Deployment:**
- All VMs must be successfully allocated for the task to be accepted
- If any VM fails to allocate, the entire task is rejected
- Previously allocated VMs for that task are rolled back

See `config/example_config.json` for a complete working example.

## Output

Results are saved as JSON containing:

- Simulation configuration and end time
- Resource states (available/total capacity)
- Statistics (accepted/rejected tasks, power consumption, etc.)
- Broker state (queue length)

## Architecture

### Traditional Provisioning Schema

The implementation mirrors the CloudLightning simulator's traditional broker:

1. **Polling-Based Monitoring**: Resources are polled at fixed intervals
2. **First-Fit Allocation**: Tasks are allocated to the first available resource
3. **All-or-Nothing**: Tasks require all VMs to be allocated or are rejected
4. **FIFO Queue**: Tasks are processed in order of arrival

### Key Components

- **Resource**: Represents compute nodes with CPU, memory, storage, accelerators
- **Network**: Manages bandwidth allocation
- **Task**: Workload with resource requirements and execution characteristics
- **TraditionalBroker**: Implements the provisioning logic
- **Cell**: Container for all datacenter resources
- **Simulator**: Main orchestration and event loop

## Example

```python
from cloud_simulator import Simulator

sim = Simulator("config/example_config.json")
results = sim.run()
sim.save_results("output/results.json")
```

## License

Apache License 2.0
