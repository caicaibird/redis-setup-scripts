#!/bin/bash

echo "please input redis type(single, ha, cluster, proxy):"

read -r type

log_path="/opt/redis/log"
conf_path="/opt/redis/conf"
data_path="/opt/redis/data"
codis_path="/opt/redis/codis-3.2.2"
redis_path="/opt/redis/redis-5.0.7/src"

start_single_redis() {
  rm -f ${data_path}/6379/*

  cp ../conf/redis.conf ${conf_path}/redis-single-6379.conf
  echo "port 6379" >>${conf_path}/redis-single-6379.conf

  nohup "${redis_path}/redis-server" ${conf_path}/redis-single-6379.conf >>${log_path}/6379.log 2>&1 &
}

start_ha_redis() {
  rm -f ${data_path}/638*/* ${data_path}/638*/*

  for i in $(seq 6380 6381); do
    cp ../conf/redis.conf ${conf_path}/redis-ha-"${i}".conf
    echo "port ${i}" >>${conf_path}/redis-ha-"${i}".conf

  done
  cp ../conf/redis.conf ${conf_path}/redis-ha-6381.conf
  echo "port 6381" >>${conf_path}/redis-ha-6381.conf

  nohup "${redis_path}/redis-server" ${conf_path}/redis-ha-6380.conf >>${log_path}/6380.log 2>&1 &
  nohup "${redis_path}/redis-server" ${conf_path}/redis-ha-6381.conf --slaveof 127.0.0.1 6380 >>${log_path}/6381.log 2>&1 &
}

start_cluster_redis() {
  rm -f ${data_path}/800*/*

  for i in $(seq 8000 8005); do
    cp ../conf/redis.conf "${conf_path}/redis-cluster-${i}.conf"
    {
      echo "port ${i}"
      echo "cluster-enabled yes"
      echo "cluster-node-timeout 15000"
      echo "cluster-config-file ${data_path}/${i}/nodes-${i}.conf"
    } >>"${conf_path}/redis-cluster-${i}.conf"
    nohup "${redis_path}/redis-server" "${conf_path}/redis-cluster-${i}.conf" >>"${log_path}/${i}.log" 2>&1 &
  done

  sleep 1

  echo "yes" | ${redis_path}/redis-cli --cluster create 127.0.0.1:8000 127.0.0.1:8001 127.0.0.1:8002 \
    127.0.0.1:8003 127.0.0.1:8004 127.0.0.1:8005 --cluster-replicas 1
}

start_proxy_redis() {
  rm -f ${data_path}/900*/*

  for i in $(seq 9000 9005); do
    cp ../conf/redis-proxy.conf "${conf_path}/redis-proxy-${i}.conf"
    {
      echo "port ${i}"
      echo "dir /opt/redis/data/${i}"
      echo "pidfile /tmp/redis_${i}.pid"
      echo "logfile /opt/redis/log/${i}.log"
    } >>"${conf_path}/redis-proxy-${i}.conf"
  done

  for i in $(seq 0 2); do
    cp ../conf/proxy.toml "${conf_path}/proxy-1900${i}.toml"
    sed -i "s/19000/1900${i}/g" "$conf_path/proxy-1900${i}.toml"
  done

  sed -i "s/11080/11081/g" "$conf_path/proxy-19000.toml"
  sed -i "s/11080/11082/g" "$conf_path/proxy-19001.toml"
  sed -i "s/11080/11083/g" "$conf_path/proxy-19002.toml"
  cp ../conf/dashboard.toml "${conf_path}/dashboard.toml"

  # 启动所有节点，6个Server，3个Proxy，1个Dashboard，1个Fe
  nohup "${codis_path}/codis-dashboard" "--config=${conf_path}/dashboard.toml" "--log=${log_path}/18080.log" "--log-level=INFO" "--pidfile=/var/run/dashboard.pid" >"${log_path}/18080.out" 2>&1 </dev/null &
  nohup "${codis_path}/codis-fe" "--assets-dir=/opt/redis/codis-3.2.2/assets" "--filesystem=/tmp/codis" "--log=${log_path}/9090.log" "--pidfile=/var/run/9090.pid" "--log-level=INFO" "--listen=0.0.0.0:9090" >"${log_path}/9090.out" 2>&1 </dev/null &
  nohup "${codis_path}/codis-proxy" "--config=${conf_path}/proxy-19000.toml" "--dashboard=18080" "--log=${log_path}/19000.log" "--log-level=INFO" "--ncpu=4" "--pidfile=/var/run/proxy-19000.pid" >"${log_path}/19000.out" 2>&1 </dev/null &
  nohup "${codis_path}/codis-proxy" "--config=${conf_path}/proxy-19001.toml" "--dashboard=18080" "--log=${log_path}/19001.log" "--log-level=INFO" "--ncpu=4" "--pidfile=/var/run/proxy-19001.pid" >"${log_path}/19001.out" 2>&1 </dev/null &
  nohup "${codis_path}/codis-proxy" "--config=${conf_path}/proxy-19002.toml" "--dashboard=18080" "--log=${log_path}/19002.log" "--log-level=INFO" "--ncpu=4" "--pidfile=/var/run/proxy-19002.pid" >"${log_path}/19002.out" 2>&1 </dev/null &
  nohup "${codis_path}/codis-server" ${conf_path}/redis-proxy-9000.conf >${log_path}/9000.log 2>&1 &
  nohup "${codis_path}/codis-server" ${conf_path}/redis-proxy-9001.conf >${log_path}/9001.log 2>&1 &
  nohup "${codis_path}/codis-server" ${conf_path}/redis-proxy-9002.conf >${log_path}/9002.log 2>&1 &
  nohup "${codis_path}/codis-server" ${conf_path}/redis-proxy-9003.conf >${log_path}/9003.log 2>&1 &
  nohup "${codis_path}/codis-server" ${conf_path}/redis-proxy-9004.conf >${log_path}/9004.log 2>&1 &
  nohup "${codis_path}/codis-server" ${conf_path}/redis-proxy-9005.conf >${log_path}/9005.log 2>&1 &
  sleep 2

  # 纳管Proxy节点
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --create-proxy --addr=127.0.0.1:11081
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --create-proxy --addr=127.0.0.1:11082
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --create-proxy --addr=127.0.0.1:11083
  sleep 1

  # 创建分组
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --create-group --gid=1
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --create-group --gid=2
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --create-group --gid=3
  sleep 1

  # 添加Server至分组
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --group-add --gid=1 --addr=127.0.0.1:9000
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --group-add --gid=1 --addr=127.0.0.1:9001
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --group-add --gid=2 --addr=127.0.0.1:9002
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --group-add --gid=2 --addr=127.0.0.1:9003
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --group-add --gid=3 --addr=127.0.0.1:9004
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --group-add --gid=3 --addr=127.0.0.1:9005
  sleep 1

  # 形成主备关系
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --promote-server --gid=1 --addr=127.0.0.1:9000
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --sync-action --create --addr=127.0.0.1:9001
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --promote-server --gid=2 --addr=127.0.0.1:9002
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --sync-action --create --addr=127.0.0.1:9003
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --promote-server --gid=3 --addr=127.0.0.1:9004
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --sync-action --create --addr=127.0.0.1:9005
  sleep 1

  # 平均分配slots
  ${codis_path}/codis-admin --dashboard=127.0.0.1:18080 --rebalance --confirm
}

start_redis() {
  if eval "start_${type}_redis"; then
    echo "start ${type} succeed."
  else
    echo $?
    echo "start ${type} failed."
  fi
}

mkdir -p ${log_path}
mkdir -p ${data_path}
mkdir -p ${conf_path}

start_redis
