import os
import servicemanager
import sys
import win32event
import win32service

import win32serviceutil
import winerror

import logger

from config import controller_config
from controller import Controller

LOG = logger.get_logger('AgentService')


class AgentService(win32serviceutil.ServiceFramework):

    _svc_name_ = "nsight2_agent"
    _svc_display_name_ = "nsight2.0_agent"
    _svc_description_ = "nsight2.0 agent"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        self.controller = None

    def SvcDoRun(self):
        try:
            self.controller = Controller(controller_config.get_configs())
            self.controller.start()
        except Exception as e:
            LOG.exception("error:%s" % e.args)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.controller:
            self.controller.stop()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        try:
            evtsrc_dll = os.path.abspath(servicemanager.__file__)
            servicemanager.PrepareToHostSingle(AgentService)
            servicemanager.Initialize('AgentService', evtsrc_dll)
            servicemanager.StartServiceCtrlDispatcher()
        except win32service.error, details:
            if details[0] == winerror.ERROR_FAILED_SERVICE_CONTROLLER_CONNECT:
                win32serviceutil.usage()
    else:
        win32serviceutil.HandleCommandLine(AgentService)
