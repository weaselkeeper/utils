AWS utils
--------

Some utility scripts for AWS 

#instance-report.py
Generates a report on the instances running under an AWS account, including
how many of what types, and if there are reserved instances being used or
underused 

'''./instance-report.py -h will provide brief instructions.'''

The script uses your aws credentials, and can distinguish between profiles with
the -p flag. 

Used with no options, will check the default account, and generate a full
instance rreport including region, type and number. 

