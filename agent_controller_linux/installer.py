import os
import subprocess

import logger
from process_holder import ProcessHolder

LOG = logger.get_logger('InstallTracker')


class Installer(ProcessHolder):

    def __init__(self, install_package_dir, recycle_queue):
        super(Installer, self).__init__(recycle_queue)
        self.install_package_dir = install_package_dir
        self.install_process = None
        self.uninstall_process = None
        self.RUN = True

    def install(self):
        LOG.info('****** install: %s', self.install_package_dir)
        self.RUN = True
        self.install_process = subprocess.Popen(['%s/agent_install.sh' % self.install_package_dir],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE, close_fds=True,
                                                preexec_fn=os.setsid)
        if self.install_process.pid <= 0:
            LOG.error('failed to install agent')
            return False

        ProcessHolder.set_nonblocking(self.install_process.stdout.fileno())
        ProcessHolder.set_nonblocking(self.install_process.stderr.fileno())

        while self.RUN:
            for line in self.collect(self.install_process):
                LOG.debug(line)
                if line.find('Successfully installed') > -1:
                    self.wait_process(self.install_process)
                    self.install_process = None
                    return True
                elif line.find('NSight-Agent installed') > -1:
                    self.wait_process(self.install_process)
                    self.install_process = None
                    return True

    def uninstall(self):
        LOG.info('****** uninstall')
        self.RUN = True
        try:
            self.uninstall_process = subprocess.Popen(['%s/agent_uninstall.sh' % self.install_package_dir],
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE, close_fds=True,
                                                      preexec_fn=os.setsid)
        except Exception:
            os.popen('rm -rf %s' % self.install_package_dir)
            return True

        if self.uninstall_process.pid <= 0:
            LOG.error('failed to install agent')
            return False

        ProcessHolder.set_nonblocking(self.uninstall_process.stdout.fileno())
        ProcessHolder.set_nonblocking(self.uninstall_process.stderr.fileno())

        while self.RUN:
            for line in self.collect(self.uninstall_process):
                LOG.debug(line)
                if line.find('NSight-Agent uninstalled') > -1:
                    self.wait_process(self.uninstall_process)
                    self.uninstall_process = None
                    return True

    def terminate(self):
        LOG.info('****** terminate installer')
        if self.install_process:
            self.kill_process(self.install_process)
            self.install_process = None
        if self.uninstall_process:
            self.kill_process(self.uninstall_process)
            self.uninstall_process = None
        self.RUN = False
