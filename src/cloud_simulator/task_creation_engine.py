"""
Task Creation Engine (TCE) for CloudLightning Simulator

Copyright 2017 The CloudLightning Simulation Framework Authors.
Translated from C++ to Python.
"""

from typing import List, Optional
import random
import math


def task_creation_engine(jobs: List, app):
    """
    Creates tasks based on application configuration.

    Args:
        jobs: List to append created tasks to
        app: AppInputs configuration object
    """
    random.seed(0)
    r = random.random()

    number_of_tasks = round(app.minmax_jobs_per_sec[0] + r * (app.minmax_jobs_per_sec[1] - app.minmax_jobs_per_sec[0]))

    for i in range(number_of_tasks):
        r = random.random()
        application_type = math.floor(app.num_of_apps * r)
        r = random.random()

        curr_requested_instructions = (
            app.minmax_ins_per_app[application_type][0] +
            r * (app.minmax_ins_per_app[application_type][1] - app.minmax_ins_per_app[application_type][0])
        )

        curr_number_of_vms = round(
            app.minmax_vm_per_app[application_type][0] +
            r * (app.minmax_vm_per_app[application_type][1] - app.minmax_vm_per_app[application_type][0])
        )

        curr_req_p = round(
            app.minmax_proc_per_vm[application_type][0] +
            r * (app.minmax_proc_per_vm[application_type][1] - app.minmax_proc_per_vm[application_type][0])
        )

        curr_req_m = (
            app.minmax_mem_per_vm[application_type][0] +
            r * (app.minmax_mem_per_vm[application_type][1] - app.minmax_mem_per_vm[application_type][0])
        )

        curr_req_n = (
            app.minmax_net_per_app[application_type][0] +
            r * (app.minmax_net_per_app[application_type][1] - app.minmax_net_per_app[application_type][0])
        )

        curr_req_s = (
            app.minmax_sto_per_vm[application_type][0] +
            r * (app.minmax_sto_per_vm[application_type][1] - app.minmax_sto_per_vm[application_type][0])
        )

        from .task import Task
        task = Task(
            application_type,
            app.number_of_available_implementations_per_app[application_type],
            app.available_implementations_per_app[application_type],
            curr_requested_instructions,
            curr_number_of_vms,
            curr_req_p,
            curr_req_m,
            curr_req_n,
            curr_req_s,
            app.type_of_act_p[application_type],
            app.type_of_act_m[application_type],
            app.type_of_act_n[application_type],
            app.minmax_act_p[application_type],
            app.minmax_act_m[application_type],
            app.minmax_act_n[application_type],
            app.accelerator[application_type],
            app.rho_acc[application_type]
        )
        jobs.append(task)


def task_impl_select(jobs: List):
    """
    Randomly selects an implementation for each task.

    Args:
        jobs: List of tasks to process
    """
    number_of_tasks = len(jobs)

    for i in range(number_of_tasks):
        r = random.random()
        task = jobs[i]
        implementation_type = math.floor(r * float(task.get_number_of_available_implementations()))

        l_number_of_available_implementations = 1
        l_type = task.get_type()
        l_available_implementations = [task.get_available_implementations()[implementation_type]]
        l_requested_instructions = task.get_requested_instructions()
        l_number_of_vms = task.get_number_of_vms()

        l_req_pmns = task.get_req_pmns()[:]
        l_typeact_pmn = task.get_typeact_pmn()[:]
        l_minmaxact_pmn = [row[:] for row in task.get_minmaxact_pmn()]

        l_av_acc = [task.get_av_acc()[implementation_type]]
        l_rho_acc = [task.get_rho_acc()[implementation_type]]

        from .task import Task
        jobs[i] = Task(
            l_type,
            l_number_of_available_implementations,
            l_available_implementations,
            l_requested_instructions,
            l_number_of_vms,
            l_req_pmns[0],
            l_req_pmns[1],
            l_req_pmns[2],
            l_req_pmns[3],
            l_typeact_pmn[0],
            l_typeact_pmn[1],
            l_typeact_pmn[2],
            l_minmaxact_pmn[0],
            l_minmaxact_pmn[1],
            l_minmaxact_pmn[2],
            l_av_acc,
            l_rho_acc
        )


def task_cell_select(jobs: List, gates, comm_cells: List[Optional[int]]) -> List[int]:
    """
    Selects the best cell for each task using the gateway service.

    Args:
        jobs: List of tasks
        gates: GatewayService object
        comm_cells: Output list for cell assignments

    Returns:
        List of cell indices for each task
    """
    comm_cells.clear()

    if len(jobs) != 0 and gates.get_alloc():
        comm_cells.extend([-1] * len(jobs))

        for i in range(len(jobs)):
            task = jobs[i]
            comm_cells[i] = gates.find_cell(
                task.get_available_implementations(),
                task.get_number_of_available_implementations(),
                task.get_number_of_vms(),
                task.get_req_pmns()[0],
                task.get_req_pmns()[1],
                task.get_req_pmns()[2],
                task.get_req_pmns()[3],
                task.get_av_acc()
            )

    return comm_cells
