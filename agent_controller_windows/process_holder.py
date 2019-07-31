import msvcrt
import time
from ctypes import byref, windll, wintypes, WinError

import chardet

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
                charinfo = chardet.detect(errbytes)
                if charinfo and charinfo['encoding']:
                    out = errbytes.decode(encoding=charinfo['encoding'])
                else:
                    out = errbytes.decode(encoding='ascii')
                # out = errbytes.decode(encoding='ascii')
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
                charinfo = chardet.detect(readbytes)
                if charinfo and charinfo['encoding']:
                    out = readbytes.decode(encoding=charinfo['encoding'])
                else:
                    out = readbytes.decode(encoding='ascii')
                # out = readbytes.decode(encoding='ascii')
                self.buffer += out
        except IOError as e:
            pass
        except AttributeError:
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
    def set_nonblocking(pipefd):
        PIPE_NOWAIT = wintypes.DWORD(0x00000001)

        h = msvcrt.get_osfhandle(pipefd)

        res = windll.kernel32.SetNamedPipeHandleState(h, byref(PIPE_NOWAIT), None, None)
        if res == 0:
            print(WinError())
            return False
        return True
