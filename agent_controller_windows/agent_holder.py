import os
import subprocess
import threading
import time

import logger
from process_holder import ProcessHolder

LOG = logger.get_logger('agent_tracker')


class AgentHolder(ProcessHolder):

    def __init__(self, agent_dir, recycle_queue):
        super(AgentHolder, self).__init__(recycle_queue)
        self.agent_dir = agent_dir
        self.agent_process = None
        self.log_thread = None
        self.process_id = None
        self.last_check_time = int(time.time())

    def start(self):
        LOG.info('______ start agent: %s', self.agent_dir)
        # print self.agent_dir
        py = '%s\\venv\\Scripts\\python' % self.agent_dir
        entry = '%s\\agent.py' % self.agent_dir
        self.agent_process = subprocess.Popen([py, entry], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if self.agent_process.pid <= 0:
            LOG.error('failed to start agent')
            return None

        ProcessHolder.set_nonblocking(self.agent_process.stdout.fileno())
        ProcessHolder.set_nonblocking(self.agent_process.stderr.fileno())

        self.log_thread = DumpLogThread(self)
        self.log_thread.start()

        return self.agent_process.pid

    def stop(self):
        # LOG.debug('...... stop-agent, gpid:%d, pid:%d' % (os.getpgid(self.agent_process.pid), self.agent_process.pid))
        LOG.info('______ stop agent')
        if self.log_thread:
            self.log_thread.stop()

        self.kill_process(self.agent_process)
        self.agent_process = None

        # os.popen('taskkill /f /pid %s /T' % self.agent_process.pid)
        # if self.agent_process:
        #     self.agent_process.wait()


class DumpLogThread(threading.Thread):

    def __init__(self, agent_tracker):
        super(DumpLogThread, self).__init__()
        self.agent_tracker = agent_tracker
        self.RUN = True

    def run(self):
        while self.RUN:
            try:
                for line in self.agent_tracker.collect(self.agent_tracker.agent_process):
                    self.process_line(line)
                time.sleep(1)
            except Exception as e:
                LOG.error('dump log error: %s', e.args)

    def stop(self):
        self.RUN = False

    def process_line(self, line):
        LOG.debug(line)
        if line.find('Sender Running') > -1:
            self.agent_tracker.last_check_time = int(time.time())
