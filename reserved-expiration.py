#!/usr/bin/env python
# vim: set expandtab:
# with thanks to https://github.com/bpennypacker/ec2-check-reserved-instances.git 
# For the initial idea, and an idea of how to do this.


PROJECTNAME = 'reserved-instance-expiration'
import os
import sys
import ConfigParser
import logging

import subprocess
import json
from pprint import pprint
from collections import defaultdict
import datetime


# Setup logging
logging.basicConfig(level=logging.WARN,
                    format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='%y.%m.%d %H:%M:%S')

# Setup logging to console.
console = logging.StreamHandler(sys.stderr)
console.setLevel(logging.WARN)
logging.getLogger(PROJECTNAME).addHandler(console)
log = logging.getLogger(PROJECTNAME)


AWS_REGIONS = [ 'us-east-1',
		'us-east-2',
		'us-west-1',
		'us-west-2' ]


INSTANCE_TYPES = [ 'c3.large',
                    'c4.xlarge',
                    'm1.small',
                    'm3.large',
                    'm3.medium',
                    'm3.xlarge',
                    'm4.4xlarge',
                    'm4.large',
                    'r3.2xlarge',
                    'r3.large',
                    'r3.xlarge',
                    't2.medium',
                    't2.nano',
                    't2.small', ]

def get_options():
    """ Parse the command line options"""
    import argparse

    parser = argparse.ArgumentParser(
        description='check for expiring reserved instances')
    parser.add_argument('-D', '--debug', action='store_true', \
                        help='Enable debugging during execution.', \
                        default=None)
    parser.add_argument('-p', '--profile', action='store', default='default', \
			help='Which AWS profile to use, defaults to default')
    parser.add_argument('-d', '--days', help="Report instances that expire in D days", required=False, action='store', default = 30)
    parser.add_argument('-t', '--text', action='store_true', help='Output in text fmt, not json')
    _args = parser.parse_args()
    _args.usage = PROJECTNAME + ".py [options]"

    return _args


def get_args():
    """ we only run if called from main """
    _args = get_options()

    if _args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARN)

    return _args



def get_data():
    # replace this with a shell out to get the info,
    # command example aws --profile prod ec2 describe-reserved-instances   --filter Name=state,Values=active
    # build command 
    profile = args.profile
    commandquery = ["aws", "--profile", profile,"ec2", "describe-reserved-instances", "--filter", "Name=state,Values=active"]
    result = subprocess.Popen(commandquery, stdout=subprocess.PIPE)
    reservations_data,RC = result.communicate([0])
    reservations = json.loads(reservations_data)
    return reservations


def get_expires(reservations):
    expiry_list = {}
    today = datetime.datetime.today()
    now = (today - datetime.datetime(1970, 1, 1)).total_seconds()
    for reservation in reservations['ReservedInstances']:
        exp_date = reservation['End']
        utc_date = datetime.datetime.strptime(exp_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        exp_seconds = (utc_date - datetime.datetime(1970, 1, 1)).total_seconds()
        res_id=reservation['ReservedInstancesId']
        if now + seconds_to_exp > exp_seconds:
            expiry_list[res_id] = exp_date
    return expiry_list


def return_values(reservations):
    # get a dict of any expirations happeing within 'days' and return some
    # coherent value for RC and data, some kind of monitor will consume this.
    expires = get_expires(reservations)
    if expires.keys() == []:
        sys.exit(0)
    else: return expires

def output_results(expires):
    # Output reserved instances that are expiring soon 
    if args.text:
        # output in text format
        for key in expires.keys():
            print key, expires[key]
    else:
        print expires

    # Here we start if called directly (the usual case.)
if __name__ == "__main__":
    # This is where we will begin when called from CLI. No need for argparse
    # unless being called interactively, so import it here
    args = get_args()
    seconds_to_exp = int(args.days) * 86400
    # get the instance report
    reservations = get_data()
    output_results(return_values(reservations))

