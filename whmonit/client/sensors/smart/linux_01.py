#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
S.M.A.R.T. sensor for monitoring hard disks
'''

import re
from subprocess import check_output, CalledProcessError

from whmonit.client.sensors import TaskSensorBase


class Sensor(TaskSensorBase):
    '''
    S.M.A.R.T. sensor class
    '''

    name = 'smart'

    # float values:
    # raw_value:   Vendor-specific raw value of the attribute (eg. time in hours or minutes)
    # value:       The value normalized according to disk's firmware. It's in range from
    #              1 to 255. If it's less than 'threshold', the attribute has failed
    # worst:       the lowest normalized value recorded since SMART was enabled
    # bool values (from manual):
    # disk_failing:      SMART status check returned "DISK FAILING:
    # below_thresh:      some attributes are below threshold (that is are failing)
    # below_thresh_past: status check returned "DISK OK" but some attributes
    #                    were below threshold in the past (that is were failing but aren't now)
    # err_log:           there are errors in error log
    # selftest_err_log:  self-test log contains errors
    #                    (new results from self-test override previous)
    streams = {
        'value': float,
        'worst': float,
        'threshold': float,
        'raw_value': float,
        'disk_failing': bool,
        'below_thresh': bool,
        'below_thresh_past': bool,
        'err_log': bool,
        'selftest_err_log': bool
    }

    config_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'id': {
                'type': 'string',
                'description': 'the Id of attribute to be read from S.M.A.R.T'
            },
            'disk_name': {
                'type': 'string',
                'description': 'eg. /dev/sda'
            },
            'disk_type': {
                'type': 'string',
                'description': 'eg. ata, scsi (all options in smartctl manual)'
            }
        },
        'required': ['id', 'disk_name'],
        'additionalProperties': False
    }

    # a regex to find the beginning of table with values sensor looks for
    beg_attr = re.compile(
        'ID#\\s*'
        'ATTRIBUTE_NAME\\s*'
        'FLAG\\s*'
        'VALUE\\s*'
        'WORST\\s*'
        'THRESH\\s*'
        'TYPE\\s*'
        'UPDATED\\s*'
        'WHEN_FAILED\\s*'
        'RAW_VALUE'
    )

    def do_run(self):
        #get output and returncode from smartctl command
        output = ''
        returncode = 0
        try:
            if 'disk_type' in self.config:
                output = check_output([
                    'smartctl',
                    '-s',
                    'on',
                    '-d',
                    self.config['disk_type'],
                    '-AH',
                    self.config['disk_name']
                ])
            else:
                output = check_output(['smartctl', '-s', 'on', '-AH', self.config['disk_name']])
        except CalledProcessError as cpe:
            if cpe.returncode & (1 << 0):
                self.log(
                    'command \"{}\" did not parse\n'
                    'maybe some of the parameters are wrong?'.format(' '.join(cpe.cmd))
                )
                return
            if cpe.returncode & (1 << 1):
                self.log('failed to open device {}'.format(self.config['disk_name']))
                return
            if cpe.returncode & (1 << 2):
                self.log(
                    'some SMART or other ATA command to the disk failed'
                    'or there was a checksum error in a SMART data structure\n'
                    'the command that caused error: \"{}\"'.format(' '.join(cpe.cmd))
                )
                return
            returncode = cpe.returncode
            output = cpe.output
        except OSError as ose:
            parameters = ' disk_name \"{}\"'.format(self.config['disk_name'])
            if 'disk_type' in self.config:
                parameters += ' disk_type \"{}\"'.format(self.config['disk_type'])
            self.log(
                'error evaluating command smartctl with parameters: {}'
                '\n\n possible reason is that program smartctl is not installed '
                '(try checking smartmontools pckage)'
                '\n\nreason from shell: \n{}\n'.format(parameters, ose)
            )
            return

        #get attributes from output
        # start_attr - index in output where table starts
        # regex (groups in brackets):
        # (id attribute_name flag)(value)(\s)(worst)(\s)(thresh)(\s)(type updated when_fail \s)(raw)
        # this is example row from the output with groups
        #(  9 Power_On_Hours          0x0012   )(098)(   )(098)
        #(   )(000)(    )(Old_age   Always       -       )(969)
        start_attr = self.__class__.beg_attr.search(output).end()
        attributes = re.compile(
            '(\\s*{}\\s+[A-Za-z_]+\\s+\\S+\\s+)'
            '([0-9]{{3}})(\\s+)'
            '([0-9]{{3}})(\\s+)'
            '([0-9]{{3}})(\\s+)'
            '(\\S+\\s+\\S+\\s+\\S+\\s+)(\d+)'.format(self.config['id'])
        ).search(output, start_attr)

        if attributes is None:
            self.log('requested id {} not found in output of smartctl'.format(self.config['id']))
            return

        return (
            ('value', float(attributes.group(2))),
            ('worst', float(attributes.group(4))),
            ('threshold', float(attributes.group(6))),
            ('raw_value', float(attributes.group(9))),
            ('disk_failing', bool(returncode & (1 << 3))),
            ('below_thresh', bool(returncode & (1 << 4))),
            ('below_thresh_past', bool(returncode & (1 << 5))),
            ('err_log', bool(returncode & (1 << 6))),
            ('selftest_err_log', bool(returncode & (1 << 7)))
        )
