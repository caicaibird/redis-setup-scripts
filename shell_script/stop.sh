#!/bin/bash

echo "please input redis type(single, ha, cluster, proxy):"

read -r type

(($(pgrep -c "codis|redis") == 0)) && echo "there is no redis program." && exit 0

function stop_single_redis() {
  pgrep -f "redis.*6379" | xargs kill -9
}

function stop_ha_redis() {
  pgrep -f "redis.*638" | xargs kill -9
}

function stop_cluster_redis() {
  pgrep -f "redis.*800" | xargs kill -9
}

function stop_proxy_redis() {
  pgrep -f "codis" | xargs kill -9
  rm -rf /tmp/codis
}

function stop_redis() {
  if eval "stop_${type}_redis"; then
    echo "stop ${type} succeed."
  else
    echo "stop ${type} failed."
  fi
}

stop_redis
