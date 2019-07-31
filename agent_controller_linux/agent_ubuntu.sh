#!/bin/bash

AGENT_ROOT=$(cd `dirname $0`; pwd)
PYTHON_HOME=$AGENT_ROOT/agent_python
VENV_BIN=$AGENT_ROOT/.venv/bin
PYTHON_PATH=$VENV_BIN/python
AGENT_PATH=$AGENT_ROOT/controller.py
SERVICE_SOURCE_FILE="nsight-agent-service"
SERVICE_FILE="nsight-agent"

install_agent() {
  if [ ! -e $PYTHON_HOME/bin/python ]; then
    if [ ! -d $AGENT_ROOT/install/Python-2.7.5 ]; then
      tar xzf $AGENT_ROOT/install/Python-2.7.5.tar.gz -C $AGENT_ROOT/install
    fi
    cd $AGENT_ROOT/install/Python-2.7.5
    ./configure --prefix=$PYTHON_HOME
    make
    make install
    cd $AGENT_ROOT
  fi

  export PATH=$PYTHON_HOME/bin:$PATH

  python $AGENT_ROOT/virtualenv/virtualenv.py -p /usr/bin/python2.7 $AGENT_ROOT/.venv
  $VENV_BIN/pip install --no-index --find-links=$AGENT_ROOT/wheels APScheduler
  if [ $? -ne 0 ]
  then
    echo "install wheels failure"
    return
  fi

  PYTHON_PATH=${PYTHON_PATH//\//\\\/}
  AGENT_PATH=${AGENT_PATH//\//\\\/}
  sed -e "s/PYTHON/$PYTHON_PATH/g" -e "s/AGENT/$AGENT_PATH/g" ${AGENT_ROOT}/${SERVICE_SOURCE_FILE} > ${AGENT_ROOT}/${SERVICE_FILE}
  chmod +x ${AGENT_ROOT}/${SERVICE_FILE}
  mv ${AGENT_ROOT}/${SERVICE_FILE} /etc/init.d/
  enable_agent
}

start_agent() {
  cd /etc/init.d/ && service ${SERVICE_FILE} start && cd -
}

stop_agent() {
  cd /etc/init.d/ && service ${SERVICE_FILE} stop && cd -
}

enable_agent() {
  cd /etc/init.d/ && update-rc.d ${SERVICE_FILE} defaults 90 && cd -
}

disable_agent() {
  cd /etc/init.d/ && update-rc.d -f ${SERVICE_FILE} remove && cd -
}

case $1 in
  install)
    install_agent
    ;;
  start)
    start_agent
    ;;
  stop)
    stop_agent
    ;;
  enable)
    enable_agent
    ;;
  disable)
    disable_agent
    ;;
  *)
    ;;
esac
