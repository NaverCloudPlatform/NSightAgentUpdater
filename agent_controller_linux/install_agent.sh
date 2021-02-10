#!/bin/bash

AGENT_ROOT=$(cd `dirname $0`; pwd)

if [ -f /etc/redhat-release ]; then
  OS=`cat /etc/redhat-release | awk '{print $1}'`
  VER=`cat /etc/redhat-release | awk '{for(i=1;i<=NF;i++){if($i=="release")print$(i+1)}}'`
  MVER=`echo $VER | awk -F '.' '{print $1}'`
elif [ `command -v lsb_release` ]; then
  OS=`lsb_release -i 2> /dev/null | awk '{print $3}'`
  VER=`lsb_release -r 2> /dev/null | awk '{print $2}'`
  MVER=`echo $VER | awk -F '.' '{print $1}'`
elif [ -f /etc/SuSE-release ]; then
  OS=`head -1 /etc/SuSE-release | awk '{print $1}'`
  VER=`sed -n 2p /etc/SuSE-release | awk '{print $3}'`
  MVER=$VER
else
  OS="unknow"
  VER="unknow"
  MVER="unknow"
fi

#echo $OS
#echo $VER
#echo $MVER

if [ $OS == "Ubuntu" ]; then
  #.$AGENT_ROOT/build_env_ubuntu.sh
  echo "Ubuntu"
  if [ $MVER == "18" ]; then
    echo "18"
    sudo $AGENT_ROOT/build_env_ubuntu18.sh
    sudo $AGENT_ROOT/agent_default.sh install
    sudo $AGENT_ROOT/agent_default.sh start
  elif [ $MVER == "17" ]; then
    echo "17"
    sudo $AGENT_ROOT/agent_default.sh install $1
    sudo $AGENT_ROOT/agent_default.sh start
  elif [ $MVER == "16" ]; then
    echo "16"
    sudo $AGENT_ROOT/build_env_ubuntu.sh
    sudo $AGENT_ROOT/agent_ubuntu16.sh install
    sudo $AGENT_ROOT/agent_ubuntu16.sh start
  elif [ $MVER == "14" ]; then
    echo "14"
    sudo $AGENT_ROOT/build_env_ubuntu.sh
    sudo $AGENT_ROOT/agent_ubuntu.sh install
    sudo $AGENT_ROOT/agent_ubuntu.sh start
  elif [ $MVER == "12" ]; then
    echo "12"
    sudo $AGENT_ROOT/build_env_ubuntu.sh
    sudo $AGENT_ROOT/agent_ubuntu.sh install
    sudo $AGENT_ROOT/agent_ubuntu.sh start
  fi
elif [ $OS == "CentOS" ]; then
  echo "Centos"
  if [ $MVER == "8" ]; then
    echo "8"
    sudo $AGENT_ROOT/build_env_centos.sh
    sudo $AGENT_ROOT/agent_default.sh install
    sudo $AGENT_ROOT/agent_default.sh enable
    sudo $AGENT_ROOT/agent_default.sh start
  elif [ $MVER == "7" ]; then
    echo "7"
    sudo $AGENT_ROOT/build_env_centos.sh
    sudo $AGENT_ROOT/agent_default.sh install
    sudo $AGENT_ROOT/agent_default.sh enable
    sudo $AGENT_ROOT/agent_default.sh start
  elif [ $MVER == "6" ]; then
    echo "6"
    sudo $AGENT_ROOT/build_env_centos.sh
    sudo $AGENT_ROOT/agent_centos.sh install
    sudo $AGENT_ROOT/agent_centos.sh enable
    sudo $AGENT_ROOT/agent_centos.sh start
  elif [ $MVER == "5" ]; then
    echo "5"
    sudo $AGENT_ROOT/build_env_centos5.sh
    sudo $AGENT_ROOT/agent_centos.sh install
    sudo $AGENT_ROOT/agent_centos.sh enable
    sudo $AGENT_ROOT/agent_centos.sh start
  fi
elif [ $OS == "Red" ]; then
  echo "Red Hat Enterprise Linux"
  if [ $MVER == "8" ]; then
    echo "8"
    sudo $AGENT_ROOT/build_env_centos.sh
    sudo $AGENT_ROOT/agent_rhel8.sh install
    sudo $AGENT_ROOT/agent_rhel8.sh enable
    sudo $AGENT_ROOT/agent_rhel8.sh start
  elif [ $MVER == "7" ]; then
    echo "7"
    sudo $AGENT_ROOT/build_env_centos.sh
    sudo $AGENT_ROOT/agent_default.sh install
    sudo $AGENT_ROOT/agent_default.sh enable
    sudo $AGENT_ROOT/agent_default.sh start
  elif [ $MVER == "6" ]; then
    echo "6"
    sudo $AGENT_ROOT/build_env_centos.sh
    sudo $AGENT_ROOT/agent_centos.sh install
    sudo $AGENT_ROOT/agent_centos.sh enable
    sudo $AGENT_ROOT/agent_centos.sh start
  fi
elif [ $OS == "SUSE" ]; then
  echo "SUSE Linux"
  if [ $MVER == "12" ]; then
    echo "12"
    sudo $AGENT_ROOT/build_env_suse.sh
    sudo $AGENT_ROOT/agent_suse12.sh install
    sudo $AGENT_ROOT/agent_suse12.sh start
  fi
  if [ $MVER == "11" ]; then
    echo "11"
    sudo $AGENT_ROOT/build_env_suse.sh
    sudo $AGENT_ROOT/agent_suse11.sh install
    sudo $AGENT_ROOT/agent_suse11.sh enable
    sudo $AGENT_ROOT/agent_suse11.sh start
  fi
fi
