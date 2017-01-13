#!/usr/bin/env python
# vim: set expandtab:
# with thanks to https://github.com/bpennypacker/ec2-check-reserved-instances.git 
# For the initial idea, and an idea of how to do this.


PROJECTNAME = 'ec2-check-reserved-instances'
import os
import sys
import ConfigParser
import logging

import boto
import boto.ec2
from pprint import pprint
from collections import defaultdict


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
        description='Instance-report reports on your ec2 reserved vs on demand instances')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debugging during execution.',
                        default=None)
    parser.add_argument('-p', '--profile', action='store', help='Which AWS profile to use.')
    parser.add_argument('-r', '--region', action='store', default='us-east-1',
                        help='Must be valid region in AWS_REGIONS list, if empty, defaults to us-east-1')
    parser.add_argument('-N', '--names', help="Include names or instance IDs of instances that fit non-reservations", required=False, action='store_true')
    parser.add_argument('-t', '--type', action='store', help='Specific instance type')
    parser.add_argument('-R', '--report', action='store_true',help='instance report', default=False)
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

    if _args.type:
        if _args.type not in INSTANCE_TYPES:
            sys.exit('invalid instance type %s:' % _args.type)
    return _args


def get_connection(args):
    if args.profile:
        if args.region:
            ec2_conn = boto.ec2.connect_to_region( args.region, profile_name=args.profile )
        else:
            ec2_conn = boto.connect_ec2( profile_name=args.profile )
    else:
        if args.region:
            ec2_conn = boto.ec2.connect_to_region( args.region )
        else:
            ec2_conn = boto.connect_ec2()
 
    return ec2_conn
    

def get_report(conn,args):
    reservations = conn.get_all_instances()
    running_instances = {}
    instance_ids = defaultdict(list)
    for reservation in reservations:
        for instance in reservation.instances:
            # ignore spot instances and non running instances.
            if instance.state != "running":
                log.info("Non-running instance %s: Ignoring\n" % ( instance.id ) )
            elif instance.spot_instance_request_id:
                log.info("Spot instance %s: Ignoring\n" % ( instance.id ) )
            else:
                az = instance.placement
                instance_type = instance.instance_type
                if args.type is None or args.type == instance_type:
                    running_instances[ (instance_type, az ) ] = running_instances.get( (instance_type, az ) , 0 ) + 1

                if "Name" in instance.tags and len(instance.tags['Name']) > 0:
                    instance_ids[ (instance_type, az ) ].append(instance.tags['Name'])
                else:
                    instance_ids[ (instance_type, az ) ].append(instance.id)

    reserved_instances = {}
    for reserved_instance in conn.get_all_reserved_instances():
        if reserved_instance.state != "active":
            log.info( "Inactive reserved instance %s: \n" % ( reserved_instance.id ) )
        else:
            az = reserved_instance.availability_zone
            instance_type = reserved_instance.instance_type
            if args.type is None or args.type == instance_type:
                reserved_instances[( instance_type, az) ] = reserved_instances.get ( (instance_type, az ), 0 )  + reserved_instance.instance_count

    """ value is neg for on demand, pos for unused reservations. """
    instance_diff = dict([(x, reserved_instances[x] - running_instances.get(x, 0 )) for x in reserved_instances])

    for key in running_instances:
        if not key in reserved_instances:
            instance_diff[key] = -running_instances[key]

    unused_reservations = dict((key,value) for key, value in instance_diff.iteritems() if value > 0)
    if unused_reservations == {}:
        if args.type:
            print ("Congratulations, you have no unused reservations of type %s:" % args.type) 
        else:
            print "Congratulations, you have no unused reservations"
    else:
        for unused_reservation in unused_reservations:
            print "UNUSED RESERVATION!\t(%s)\t%s\t%s" % ( unused_reservations[ unused_reservation ], unused_reservation[0], unused_reservation[1] )

    print ""

    unreserved_instances = dict((key,-value) for key, value in instance_diff.iteritems() if value < 0)
    if unreserved_instances == {}:
        if args.type:
            print ("Congratulations, you have no unreserved instances of type %s:" % args.type)
        else:
            print "Congratulations, you have no unreserved instances"
    else:
        ids=""
        for unreserved_instance in unreserved_instances:
            if args.names:
                ids = ', '.join(sorted(instance_ids[unreserved_instance]))
            print "Non-reserved:\t%s\t%s\t%s\t%s" % ( unreserved_instances[ unreserved_instance ], unreserved_instance[0], unreserved_instance[1], ids )

    if running_instances.values():
        qty_running_instances = reduce( lambda x, y: x+y, running_instances.values() )
    else:
        qty_running_instances = 0

    if reserved_instances.values():
        qty_reserved_instances = reduce( lambda x, y: x+y, reserved_instances.values() )
    else:
        qty_reserved_instances = 0

    print "\n(%s) running on-demand instances\n(%s) reservations" % ( qty_running_instances, qty_reserved_instances )


    if args.report:
        all_keys = {}
        for key in reserved_instances.keys():
            all_keys[key] = 0
        for key in running_instances.keys():
            all_keys[key] = 0
        for key in all_keys.keys():
            try: 
                running = running_instances[key]
            except KeyError:
                running = 0
            try: 
                reserved = reserved_instances[key]
            except KeyError:
                reserved = 0
            all_keys[key] = (running,reserved)

        print"type AZ running reserved over/under"
        for key in all_keys.keys():
            _type = key[0]
            AZ = key[1]
            running, reserved = all_keys[key]
            miss = reserved - running
            print ("%s %s %s %s %s" % (_type, AZ, running, reserved, miss ) )

# Here we start if called directly (the usual case.)
if __name__ == "__main__":
    # This is where we will begin when called from CLI. No need for argparse
    # unless being called interactively, so import it here
    args = get_args()
    # get the instance report
    conn = get_connection(args)
    sys.exit(get_report(conn,args))






