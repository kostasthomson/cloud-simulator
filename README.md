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

The configuration file defines:

- **Simulation parameters**: max_time, update_interval
- **Broker settings**: poll_interval
- **Network**: total_bandwidth
- **Resource types**: CPU, memory, storage, accelerators, power models
- **Tasks**: workload specifications, arrival times, resource requirements

See `config/example_config.json` for a complete example.

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
