import os
import subprocess

import logger
from process_holder import ProcessHolder

LOG = logger.get_logger('InstallTracker')


class Installer(ProcessHolder):

    def __init__(self, install_package_dir):
        super(Installer, self).__init__()
        self.install_package_dir = install_package_dir
        self.install_process = None
        self.uninstall_process = None

    def install(self):
        LOG.debug('****** install: %s', self.install_package_dir)
        self.install_process = subprocess.Popen(['%s\\agent_install.bat' % self.install_package_dir],
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if self.install_process.pid <= 0:
            LOG.error('failed to install agent')
            return False

        ProcessHolder.set_nonblocking(self.install_process.stdout.fileno())
        ProcessHolder.set_nonblocking(self.install_process.stderr.fileno())

        while True:
            for line in self.collect(self.install_process):
                LOG.debug(line)
                if line.find('Successfully installed') > -1:
                    if self.install_process:
                        self.install_process.wait()
                    return True
                elif line.find('NSight-Agent installed') > -1:
                    if self.install_process:
                        self.install_process.wait()
                    return True

    def uninstall(self):
        LOG.debug('****** uninstall')
        try:
            self.uninstall_process = subprocess.Popen(['%s/agent_uninstall.sh' % self.install_package_dir],
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE)
        except Exception:
            os.system('rd /s /q %s' % self.install_package_dir)
            return True

        if self.uninstall_process.pid <= 0:
            LOG.error('failed to install agent')
            return False

        ProcessHolder.set_nonblocking(self.uninstall_process.stdout.fileno())
        ProcessHolder.set_nonblocking(self.uninstall_process.stderr.fileno())

        while True:
            for line in self.collect(self.uninstall_process):
                LOG.debug(line)
                if line.find('NSight-Agent uninstalled') > -1:
                    if self.uninstall_process:
                        self.uninstall_process.wait()
                    return True
