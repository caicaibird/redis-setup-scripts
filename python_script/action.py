import cmd
import os
import subprocess
import shutil
import time


class Action(cmd.Cmd):
    intro = "快速搭建redis环境，输入 help 或者 ? 列出命令。"

    prompt = "action>"

    def do_start(self, _):
        """
        启动redis，支持部署类型：single，ha，cluster，proxy
        single：单机，端口6379
        ha：主备，端口6380—6381
        cluster：原生集群，端口8000—8005
        proxy：codis集群，端口19000—19002
        """
        redis_type = input("请输入类型如下：single，ha，cluster，proxy:")
        start_redis(redis_type)

    def do_stop(self, _):
        """
        停止redis，支持部署类型：single，ha，cluster，proxy
        """
        redis_type = input("请输入类型如下：single，ha，cluster，proxy:")
        stop_redis(redis_type)

    def do_init(self, _):
        """
        初始化运行环境
        """
        if os.path.exists("/opt/redis"):
            shutil.rmtree("/opt/redis")
        if os.path.exists("/opt/redis-5.0.7"):
            shutil.rmtree("/opt/redis-5.0.7")
        if os.path.exists("/opt/codis-3.2.2"):
            shutil.rmtree("/opt/codis-3.2.2")

        ports = ["6379", "6380", "6381", "8000", "8001", "8002", "8003", "8004", "8005", "9000", "9001", "9002", "9003",
                 "9004", "9005"]
        os.makedirs("/opt/redis/conf")
        os.makedirs("/opt/redis/log")
        for port in ports:
            os.makedirs("/opt/redis/data/" + port)
        os.chdir(os.path.abspath("../components"))
        subprocess.run("tar -zxvf codis-3.2.2.tar.gz -C /opt", shell=True)
        subprocess.run("tar -zxvf redis-5.0.7.tar.gz -C /opt", shell=True)
        subprocess.run("mv /opt/codis3.2.2-go1.8.5-linux /opt/codis-3.2.2", shell=True)
        subprocess.run("cd /opt/redis-5.0.7/src && make", shell=True)

    def do_exit(self, _):
        """
        退出
        """
        exit(0)

    def do_EOF(self, _):
        return True


log_path = "/opt/redis/log"
data_path = "/opt/redis/data"
bin_path = "/opt/redis-5.0.7/src"
codis_path = "/opt/codis-3.2.2"
conf_dst_path = "/opt/redis/conf"
conf_src_path = os.path.abspath("..") + "/conf"
proxy_ports = ["19000", "19001", "19002"]
redis_ports = {
    "single": ["6379"],
    "ha": ["6380", "6381"],
    "cluster": ["8000", "8001", "8002", "8003", "8004", "8005"],
    "proxy": ["9000", "9001", "9002", "9003", "9004", "9005"]
}


def start_redis(redis_type):
    if redis_type not in ["single", "ha", "proxy", "cluster"]:
        print("请输入类型如下：single，ha，cluster，proxy")
        return

    if exist_process(redis_type):
        print("%s is already running!" % redis_type)
        return

    prepare_conf(redis_type)

    clean_data(redis_type)

    if "single" == redis_type:
        subprocess.run('nohup "%s/redis-server" %s/redis-single-6379.conf --port 6379 > %s/6379.log 2>&1 &' % (
            bin_path, conf_dst_path, log_path), shell=True)
    elif "ha" == redis_type:
        subprocess.run('nohup "%s/redis-server" %s/redis-ha-6380.conf --port 6380 > %s/6380.log 2>&1 &' % (
            bin_path, conf_dst_path, log_path), shell=True)
        subprocess.run(
            'nohup "%s/redis-server" %s/redis-ha-6381.conf --port 6381 --slaveof 127.0.0.1 6380 > %s/6381.log 2>&1 &' % (
                bin_path, conf_dst_path, log_path), shell=True)
    elif "cluster" == redis_type:
        subprocess.run('nohup "%s/redis-server" %s/redis-cluster-8000.conf > %s/8000.log 2>&1 &' % (
            bin_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/redis-server" %s/redis-cluster-8001.conf > %s/8001.log 2>&1 &' % (
            bin_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/redis-server" %s/redis-cluster-8002.conf > %s/8002.log 2>&1 &' % (
            bin_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/redis-server" %s/redis-cluster-8003.conf > %s/8003.log 2>&1 &' % (
            bin_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/redis-server" %s/redis-cluster-8004.conf > %s/8004.log 2>&1 &' % (
            bin_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/redis-server" %s/redis-cluster-8005.conf > %s/8005.log 2>&1 &' % (
            bin_path, conf_dst_path, log_path), shell=True)
        time.sleep(1)
        print("初始化集群")
        output = subprocess.check_output(
            'echo "yes" | %s/redis-cli --cluster create 127.0.0.1:8000 127.0.0.1:8001 127.0.0.1:8002 127.0.0.1:8003 '
            '127.0.0.1:8004 127.0.0.1:8005 --cluster-replicas 1' % bin_path, shell=True, timeout=5000)
        print(str(output, encoding='utf-8'))
    elif "proxy" == redis_type:
        if os.path.exists("/tmp/codis"):
            shutil.rmtree("/tmp/codis")
        subprocess.run(
            'nohup "%s/codis-dashboard" "--config=%s/dashboard.toml" "--log=%s/18080.log" "--log-level=INFO" '
            '"--pidfile=/var/run/dashboard.pid" > "%s/18080.out" 2>&1 < /dev/null &' % (
                codis_path, conf_dst_path, log_path, log_path), shell=True)
        subprocess.run(
            'nohup "%s/codis-fe" "--assets-dir=%s/assets" "--filesystem=/tmp/codis" "--log=%s/9090.log" '
            '"--pidfile=/var/run/9090.pid" "--log-level=INFO" "--listen=0.0.0.0:9090" > "%s/9090.out" 2>&1 < '
            '/dev/null &' % (codis_path, codis_path, log_path, log_path), shell=True)
        time.sleep(1)
        print("启动redis-server")
        subprocess.run('nohup "%s/codis-server" %s/redis-proxy-9000.conf > %s/9000.log 2>&1 &' % (
            codis_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/codis-server" %s/redis-proxy-9001.conf > %s/9001.log 2>&1 &' % (
            codis_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/codis-server" %s/redis-proxy-9002.conf > %s/9002.log 2>&1 &' % (
            codis_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/codis-server" %s/redis-proxy-9003.conf > %s/9003.log 2>&1 &' % (
            codis_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/codis-server" %s/redis-proxy-9004.conf > %s/9004.log 2>&1 &' % (
            codis_path, conf_dst_path, log_path), shell=True)
        subprocess.run('nohup "%s/codis-server" %s/redis-proxy-9005.conf > %s/9005.log 2>&1 &' % (
            codis_path, conf_dst_path, log_path), shell=True)
        subprocess.run(
            'nohup "%s/codis-proxy" "--config=%s/proxy-19000.toml" "--dashboard=18080" "--log=%s/19000.log" '
            '"--log-level=INFO" "--ncpu=4" "--pidfile=/var/run/proxy-19000.pid" > "%s/19000.out" 2>&1 < /dev/null &' % (
                codis_path, conf_dst_path, log_path, log_path), shell=True)
        subprocess.run(
            'nohup "%s/codis-proxy" "--config=%s/proxy-19001.toml" "--dashboard=18080" "--log=%s/19001.log" '
            '"--log-level=INFO" "--ncpu=4" "--pidfile=/var/run/proxy-19001.pid" > "%s/19001.out" 2>&1 < /dev/null &' % (
                codis_path, conf_dst_path, log_path, log_path), shell=True)
        subprocess.run(
            'nohup "%s/codis-proxy" "--config=%s/proxy-19002.toml" "--dashboard=18080" "--log=%s/19002.log" '
            '"--log-level=INFO" "--ncpu=4" "--pidfile=/var/run/proxy-19002.pid" > "%s/19002.out" 2>&1 < /dev/null &' % (
                codis_path, conf_dst_path, log_path, log_path), shell=True)
        time.sleep(1)
        print("纳管Proxy节点")
        subprocess.run('%s/codis-admin --dashboard=0.0.0.0:18080 --create-proxy -x 0.0.0.0:11080' % codis_path,
                       shell=True)
        subprocess.run('%s/codis-admin --dashboard=0.0.0.0:18080 --create-proxy -x 0.0.0.0:11081' % codis_path,
                       shell=True)
        subprocess.run('%s/codis-admin --dashboard=0.0.0.0:18080 --create-proxy -x 0.0.0.0:11082' % codis_path,
                       shell=True)
        time.sleep(1)
        print("创建分组")
        subprocess.run('%s/codis-admin --dashboard=0.0.0.0:18080 --create-group --gid=1' % codis_path, shell=True)
        subprocess.run('%s/codis-admin --dashboard=0.0.0.0:18080 --create-group --gid=2' % codis_path, shell=True)
        subprocess.run('%s/codis-admin --dashboard=0.0.0.0:18080 --create-group --gid=3' % codis_path, shell=True)
        time.sleep(1)
        print("添加redis-server至分组")
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --group-add --gid=1 --addr=0.0.0.0:9000' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --group-add --gid=1 --addr=0.0.0.0:9001' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --group-add --gid=2 --addr=0.0.0.0:9002' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --group-add --gid=2 --addr=0.0.0.0:9003' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --group-add --gid=3 --addr=0.0.0.0:9004' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --group-add --gid=3 --addr=0.0.0.0:9005' % codis_path,
            shell=True)
        time.sleep(1)
        print("形成主备关系")
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --promote-server --gid=1 --addr=0.0.0.0:9000' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --sync-action --create --addr=0.0.0.0:9001' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --promote-server --gid=2 --addr=0.0.0.0:9002' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --sync-action --create --addr=0.0.0.0:9003' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --promote-server --gid=3 --addr=0.0.0.0:9004' % codis_path,
            shell=True)
        subprocess.run(
            '%s/codis-admin --dashboard=0.0.0.0:18080 --sync-action --create --addr=0.0.0.0:9005' % codis_path,
            shell=True)
        time.sleep(1)
        print("平均分配slots")
        subprocess.run('%s/codis-admin --dashboard=0.0.0.0:18080 --rebalance --confirm' % codis_path, shell=True)
    print("启动完毕")


def stop_redis(redis_type):
    if redis_type not in ["single", "ha", "proxy", "cluster"]:
        print("请输入类型如下：single，ha，cluster，proxy")
        return

    if not exist_process(redis_type):
        print("%s is not running!" % redis_type)
        return

    ports = redis_ports[redis_type]
    if "proxy" == redis_type:
        ports.extend(proxy_ports)
        ports.extend(["9090", "18080"])
    for port in ports:
        subprocess.run("kill -9 $(netstat -tlpn | grep %s | awk  '{print $7}' | cut -d / -f 1)" % port, shell=True)
        print("stop port:%s" % port)


def prepare_conf(redis_type):
    if not os.path.exists(conf_dst_path):
        os.makedirs(conf_dst_path)
    if "single" == redis_type:
        copy_redis_conf(redis_type, "redis.conf")
        replace_redis_port(redis_type)
    elif "ha" == redis_type:
        copy_redis_conf(redis_type, "redis.conf")
        replace_redis_port(redis_type)
    elif "cluster" == redis_type:
        copy_redis_conf(redis_type, "redis.conf")
        replace_redis_port(redis_type)
        replace_redis_conf(redis_type, "# cluster-config-file", "cluster-config-file")
        replace_redis_conf(redis_type, "# cluster-enabled", "cluster-enabled")
        replace_redis_conf(redis_type, "# cluster-node-timeout", "cluster-node-timeout")
    elif "proxy" == redis_type:
        copy_redis_conf(redis_type, "redis-proxy.conf")
        replace_redis_port(redis_type)
        copy_proxy_conf()
        replace_proxy_port()


def exist_process(redis_type):
    port_list = {"single": "6379", "ha": "6380", "proxy": "9090", "cluster": "8000"}
    output = subprocess.check_output(
        "netstat -tlpn | grep %s | awk  '{print $7}' | cut -d / -f 1" % port_list[redis_type],
        stderr=subprocess.STDOUT, shell=True)
    if str(output, encoding='utf-8') == "":
        return False
    return True


def replace_redis_conf(redis_type, old, new):
    for port in redis_ports[redis_type]:
        file = "/opt/redis/conf/redis-%s-%s.conf" % (redis_type, port)
        replace_file(file, {old: new})


def replace_redis_port(redis_type):
    for port in redis_ports[redis_type]:
        file = "/opt/redis/conf/redis-%s-%s.conf" % (redis_type, port)
        replace_file(file, {"6379": port})


def copy_redis_conf(redis_type, redis_conf):
    for port in redis_ports[redis_type]:
        source_file = conf_src_path + "/" + redis_conf
        target_file = conf_dst_path + "/redis-%s-%s.conf" % (redis_type, port)
        shutil.copy(source_file, target_file)


def copy_proxy_conf():
    shutil.copy(conf_src_path + "/dashboard.toml",
                conf_dst_path + "/dashboard.toml")
    for port in proxy_ports:
        shutil.copy(conf_src_path + "/proxy.toml",
                    conf_dst_path + "/proxy-%s.toml" % port)


def replace_proxy_port():
    for i in range(0, 3):
        file = "/opt/redis/conf/proxy-%s.toml" % proxy_ports[i]
        content = {"11080": "1108" + str(i), "19000": proxy_ports[i]}
        replace_file(file, content)


def replace_file(file, content):
    f = open(file, mode='r')
    lines = f.read()
    f.close()
    f = open(file, mode='w')
    for key, val in content.items():
        lines = lines.replace(key, val)
    f.write(lines)
    f.flush()
    f.close()


def clean_data(redis_type):
    for port in redis_ports[redis_type]:
        path = data_path + "/" + port
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)


if __name__ == '__main__':
    Action().cmdloop()

