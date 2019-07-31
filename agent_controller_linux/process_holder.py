import os
import time

import fcntl

import logger

LOG = logger.get_logger('Tracker')


class ProcessHolder(object):

    def __init__(self):
        print 'init Tracker'
        self.buffer = ''
        self.datalines = []
        self.last_datapoint = int(time.time())

    def read(self, process):
        try:
            errbytes = process.stderr.read()
            if errbytes is not None:
                out = errbytes.decode(encoding='ascii')
                if out:
                    LOG.debug('got %d bytes on stderr',
                              len(out))
                    for line in out.splitlines():
                        if len(line.strip()):
                            LOG.warning('%s', line)
        except IOError as e:
            pass
        except Exception as e:
            LOG.exception('uncaught exception in stderr read: %s', e.args)

        try:
            readbytes = process.stdout.read()
            if readbytes is not None:
                out = readbytes.decode(encoding='ascii')
                # if out:
                #     LOG.debug('read %d bytes on stdout',
                #               len(out))
                self.buffer += out
                # if len(self.buffer):
                #     LOG.debug('buffer now %d bytes', len(self.buffer))
        except IOError as e:
            pass
        except AttributeError:
            # sometimes the process goes away in another thread and we don't
            # have it anymore, so log an error and bail
            LOG.exception('caught exception, collector process went away while reading stdout')
        except Exception as e:
            LOG.exception('uncaught exception in stdout read: %s', e.args)
            return

        while self.buffer:
            idx = self.buffer.find('\n')
            if idx == -1:
                break

            line = self.buffer[0:idx].strip()
            if line:
                # LOG.debug(line)
                self.datalines.append(line)
                self.last_datapoint = int(time.time())
            self.buffer = self.buffer[idx + 1:]

    def collect(self, process):
        while process is not None:
            self.read(process)
            if not len(self.datalines):
                return
            while len(self.datalines):
                yield self.datalines.pop(0)

    @staticmethod
    def set_nonblocking(fd):
        """"Sets the given file descriptor to non-blocking mode."""
        fl = fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, fl)
