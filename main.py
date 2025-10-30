#!/usr/bin/env python3
"""
Cloud Simulator - Main Entry Point

Runs the cloud infrastructure simulator with traditional provisioning.
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cloud_simulator import Simulator


def setup_logging(log_level: str) -> None:
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    parser = argparse.ArgumentParser(
        description='Cloud Simulator with Traditional Provisioning Schema'
    )
    parser.add_argument(
        '--cell-data',
        type=str,
        default='input/CellData.json',
        help='Path to cell data JSON file'
    )
    parser.add_argument(
        '--broker-data',
        type=str,
        default='input/BrokerData.json',
        help='Path to broker data JSON file'
    )
    parser.add_argument(
        '--task-data',
        type=str,
        default='input/TaskData.json',
        help='Path to task data JSON file (optional)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output/simulation_results.json',
        help='Path to output results JSON file'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level'
    )

    args = parser.parse_args()

    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        simulator = Simulator(args.cell_data, args.broker_data, args.task_data)
        logger.info("=" * 80)
        logger.info(f"Cloud Simulator - {simulator.get_broker()} Provisioning Schema")
        logger.info("=" * 80)
        results = simulator.run()
        simulator.save_results(args.output, results)

        logger.info("=" * 80)
        logger.info("Simulation Summary:")
        logger.info(f"  Resource allocation mechanism: {results['Resource allocation mechanism']}")
        logger.info(f"  Total number of submitted tasks: {results['Total number of submitted tasks']}")

        for cl_output in results['CLSim outputs']:
            cell_id = cl_output['Cell']
            hw_type = cl_output['HW Type']
            outputs = cl_output['Outputs']

            if outputs:
                last_output = outputs[-1]
                logger.info(f"\nCell {cell_id}, HW Type {hw_type}:")
                logger.info(f"  Active Servers: {last_output['Active Servers']}")
                logger.info(f"  Running VMs: {last_output['Running VMs']}")
                logger.info(f"  Accepted Tasks: {last_output['Total Number of accepted Tasks']}")
                logger.info(f"  Rejected Tasks: {last_output['Total Number of rejected Tasks']}")
                logger.info(f"  Total Energy Consumption: {last_output['Total Energy Consumption']:.6e} GWh")
                logger.info(f"  Total Timesteps: {len(outputs)}")

        logger.info("=" * 80)
        logger.info(f"Results saved to: {args.output}")

    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
