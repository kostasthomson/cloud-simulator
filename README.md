# Smart Task Allocator for Cloud Simulation

A machine learning-based task allocation service for HPC cloud simulation environments. This service provides intelligent resource allocation decisions to minimize operational costs (electricity consumption) while respecting resource constraints.

## Overview

The Smart Task Allocator is a FastAPI-based REST service that integrates with a C++ cloud simulator. It receives allocation requests containing system state and task requirements, then returns optimal placement decisions based on energy efficiency heuristics.

**Current Implementation**: Heuristic-based energy-aware allocation  
**Future Enhancements**: Machine learning models, reinforcement learning agents

## Architecture

```
smart_allocator/
├── main.py                      # FastAPI application entry point
├── models/
│   ├── schemas.py              # Pydantic models for validation
│   └── allocation.py           # Core allocation data structures
├── services/
│   ├── allocator.py            # Main allocation logic
│   └── energy_calculator.py   # Energy estimation utilities
├── config/
│   └── settings.py             # Configuration management
└── utils/
    └── logger.py               # Logging setup
```

## Features

### Current (v1.0)
- ✅ Energy-aware heuristic allocation
- ✅ Multi-cell, multi-hardware-type support
- ✅ CPU, GPU, DFE, MIC implementation compatibility
- ✅ Resource capacity constraint validation
- ✅ Power consumption modeling and estimation
- ✅ RESTful API with comprehensive validation
- ✅ Structured logging (JSON format)
- ✅ Statistics tracking

### Planned (Future)
- 🔄 Supervised learning for workload prediction
- 🔄 Reinforcement learning for adaptive allocation
- 🔄 Historical data collection and analysis
- 🔄 Multi-objective optimization
- 🔄 Task migration support

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

Run the script ``quickstart.sh`` at the root level. Or manually:

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment (optional):**
   Create `.env` file:
   ```env
   ALLOCATOR_APP_NAME=Smart Task Allocator
   ALLOCATOR_API_PORT=8000
   ALLOCATOR_LOG_LEVEL=INFO
   ALLOCATOR_MODEL_TYPE=heuristic_energy_aware
   ```

## Usage

### Starting the Service

**Development mode (with auto-reload):**
```bash
python main.py
```

**Production mode:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The service will be available at `http://localhost:8000`

### API Endpoints

#### 1. Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_type": "heuristic_energy_aware"
}
```

#### 2. Allocate Task (Main Endpoint)
```bash
POST /allocate_task
Content-Type: application/json
```

Request body:
```json
{
  "timestamp": 100.0,
  "cells": [
    {
      "cell_id": 1,
      "hw_types": [
        {
          "hw_type_id": 1,
          "hw_type_name": "CPU",
          "num_servers": 25000,
          "num_cpus_per_server": 20,
          "memory_per_server": 128.0,
          "storage_per_server": 1.0,
          "compute_capability": 88000.8,
          "accelerators": 0,
          "num_accelerators_per_server": 0,
          "accelerator_compute_capability": 0.0,
          "cpu_power_consumption": [163, 170.1, 172.6, 175.4, 179.8, 183.6, 190.0, 196.8, 206.3, 215.9, 220.2],
          "cpu_utilization_bins": [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
          "cpu_idle_power": 163.0,
          "accelerator_idle_power": 0.0,
          "accelerator_max_power": 0.0
        }
      ],
      "available_resources": {
        "1": {
          "cpu": 500000.0,
          "memory": 3200000.0,
          "storage": 25000.0,
          "network": 20.0,
          "accelerators": 0
        }
      },
      "current_utilization": {
        "1": {
          "cpu": 0.0,
          "memory": 0.0,
          "network": 0.0
        }
      }
    }
  ],
  "task": {
    "task_id": "task_001",
    "application_id": 1,
    "implementation_id": 1,
    "num_vms": 2,
    "vcpus_per_vm": 4,
    "memory_per_vm": 8.0,
    "storage_per_vm": 0.02,
    "network_per_vm": 0.0025,
    "requires_accelerator": false,
    "accelerator_utilization": 0.0,
    "estimated_duration": 3600.0
  }
}
```

Response (Success):
```json
{
  "success": true,
  "cell_id": 1,
  "hw_type_id": 1,
  "estimated_energy_cost": 0.1525,
  "reason": "Selected CPU in Cell 1 for optimal energy efficiency (Est: 0.1525 kWh)",
  "allocation_method": "heuristic_energy_aware",
  "timestamp": 100.0
}
```

Response (Rejection):
```json
{
  "success": false,
  "cell_id": null,
  "hw_type_id": null,
  "estimated_energy_cost": null,
  "reason": "No suitable resources available in any cell",
  "allocation_method": "heuristic_energy_aware",
  "timestamp": 100.0
}
```

#### 3. Get Statistics
```bash
GET /statistics
```

Response:
```json
{
  "status": "success",
  "statistics": {
    "total_allocations": 1520,
    "rejections": 45,
    "success_rate": 97.04
  }
}
```

## Integration with C++ Simulator

### Communication Flow

1. **C++ Simulator** generates task arrival event
2. **Simulator** composes JSON request with:
   - Current system state (all cells, resources)
   - Task requirements
3. **Simulator** sends HTTP POST to `/allocate_task`
4. **Allocator Service** processes request and returns decision
5. **Simulator** applies allocation or handles rejection

### C++ Integration Example

Using `libcurl` or `cpp-httplib`:

```cpp
#include <cpp-httplib/httplib.h>
#include <nlohmann/json.hpp>

// Create HTTP client
httplib::Client client("localhost", 8000);

// Compose request
nlohmann::json request = {
    {"timestamp", current_time},
    {"cells", cells_state},
    {"task", task_requirements}
};

// Send POST request
auto response = client.Post(
    "/allocate_task",
    request.dump(),
    "application/json"
);

// Parse response
if (response && response->status == 200) {
    auto decision = nlohmann::json::parse(response->body);

    if (decision["success"]) {
        int cell_id = decision["cell_id"];
        int hw_type_id = decision["hw_type_id"];
        // Apply allocation
        allocate_task_to_server(cell_id, hw_type_id, task);
    } else {
        // Handle rejection
        reject_task(task, decision["reason"]);
    }
}
```

## Algorithm Details

### Heuristic Energy-Aware Allocation

The current allocation algorithm follows these steps:

1. **Compatibility Check**: Filter hardware types compatible with task implementation
   - Implementation 1 (CPU): Can run on any HW
   - Implementation 2 (GPU): Requires GPU accelerators
   - Implementation 3 (DFE): Requires DFE accelerators
   - Implementation 4 (MIC): Requires MIC accelerators

2. **Resource Availability Check**: Ensure sufficient CPU, memory, storage, network, and accelerators

3. **Energy Estimation**: For each candidate:
   - Interpolate CPU power consumption based on utilization
   - Calculate accelerator power (if applicable)
   - Estimate total energy: `(Power × Duration) / 3,600,000` kWh

4. **Efficiency Scoring**: Calculate resource availability score

5. **Selection**: Choose candidate with lowest combined energy-efficiency score

### Energy Calculation

CPU power is interpolated from utilization bins:
```
P_cpu = interpolate(utilization, bins, power_values)
```

Accelerator power (linear model):
```
P_accel = P_idle + ρ × (P_max - P_idle)
```
where ρ is accelerator utilization ratio.

Total energy:
```
E = (P_cpu + P_accel) × duration / 3,600,000  [kWh]
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOCATOR_APP_NAME` | Application name | "Smart Task Allocator" |
| `ALLOCATOR_API_PORT` | API server port | 8000 |
| `ALLOCATOR_LOG_LEVEL` | Logging level | "INFO" |
| `ALLOCATOR_LOG_FORMAT` | Log format (json/text) | "json" |
| `ALLOCATOR_MODEL_TYPE` | Model type identifier | "heuristic_energy_aware" |
| `ALLOCATOR_DEFAULT_TASK_DURATION` | Default task duration (s) | 3600.0 |

## Development

### Project Structure Best Practices

- **Modular design**: Separate concerns (models, services, config)
- **Type hints**: Full type annotation for better IDE support
- **Pydantic validation**: Automatic request/response validation
- **Logging**: Structured JSON logging for production
- **Configuration**: Environment-based settings

### Adding New Allocation Strategies

To add a new allocation strategy:

1. Create new method in `TaskAllocator` class:
   ```python
   def _ml_based_allocation(self, request: AllocationRequest):
       # Your ML logic here
       pass
   ```

2. Update `allocate_task()` to call your method

3. Update configuration to select strategy

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Change port in .env or use command line
uvicorn main:app --port 8001
```

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Connection refused from C++ simulator:**
- Check firewall settings
- Verify service is running: `curl http://localhost:8000/health`
- Check host/port configuration

## Future Enhancements

### Phase 2: Machine Learning Integration
- Collect historical allocation data
- Train supervised models for resource prediction
- Implement online learning for adaptation

### Phase 3: Reinforcement Learning
- Formulate as MDP (Markov Decision Process)
- Implement DQN or Actor-Critic agent
- Train with simulation data
- Deploy trained policy

### Phase 4: Advanced Features
- Multi-objective optimization (energy + latency + cost)
- Task migration and rescheduling
- Predictive scaling
- Federated learning across cells

## License

MIT License - See LICENSE file for details

## Contact

For questions or issues, please open a GitHub issue or contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Status**: Production Ready (Heuristic Model)
