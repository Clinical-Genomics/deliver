# -*- coding: utf-8 -*-
"""
Deliver FASTQ files to be run with the microbial pipeline.

=> INPUT: flowcell

=> CONFIG: root_dir, clinstatsdb_connection
=> INFO:
     - FASTQ: flowcell, lims_id
     - LINK: project_id, sample_name, fastq_files
"""
import logging
import re

from cglims.api import ClinicalLims
from clinstatsdb.db import api
from clinstatsdb.db.models import Demux, Flowcell, Sample, Unaligned
from path import path

log = logging.getLogger(__name__)


def link_microbial(config, flowcell=None, project=None, sample=None,
                   dry_run=False):
    """Link FASTQ files for microbial samples."""
    lims_api = ClinicalLims(**config['lims'])
    manager = api.connect(config['clinstatsdb_uri'])

    if sample:
        lims_ids = [sample]
    elif project:
        lims_ids = project_samples(lims_api, project)
    elif flowcell:
        lims_ids = flowcell_samples(manager, flowcell)
    else:
        raise ValueError("must supply flowcell, project or sample!")

    lims_samples = (lims_api.sample(lims_id) for lims_id in lims_ids)
    relevant_samples = (sample for sample in lims_samples
                        if (sample.udf.get('Sequencing Analysis', '')
                                      .startswith('MW')))
    for lims_sample in relevant_samples:
        log.info("working on sample: %s", lims_sample.id)
        demux_root = config['demux_root']
        microbial_root = config['microbial_root']
        lims_data = get_limsinfo(lims_sample)
        project_id = lims_data['project_id']
        sample_root = path(microbial_root).joinpath(project_id, lims_sample.id)
        if not dry_run:
            if sample_root.exists():
                log.info("removing dir: %s", sample_root)
                sample_root.rmtree()
            # Make sure that project/sample dir exists
            sample_root.makedirs_p()

        files = from_sample(manager, demux_root, sample_root, project_id,
                            lims_sample.id)
        for fastq, new_loc in files:
            log.info("linking file: %s -> %s", fastq, new_loc)
            if not dry_run:
                path(fastq).symlink(new_loc)


def flowcell_samples(csdb_manager, flowcell_id):
    """Return sample data from a flowcell output."""
    flowcell = Flowcell.query.filter_by(flowcellname=flowcell_id).one()
    lims_ids = get_samples(flowcell)
    return lims_ids


def project_samples(lims_api, project_id):
    """Get all samples for a project."""
    lims_samples = lims_api.get_samples(projectname=project_id)
    assert len(lims_samples) > 0, "bad project id: {}".format(project_id)
    for lims_sample in lims_samples:
        yield lims_sample.id


def get_samples(flowcell):
    """Return LIMS ids for all microbial samples on a flowcell."""
    for demux in flowcell.demuxes:
        for unaligned in demux.unaligned:
            sample_name = unaligned.sample.samplename
            lims_id = sample_name.rsplit('_', 1)[0]
            yield lims_id


def from_sample(csdb_manager, demux_root, sample_root, project_id, lims_id):
    """Perform linking for a sample."""
    flowcells = get_flowcells(csdb_manager, lims_id)
    for flowcell in flowcells:
        flowcell_id = flowcell.flowcellname
        log.debug("working on flowcell: %s", flowcell_id)
        fastqs = get_fastqs(demux_root, flowcell_id, project_id, lims_id)
        for fastq_file in fastqs:
            new_name = rename_fastq(fastq_file, flowcell_id, lims_id)
            new_loc = path(sample_root).joinpath(new_name)
            yield fastq_file, new_loc


def get_flowcells(csdb_manager, lims_id):
    """Get demux info about a sample."""
    query = (Flowcell.query
                     .join(Flowcell.demuxes)
                     .join(Demux.unaligned)
                     .join(Unaligned.sample)
                     .filter(Sample.samplename.like("{}%".format(lims_id))))
    return query


def get_fastqs(demux_root, flowcell_id, project_id, lims_id):
    """Get FASTQ files for a sample."""
    demux_path = path(demux_root)
    fastqs = demux_path.glob("*{}/Unaligned*/Project_{}/Sample_{}_*/*.fastq.gz"
                             .format(flowcell_id, project_id, lims_id))
    return fastqs


def rename_fastq(fastq_file, flowcell_id, lims_id):
    """Make up a new clean name for a fastq_file."""
    file_name = fastq_file.basename()
    lane = re.search("_L\d{3}_", file_name).group()[-2]
    read_direction = re.search("_R\d_", file_name).group()[-2]
    new_name = ("{}_{}_L{}_R{}.fastq.gz"
                .format(lims_id, flowcell_id, lane, read_direction))
    return new_name


def get_limsinfo(lims_sample):
    """Get information from LIMS."""
    # check that application tag is indicating microbial sample
    app_tag = lims_sample.udf['Sequencing Analysis']
    project_id = lims_sample.project.name
    customer = lims_sample.udf['customer']
    return {'customer': customer, 'project_id': project_id, 'app_tag': app_tag}
