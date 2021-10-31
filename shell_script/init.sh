#!/bin/bash

# remake directories,make sure you have the right to operate /opt
rm -rf /opt/redis
mkdir -p /opt/redis/conf /opt/redis/log
mkdir -p /opt/redis/data/6379
mkdir -p /opt/redis/data/6380 /opt/redis/data/6381
mkdir -p /opt/redis/data/8000 /opt/redis/data/8001 /opt/redis/data/8002 /opt/redis/data/8003 /opt/redis/data/8004 /opt/redis/data/8005
mkdir -p /opt/redis/data/9000 /opt/redis/data/9001 /opt/redis/data/9002 /opt/redis/data/9003 /opt/redis/data/9004 /opt/redis/data/9005
echo "remake directories successfully"

# cd work path
cd "$(find / -name "redis-setup-scripts")"/components || (echo "cd work path failed!" && exit)

# uncompress source files
tar -zxvf codis-3.2.2.tar.gz -C /opt/redis
tar -zxvf redis-5.0.7.tar.gz -C /opt/redis
echo "uncompress source files successfully"


# compile source files
mv /opt/redis/codis3.2.2-go1.8.5-linux /opt/redis/codis-3.2.2
cd /opt/redis/redis-5.0.7/src && make
echo "compile source files successfully"
