# 概览
快速搭建redis实验环境的shell脚本，包括单机，主备，原生集群，codis集群

使用环境为Linux，需要能编译redis源码

redis版本为5.0.3，codis版本为3.2.2



# 目录

- component：二进制组件，包括codis-3.2.2，redis-5.0.7
- conf：初始配置文件
- scripts：环境初始化，启动，停止redis的脚本



# 快速开始

进入scripts目录：cd {project_path}/scripts

初始化环境：bash init.sh

启动单机redis：echo single | bash start.sh

启动主备redis：echo ha| bash start.sh

启动集群redis：echo cluster| bash start.sh

启动codis：echo proxy| bash start.sh

停止所有redis：echo all | bash stop.sh
