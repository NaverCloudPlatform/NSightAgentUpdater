import Queue
import datetime
import json
import os
import ssl
import sys
import time
import urllib2

from apscheduler.schedulers.blocking import BlockingScheduler

import logger
import utils
from agent_holder import AgentHolder
from config import controller_config
from installer import Installer
from process_holder import ProcessRecycle

LOG = logger.get_logger('controller')


class Controller:

    def __init__(self, configs):
        self.main_loop_lock = False
        self.scheduler = None
        self.configs = configs
        # self.installer = None
        self.agent_holder = None

        self.need_download = False
        self.need_install = False
        self.need_start = False
        self.need_version_recheck = False

        self.download_path = None
        self.checksum = None

        self.ssl_context = ssl.create_default_context()

        self.recycle_queue = Queue.Queue()
        # self.block_count = 0

    def start(self):
        LOG.debug('controller started')

        recycle_thread = ProcessRecycle(self.recycle_queue)
        recycle_thread.start()

        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(self.update_check, trigger='interval', seconds=self.configs['update_check_period'], next_run_time=datetime.datetime.now())
        self.scheduler.add_job(self.main_job, trigger='cron', minute='*/%d' % self.configs['main_loop_period_minute'], second='0')
        self.scheduler.start()
        LOG.debug('controller stopped')

    def stop(self):
        self.stop_agent()
        if self.scheduler:
            self.scheduler.shutdown()

    def main_job(self):
        if self.main_loop_lock:
            # if self.block_count >= 3:
            #     self.terminate_installer()
            #     self.block_count = 0
            return
        self.main_loop_lock = True
        # self.block_count = 0
        self.health_check()
        if self.need_version_recheck:
            self.version_recheck()

        try:
            if self.need_download:
                LOG.info('********************* download')
                if self.download_agent():
                    self.need_download = False
                    self.need_install = True

            if self.need_install:
                LOG.info('********************* install')

                old_folder = self.get_latest_install_folder()

                update = self.need_install_check()
                # reinstall current agent package
                if not update:
                    self.stop_agent()
                    self.uninstall_agent(old_folder)

                package_path = self.get_latest_install_package()

                if package_path:
                    agent_dir = self.install_agent(package_path)

                    # new agent installed, remove old agent folder
                    if update:
                        self.stop_agent()
                        self.uninstall_agent(old_folder)

                    self.start_agent(agent_dir)
                    self.need_install = False
                    self.need_start = False

            elif self.need_start:
                LOG.info('********************* restart')
                self.need_start = False

                self.stop_agent()

                agent_dir = self.get_latest_install_folder()
                if not agent_dir:
                    package_path = self.get_latest_install_package()
                    if package_path:
                        LOG.debug('********************* restart install')
                        agent_dir = self.install_agent(package_path)
                    else:
                        return

                LOG.debug('********************* restart start')
                self.start_agent(agent_dir)

        except Exception as e:
            pass
        finally:
            self.main_loop_lock = False

    def install_agent(self, package_path):
        checksum = utils.get_checksum(package_path, self.get_checksum_dir())
        if not utils.check_file(package_path, checksum):
            LOG.debug("check downloaded package failed, removing %s", package_path)
            os.remove(package_path)
            utils.remove_checksum(package_path, self.get_checksum_dir())
            return None

        dirname = utils.get_file_name_without_extension(package_path)
        agent_dir = '%s\%s' % (self.get_install_dir(), dirname)
        tmp_dir = '%s\%s' % (self.get_tmp_dir(), dirname)

        try:
            if utils.unzip(package_path, tmp_dir):
                tmp_name = os.listdir(tmp_dir)[0]
                tmp_path = '%s\%s' % (tmp_dir, tmp_name)
                ren_path = '%s\%s' % (tmp_dir, dirname)

                if os.system('ren "%s" "%s"' % (tmp_path, dirname)) != 0:
                    return None

                if os.system('move "%s" "%s"' % (ren_path, self.get_install_dir())) != 0:
                    return None
            else:
                return None
        finally:
            if os.path.isdir(tmp_dir):
                os.system('rd /s /q "%s"' % tmp_dir)

        installer = Installer(agent_dir, self.recycle_queue)
        installer.install()
        return agent_dir

    def uninstall_agent(self, agent_dir=None):
        # if self.installer is None:
        #     if agent_dir and os.path.isdir(agent_dir):
        #         self.installer = Installer(agent_dir, self.recycle_queue)
        #     else:
        #         return
        # self.installer.uninstall()
        # self.installer = None
        if agent_dir and os.path.isdir(agent_dir):
            installer = Installer(agent_dir, self.recycle_queue)
            installer.uninstall()

    # def terminate_installer(self):
    #     if self.installer:
    #         self.installer.terminate()
    #         self.installer = None

    def start_agent(self, agent_dir):
        if agent_dir:
            self.agent_holder = AgentHolder(agent_dir, self.recycle_queue)
            pid = str(self.agent_holder.start())
            if pid:
                self.save_pid_to_disk(pid)

    def stop_agent(self):
        if self.agent_holder is None:
            # pid = self.get_pid_from_disk()
            # if pid:
            #     os.popen('taskkill /f /pid %s /T' % pid)
            #     self.save_pid_to_disk()
            pass
        else:
            self.agent_holder.stop()
            self.agent_holder = None
            self.save_pid_to_disk()

    def health_check(self):
        if self.agent_holder:
            LOG.info('.............. last check before: %d seconds' % (int(time.time()) - self.agent_holder.last_check_time))
            if int(time.time()) - self.agent_holder.last_check_time > self.configs['health_check_threshold']:
                LOG.info('.............. check health, failed')
                self.need_install = True
            else:
                self.need_start = False
        else:
            LOG.info('.............. agent_holder is None')
            self.need_start = True

    def update_check(self):
        if self.check_new_version():
            self.need_download = True
        else:
            self.need_download = False

        if self.need_install_check():
            LOG.info('a later version downloaded, need install it')
            self.need_install = True

    def need_install_check(self):
        download_version = int(utils.get_version_from_path(self.get_latest_install_package()))
        install_version = int(utils.get_version_from_path(self.get_latest_install_folder()))
        if download_version > install_version:
            return True
        else:
            return False

    def version_recheck(self):
        LOG.info('^^^^^^^^^^^ version_recheck')
        self.need_version_recheck = False
        if self.check_new_version():
            self.need_download = True
        else:
            self.need_download = False

    def check_new_version(self):
        try:
            url = '%s%s' % (self.configs['update_server_url'], self.configs['update_info_path'])
            req = urllib2.Request(url)
            response = urllib2.urlopen(req, timeout=3, context=self.ssl_context)
            response_json = json.loads(response.read())
            new_version = response_json['version']
            new_path = response_json['path']
            checksum = response_json['checksum']
            # print new_version
            # print new_path

            version = int(utils.get_version_from_path(self.get_latest_install_package()))
            if new_version > version:
                self.download_path = new_path
                self.checksum = checksum
                LOG.info('check new version: new version valid')
                return True
            else:
                LOG.info('check new version: it is the latest version')
                return False
        except Exception as e:
            self.need_version_recheck = True
            LOG.exception('check new version failed, err: %s', e)
            return False

    def download_agent(self):
        if self.download_path and self.checksum:
            url = '%s/%s' % (self.configs['update_server_url'], self.download_path)
            f = urllib2.urlopen(url, timeout=300, context=self.ssl_context)
            package_name = utils.get_file_name(url)
            package_path = '%s/%s' % (self.get_download_dir(), package_name)
            with open(package_path, 'wb') as target:
                target.write(f.read())

            if not utils.check_file(package_path, self.checksum):
                os.remove(package_path)
                LOG.debug('checksum failed, removing %s', package_name)
                return False
            else:
                utils.save_checksum(self.checksum, package_path, self.get_checksum_dir())
                LOG.debug('download %s success', package_name)

        self.download_path = None
        self.checksum = None
        return True

    def get_install_dir(self):
        path = os.path.join(self.configs['home_dir'], 'install_folders')
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    def get_download_dir(self):
        path = os.path.join(self.configs['home_dir'], 'download')
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    def get_checksum_dir(self):
        path = os.path.join(self.configs['home_dir'], 'checksum')
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    def get_tmp_dir(self):
        path = os.path.join(self.configs['home_dir'], 'tmp')
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    def get_latest_install_folder(self):
        latest_version = 0
        latest_folder_path = None

        if not os.path.isdir(self.get_install_dir()):
            return None

        for folder in os.listdir(self.get_install_dir()):
            version = utils.get_version(folder)
            if version.isdigit() and int(version) > latest_version:
                latest_version = int(version)
                latest_folder_path = folder

        if latest_folder_path:
            return '%s\%s' % (self.get_install_dir(), latest_folder_path)
        else:
            return None

    def get_latest_install_package(self):
        latest_version = 0
        latest_package = None

        if not os.path.isdir(self.get_download_dir()):
            return None

        for package in os.listdir(self.get_download_dir()):
            version = utils.get_version(package)
            if version.isdigit() and int(version) > latest_version:
                latest_version = int(version)
                latest_package = package

        if latest_package:
            return '%s\%s' % (self.get_download_dir(), latest_package)
        else:
            return None

    # for debug
    def get_tmp_dir(self):
        return os.path.join(self.configs['home_dir'], 'tmp')

    def save_pid_to_disk(self, process_id=''):
        with open('%s\pid' % self.configs['home_dir'], 'w+') as f:
            f.truncate()
            f.write(process_id)

    def get_pid_from_disk(self):
        with open('%s\pid' % self.configs['home_dir'], 'a+') as f:
            return f.read()


def main(argv):
    controller = Controller(controller_config.get_configs())
    controller.start()

    # if argv[1] == 'install':
    #     package_path = controller.get_latest_install_package()
    #     print controller.install_agent(package_path)
    # elif argv[1] == 'uninstall':
    #     agent_dir = controller.get_latest_install_folder()
    #     controller.uninstall_agent(agent_dir)
    # elif argv[1] == 'start':
    #     agent_dir = controller.get_latest_install_folder()
    #     if agent_dir:
    #         controller.start_agent(agent_dir)
    #     else:
    #         package_path = controller.get_latest_install_package()
    #         agent_dir = controller.install_agent(package_path)
    #         controller.start_agent(agent_dir)
    # elif argv[1] == 'stop':
    #     controller.stop_agent()

    # controller.update_check()
    # controller.download_agent()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
