# utils
Just some utility scripts I find useful
=======
AWS utils
--------

Some utility scripts for AWS 

#instance-report.py
Generates a report on the instances running under an AWS account, including
how many of what types, and if there are reserved instances being used or
underused 

```
usage: instance-report.py [-h] [-d] [-p PROFILE] [-r REGION] [-N] [-t TYPE]
                          [-R]

Instance-report reports on your ec2 reserved vs on demand instances
optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Enable debugging during execution.
  -p PROFILE, --profile PROFILE
                        Which AWS profile to use.
  -r REGION, --region REGION
                        Must be valid region in AWS_REGIONS list, if empty,
                        defaults to us-east-1
  -N, --names           Include names or instance IDs of instances that fit
                        non-reservations
  -t TYPE, --type TYPE  Specific instance type
  -R, --report          instance report
```
The script uses your aws credentials, and can distinguish between profiles with
the -p flag. 

Used with no options, will check the default account, and generate a full
instance report including region, type and number. 

#reserved-expiration.py

Generate a report on soon to expire instance reservations.

```
usage: reserved-expiration.py [-h] [-D] [-p PROFILE] [-d DAYS] [-t]

check for expiring reserved instances

optional arguments:
  -h, --help            show this help message and exit
  -D, --debug           Enable debugging during execution.
  -p PROFILE, --profile PROFILE
                        Which AWS profile to use, defaults to default
  -d DAYS, --days DAYS  Report instances that expire in D days
  -t, --text            Output in text fmt, not json

```

The script uses your aws credentials, and can distinguish between profiles with
the -p flag. 

Used with no options, will check the default account, and generate a report of 
what instance reservations are expiring within 30 days.


