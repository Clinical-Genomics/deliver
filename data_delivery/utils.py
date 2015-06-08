# -*- coding: utf-8 -*-
import logging
import subprocess

logger = logging.getLogger(__name__)


def extract_flowcell(run_dir):
    """Extract flowcell id from run dir path.

    Args:
        run_dir (path): path to run folder

    Returns:
        str: flowcell id
    """
    run_folder = run_dir.realpath().basename()
    folder_parts = run_folder.split('_')
    flowcell_part = folder_parts[-1]
    flowcell_id = flowcell_part[1:]

    return flowcell_id


def submit_sbatch(command):
    """Submit command to sbatch."""
    command_args = ['sbatch'] + command
    return subprocess.call(command_args, shell=True)
