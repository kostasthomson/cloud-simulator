import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cloud_simulator.simulator import Simulator
from cloud_simulator.task import Task, TaskConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_sosm_initialization():
    logger.info("=" * 60)
    logger.info("Testing SOSM Integration - Initialization")
    logger.info("=" * 60)

    cell_data = Path("../cloudlightning-simulator/input/CellData.json")
    broker_data = Path("../cloudlightning-simulator/input/BrokerData_test.json")

    if not cell_data.exists():
        logger.error(f"Cell data file not found: {cell_data}")
        return False

    if not broker_data.exists():
        logger.error(f"Broker data file not found: {broker_data}")
        return False

    try:
        sim = Simulator(str(cell_data), str(broker_data))
        logger.info(f"✓ Simulator initialized successfully")
        logger.info(f"  - Number of cells: {len(sim.cells)}")
        logger.info(f"  - Broker type: {sim.sim_inputs.sosm_integration}")
        logger.info(f"  - Max simulation time: {sim.max_time}")

        cell = sim.cells[0]
        logger.info(f"✓ Cell 0 structure:")
        logger.info(f"  - Number of types: {cell.get_number_of_types()}")
        logger.info(f"  - Types: {cell.get_types()}")
        logger.info(f"  - Resources per type: {cell.get_number_of_resources_per_type()}")

        broker = cell.get_broker()
        logger.info(f"✓ SOSM Broker structure:")
        logger.info(f"  - Number of vRMs: {broker.number_of_vrms}")
        logger.info(f"  - Number of pSwitches: {broker.number_of_pswitches}")
        logger.info(f"  - Number of pRouters: {broker.number_of_prouters}")

        for i, type_vrms in enumerate(broker.vrms):
            logger.info(f"  - Type {i}: {len(type_vrms)} vRMs")

        return True

    except Exception as e:
        logger.error(f"✗ Initialization failed: {e}", exc_info=True)
        return False


def test_sosm_with_simple_task():
    logger.info("=" * 60)
    logger.info("Testing SOSM Integration - Simple Task Deployment")
    logger.info("=" * 60)

    cell_data = Path("../cloudlightning-simulator/input/CellData.json")
    broker_data = Path("../cloudlightning-simulator/input/BrokerData_test.json")

    if not cell_data.exists() or not broker_data.exists():
        logger.error("Config files not found")
        return False

    try:
        sim = Simulator(str(cell_data), str(broker_data))
        cell = sim.cells[0]
        broker = cell.get_broker()

        task_config = TaskConfig(
            processors_per_vm=2.0,
            memory_per_vm=4096.0,
            network_bandwidth=100.0,
            storage_per_vm=50.0,
            accelerators_per_vm=0,
            num_vms=1,
            total_instructions=1000000.0,
            processor_utilization=0.7,
            memory_utilization=0.8,
            storage_utilization=0.5,
            accelerator_utilization=0.0,
            available_implementations=cell.get_types()[:1],
            arrival_time=0.0,
        )

        task = Task(0, task_config)
        sim.add_task(task)

        logger.info(f"✓ Created test task: {task.id}")
        logger.info(f"  - VMs: {task.num_vms}")
        logger.info(f"  - CPUs per VM: {task.processors_per_vm}")
        logger.info(f"  - Memory per VM: {task.memory_per_vm}")
        logger.info(f"  - Available implementations: {task.available_implementations}")

        logger.info("Running simulation for 10 timesteps...")
        sim.max_time = 10.0
        results = sim.run()

        logger.info(f"✓ Simulation completed")
        logger.info(f"  - Resource allocation mechanism: {results['Resource allocation mechanism']}")
        logger.info(f"  - Total submitted tasks: {results['Total number of submitted tasks']}")

        for cl_output in results['CLSim outputs']:
            cell_id = cl_output['Cell']
            hw_type = cl_output['HW Type']
            outputs = cl_output['Outputs']

            if outputs:
                last_output = outputs[-1]
                logger.info(f"✓ Cell {cell_id}, HW Type {hw_type} statistics:")
                logger.info(f"  - Accepted tasks: {last_output['Total Number of accepted Tasks']}")
                logger.info(f"  - Rejected tasks: {last_output['Total Number of rejected Tasks']}")
                logger.info(f"  - Total timesteps collected: {len(outputs)}")

        return True

    except Exception as e:
        logger.error(f"✗ Task deployment test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("\n" + "=" * 60)
    logger.info("SOSM Integration Test Suite")
    logger.info("=" * 60 + "\n")

    tests = [
        ("Initialization", test_sosm_initialization),
        ("Simple Task Deployment", test_sosm_with_simple_task),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED\n")
            else:
                failed += 1
                logger.error(f"✗ {test_name} FAILED\n")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test_name} FAILED with exception: {e}\n", exc_info=True)

    logger.info("=" * 60)
    logger.info(f"Test Results: {passed} passed, {failed} failed")
    logger.info("=" * 60)

    sys.exit(0 if failed == 0 else 1)
