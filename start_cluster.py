#!/usr/bin/env python

import os
import time
import json
import argparse
import subprocess

parser = argparse.ArgumentParser()

# required arguments
parser.add_argument('--name', '-n', required=True, type=str, help='Name of cluster.')

# arguments with default parameters
parser.add_argument('--image-version', default='1.1', type=str, help='Google dataproc image version.')
parser.add_argument('--master-machine-type', '--master', '-m', default='n1-highmem-8', type=str, help='Master machine type.')
parser.add_argument('--master-boot-disk-size', default='100GB', type=str, help='Disk size of master machine.')
parser.add_argument('--num-master-local-ssds', default='0', type=str, help='Number of local SSDs to attach to the master machine.')
parser.add_argument('--num-preemptible-workers', '--n-pre-workers', '-np', default='0', type=str, help='Number of preemptible worker machines.')
parser.add_argument('--num-worker-local-ssds', default='0', type=str, help='Number of local SSDs to attach to each worker machine.')
parser.add_argument('--num-workers', '--n-workers', '-nw', default='2', type=str, help='Number of worker machines.')
parser.add_argument('--preemptible-worker-boot-disk-size', default='40GB', type=str, help='Disk size of preemptible machines.')
parser.add_argument('--worker-boot-disk-size', default='40GB', type=str, help='Disk size of worker machines.')
parser.add_argument('--worker-machine-type', '--worker', '-w', default='n1-standard-8', type=str, help='Worker machine type.')
parser.add_argument('--zone', default='us-central1-b', type=str, help='Compute zone for the cluster.')
parser.add_argument('--properties', default='', type=str, help='Additional configuration properties for the cluster.')

# initialization action flags
parser.add_argument('--vep', action='store_true')

# parse arguments
args = parser.parse_args()

# master machine type to memory map, to set spark.driver.memory property
machine_mem = {
    'n1-standard-1': 3.75,
    'n1-standard-2': 7.5,
    'n1-standard-4': 15,
    'n1-standard-8': 30,
    'n1-standard-16': 60,
    'n1-standard-32': 120,
    'n1-standard-64': 240,
    'n1-highmem-2': 13,
    'n1-highmem-4': 26,
    'n1-highmem-8': 52,
    'n1-highmem-16': 104,
    'n1-highmem-32': 208,
    'n1-highmem-64': 416,
    'n1-highcpu-2': 1.8,
    'n1-highcpu-4': 3.6,
    'n1-highcpu-8': 7.2,
    'n1-highcpu-16': 14.4,
    'n1-highcpu-32': 28.8,
    'n1-highcpu-64': 57.6
}

# parse Spark and HDFS configuration parameters, combine into properties argument
properties = ','.join([
    'spark:spark.driver.memory={}g'.format(str(int(machine_mem[args.master_machine_type] * 0.8))),
    'spark:spark.driver.maxResultSize=0',
    'spark:spark.task.maxFailures=20',
    'spark:spark.kryoserializer.buffer.max=1g',
    'spark:spark.driver.extraJavaOptions=-Xss4M',
    'spark:spark.executor.extraJavaOptions=-Xss4M',
    'hdfs:dfs.replication=1'
])

# default initialization script to start up cluster with
init_actions = 'gs://labbott/init_notebook2.py'
#init_actions = 'gs://hail-common/init_notebook.py'

# add VEP action
if args.vep:
    init_actions = init_actions + ',' + 'gs://hail-common/vep/vep/vep85-init.sh'
    
# command to start cluster
cmd = ' '.join([
    'gcloud dataproc clusters create',
    args.name,
    '--image-version={}'.format(args.image_version),
    '--master-machine-type={}'.format(args.master_machine_type),
    '--master-boot-disk-size={}'.format(args.master_boot_disk_size),
    '--num-master-local-ssds={}'.format(args.num_master_local_ssds),
    '--num-preemptible-workers={}'.format(args.num_preemptible_workers),
    '--num-worker-local-ssds={}'.format(args.num_worker_local_ssds),
    '--num-workers={}'.format(args.num_workers),
    '--preemptible-worker-boot-disk-size={}'.format(args.preemptible_worker_boot_disk_size),
    '--worker-boot-disk-size={}'.format(args.worker_boot_disk_size),
    '--worker-machine-type={}'.format(args.worker_machine_type),
    '--zone={}'.format(args.zone),
    '--properties={}'.format(properties),
    '--initialization-actions={}'.format(init_actions)
])

# spin up cluster
try:
    subprocess.check_output(cmd, shell=True)

# exit if cluster already exists
except subprocess.CalledProcessError:
    pass

