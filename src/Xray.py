import src
from src import Util
'''
整合xray,分为：
    1  passive    被动模式:监听端口，对经过此端口的流量进行扫描，可配合awvs、bp或者其他爬虫;
    2  initiative 主动模式:通过live.txt批量传入url在并发模式下进行主动扫描;

工作流程:
                 <--------------<
                |                |
initiative:subdomain.tmp ---> [target]    target-ymd_hms.html
                                  |            ^
                                  V            |
passive:Awvs ---> [crawled] ---> Xray ---> [vul scan] ---> vul_scan_report.html

@author B
'''
def passive(o):
    if src.OS == 'Windows':
        exe = './monster/Xray/xray webscan --listen {0}:{1} --html-output {2}'\
            .format(src.xray_proxy_addr, src.xray_proxy_port, o)
    else:
        exe = [Util.joinPath(src.path, 'monster', 'Xray', 'xray'),
               '--listen', src.xray_proxy_addr+':'+src.xray_proxy_port,
               '--html-output', o]
    src.subprocess.Popen(exe,
                         shell=False,  # 使用系统内建命令时=True
                         stdout=None,  # 命令输出重定向到父进程
                         stderr=src.subprocess.STDOUT).wait(20)  # 标准错误输出跟随stdout


def initiative(o, tf):
    with open(tf, 'r') as getTar:
        lines = getTar.readlines()
    with src.ThreadPoolExecutor(max_workers=5) as t:
        for u in lines:
            o = Util.joinPath(o, u + '-' + src.datetime.datetime.now().strftime('%F_%H:%M:%S.%f'))
            print('[INFO]Xray:开始扫描 -> {}'.format(u))
            if src.OS == 'Windows':
                e = './monster/Xray/xray webscan --url {0} --html-output {1}'.format(u, o)
            else:
                e = [Util.joinPath(src.path, 'monster', 'Xray', 'xray'), 'webscan', '--url', u, '--html-output', o]
            t.submit(lambda exe: src.subprocess.Popen(
                exe,
                shell=False,
                close_fds=True,
                stdout=src.subprocess.PIPE,
                stderr=src.subprocess.STDOUT).wait()
                     , e)
            src.time.sleep(0.01)


def start(mods):
    if not src.os.path.isfile(Util.joinPath(src.path, 'monster', 'Xray', 'xray')) and \
            not src.os.path.isfile(Util.joinPath(src.path, 'monster', 'Xray', 'xray.exe')):
        print('[ERROR]Xray:找不到xray,或者没有执行权限.')
        return
    if not src.os.path.isdir(src.xray_path):
        src.xray_path = Util.joinPath(src.path, 'reports', 'vul_scan_report')
        print('[WARN]Xray:指定目录不存在,结果将导出到默认路径!!!')
    tar_file = Util.joinPath(src.path, 'tmp', 'subdomain.tmp')

    defaultRep = Util.joinPath(src.path, 'reports', 'vul_scan_report', 'Xray_PassiveScan_report.html')
    if src.xray_model == 1:
        if src.os.path.isfile(tar_file):
            src.os.remove(tar_file)
        if 'subdomain' in mods:
            while 1:
                src.time.sleep(5)
                s, c = Util.selectDB(rowName='url', tableName='suturemonster')
                if len(list(s)) != 0:
                    c.close()
                    break
                c.close()
            s, c = Util.selectDB(rowName='url', tableName='suturemonster')
            with open(tar_file, 'a') as w:
                for ul in s:
                    w.write(str(ul[0]).strip() + '\n')
            c.close()
        else:
            with open(Util.joinPath(src.path, 'reports', 'live.txt'), 'r') as r:
                with open(tar_file, 'a') as w:
                    for u in r.readlines():
                        w.write(u.split('>>')[0].strip() + '\n')
        initiative(src.xray_path, tar_file)
    else:
        if src.os.path.isfile(defaultRep):
            print('[ERROR]Xray:请先删除或重命名原报告 -> {}'.format(defaultRep))
            return
        passive(defaultRep)
    src.sys.exit(1)
