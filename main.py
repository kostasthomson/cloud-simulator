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
        '--config',
        type=str,
        default='config/example_config.json',
        help='Path to configuration JSON file'
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

    logger.info("=" * 80)
    logger.info("Cloud Simulator - Traditional Provisioning Schema")
    logger.info("=" * 80)

    try:
        simulator = Simulator(args.config)
        results = simulator.run()
        simulator.save_results(args.output)

        logger.info("=" * 80)
        logger.info("Simulation Summary:")
        logger.info(f"  End Time: {results['simulation_config']['actual_end_time']}")

        for res_type, stats in results['cell_state']['statistics'].items():
            logger.info(f"\nResource Type {res_type}:")
            logger.info(f"  Accepted Tasks: {stats['accepted_tasks']}")
            logger.info(f"  Rejected Tasks: {stats['rejected_tasks']}")
            logger.info(f"  Acceptance Rate: {stats['acceptance_rate']:.2%}")
            logger.info(f"  Total Power Consumption: {stats['total_power_consumption']:.2f} W")
            if stats['accepted_tasks'] > 0:
                logger.info(f"  Avg Waiting Time: {stats['avg_waiting_time']:.2f} time units")
                logger.info(f"  Avg Response Time: {stats['avg_response_time']:.2f} time units")

        logger.info("=" * 80)
        logger.info(f"Results saved to: {args.output}")

    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
