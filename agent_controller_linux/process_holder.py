import os
import signal
import threading
import time

import fcntl

import logger

LOG = logger.get_logger('Tracker')


class ProcessHolder(object):

    def __init__(self, recycle_queue):
        print 'init Tracker'
        self.buffer = ''
        self.datalines = []
        self.last_datapoint = int(time.time())
        self.recycle_queue = recycle_queue

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

    def kill_process(self, process, process_name=None):
        if process is None:
            return
        if process_name:
            os.popen('killall -g %s' % process_name)
        else:
            os.killpg(process.pid, signal.SIGTERM)
        self.recycle_queue.put(process)

    def wait_process(self, process):
        if process:
            self.recycle_queue.put(process)

    @staticmethod
    def set_nonblocking(fd):
        """"Sets the given file descriptor to non-blocking mode."""
        fl = fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, fl)


class ProcessRecycle(threading.Thread):

    def __init__(self, queue):
        super(ProcessRecycle, self).__init__()
        self.queue = queue

    def run(self):
        while True:
            try:
                if self.queue.empty():
                    time.sleep(1)
                else:
                    process = self.queue.get()

                    if process is None or process.poll() is not None:
                        LOG.debug("----------- process recycled")
                        continue

                    LOG.debug("----------- process recycle 000")
                    time.sleep(10)
                    if process.poll() is None:
                        LOG.debug("----------- process recycle 111")
                        os.killpg(process.pid, signal.SIGKILL)
                        self.queue.put(process)
                    else:
                        LOG.debug("----------- process recycle 222")

            except Exception as e:
                LOG.exception('shutting down process failed, err: %s', e)
