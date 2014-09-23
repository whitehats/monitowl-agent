# -*- encoding: utf-8 -*-
'''
Custom log handlers.
'''
from __future__ import absolute_import
import datetime
import gzip
import logging
import logging.handlers
import os
import re
import time


class LogFileHandler(logging.handlers.TimedRotatingFileHandler):
    '''
    Log handler, puts all logs into a file, rotates files (saves current
    log file and opens new one) daily (by default),
    compresses old ones and deletes oldest to preserve given space limit.
    Also, puts all errors to agent's error channel.queue, config_id,
    '''
    # R0902: Too many instance attributes
    # pylint: disable=R0902
    def __init__(self, filename, when='MIDNIGHT',
                 interval=1, backup_count=14, encoding=None,
                 delay=False, utc=False, max_disk_space=10485760):
        '''
        Returns new instance of LogFileHandler.
        :param filename: specified file is opened and used as the stream for logging.
            On rotating it also sets the filename suffix
        :param when: type of interval: 'S' - seconds, 'M' - minutes, 'H' - hours
            'D' - Days, 'W0'-'W6' - weekday (0=Monday), 'MIDNIGHT' - roll over at midnight
        :param interval: rotating happens based on the product of when and
            interval, if `when` is 'MIDNIGHT' or 'W0'-'W6' interval is ignored
        :param encoding: file encoding
        :param delay: if true, file opening is deferred until the first log occurs.
        :param utc: if true, utc time is used rather then localtime
        :param max_disk_space: given disk space limit for storing log files, in bytes
        '''
        # R0913: Too many arguments
        # pylint: disable=R0913
        super(LogFileHandler, self).__init__(
            filename, when, interval, backup_count, encoding, delay, utc
        )
        self.delay = delay
        # We divide space limit in two, so one half goes for all compressed
        # files, and second one for current log file (uncompressed).
        self.max_disk_space = max_disk_space / 2
        self.start_time = int(time.time())
        # Log file suffix, whith second precision, as even if `when`='MIDNIGHT',
        # due to space restrictions, rotating may occur midday.
        self.log_suffix = "%Y-%m-%d_%H-%M-%S"
        self.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.gz$")

    def shouldRollover(self, record):
        '''
        Determine if rollover should occur - should log files be rotated.
        '''
        if int(time.time()) >= self.rolloverAt:
            return 1
        # Check if current logfile exceeds self.max_disk_space.
        if self.stream is None:
            # Delay was set to True.
            self.stream = self._open()
        msg = '{}\n'.format(self.format(record))
        # Due to non-posix-compliant Windows feature.
        self.stream.seek(0, 2)
        if self.stream.tell() + len(msg) >= self.max_disk_space:
            return 1
        return 0

    def getFilesToDelete(self):
        '''
        Determine the log files to delete when rolling over.
        '''
        # E1103: Maybe no member - `extMatch` might not have `match` member
        # pylint: disable=E1103
        dir_name, base_name = os.path.split(self.baseFilename)
        file_names = os.listdir(dir_name)
        prefix = base_name + '.'
        log_files = [
            os.path.join(dir_name, file_name) for file_name in file_names
            if file_name.startswith(prefix)
            and self.extMatch.match(file_name.strip(prefix))
        ]
        log_files.sort(reverse=True)
        used_space = 0
        i = 0
        for log_file in log_files:
            used_space += os.path.getsize(log_file)
            if used_space > self.max_disk_space:
                break
            i += 1
        return log_files[min(i, self.backupCount):]

    def doRollover(self):
        '''
        Does a rollover - rotates log files.

        Close current log file, compress it,
        check used max_disk_space and delete oldest files to fit in disk space limit,
        open new filestream.
        '''
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.utc:
            time_tuple = time.gmtime(self.start_time)
        else:
            time_tuple = time.localtime(self.start_time)
        dfn = '{}.{}.gz'.format(
            self.baseFilename,
            time.strftime(self.log_suffix, time_tuple)
        )
        if os.path.exists(dfn):
            os.remove(dfn)
        if os.path.exists(self.baseFilename):
            f_in = open(self.baseFilename, 'rb')
            f_out = gzip.open(dfn, 'wb')
            f_out.writelines(f_in)
            f_out.close()
            f_in.close()
        for old_file in self.getFilesToDelete():
            os.remove(old_file)
        if not self.delay:
            os.remove(self.baseFilename)
            self.stream = self._open()
        self.start_time = int(time.time())
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:
                    # DST kicks in before next rollover, so deduct an hour.
                    addend = -3600
                else:
                    # DST bows out before next rollover, so add an hour.
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at


class AgentErrorLogHandler(logging.Handler):
    '''
    Agent custom handler for putting error and critical logs
    into agent's error channel.
    '''
    def __init__(self, queue, config_id):
        super(AgentErrorLogHandler, self).__init__(logging.ERROR)
        self.queue = queue
        self.config_id = config_id

    def emit(self, record):
        msg = {
            'config_id': self.config_id,
            'data': record.getMessage(),
            'datatype': str,
            'timestamp': datetime.datetime.utcnow(),
            'stream_name': '_error'
        }
        self.queue.put(msg)
