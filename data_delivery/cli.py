# -*- coding: utf-8 -*-
import logging

import click
from path import path

import data_delivery.wrapper

logger = logging.getLogger(__name__)


def setup_logging(level='INFO'):
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # customize formatter, align each column
    template = "[%(asctime)s] %(name)-25s %(levelname)-8s %(message)s"
    formatter = logging.Formatter(template)

    # add a basic STDERR handler to the logger
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)

    root_logger.addHandler(console)
    return root_logger


@click.group()
def deliver():
    """Data delivery functions."""
    setup_logging()


@deliver.command()
@click.argument('run_dir', type=click.Path(exists=True))
def run(run_dir):
    """Deliver a single run directory."""
    logger.info("processing: %s", run_dir)
    data_delivery.wrapper.process_run(path(run_dir))


@deliver.command('all-runs')
@click.argument('demux_base', type=click.Path(exists=True))
def all_runs(demux_base):
    """Crawl and deliver all run directories."""
    data_delivery.wrapper.crawl_runs(demux_base)
