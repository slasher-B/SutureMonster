import src
from src import Util
'''
整合工具: nmap + hostsurvey;
扫描IP/C段存活主机,然后联动nmap对存活目标进行端口扫描以及服务识别;

工作流程:
live_ip.tmp -------------[IP]
                          |
                          V
subdomain ---[C段]---> nmap.getAliveIP() ----------> [aliveIPList]
                                                          |
                                                          V
HostScan.outPut() <------- [alivePorts & sign] <--- HostScan.portScan()
        |    L_____________________                  nmap.portScan()
        V                          |
=============txt=============      ----> allReports.db
url,aliveIP1,openPort1,sign1
url,aliveIP2,openPort2,sign2
...
=============================

@author B
'''
def nmap(tar_file):
    toolName = 'nmap'
    if src.os.environ['PATH'].find('nmap') == -1:
        toolName = './monster/HostScan/nmap/nmap'
    # nmap -sS -Pn --open --min-hostgroup 4 --min-parallelism 1024 --host-timeout 30 -T4 -v -oG result.txt -iL ip.txt
    if src.OS == 'Windows':
        exe = '{0} -Pn -s{1} --open --min-hostgroup {2} --min-parallelism {3} --host-timeout -{4} -{5} -oG {6} -iL {7} -p {8}'\
            .format(toolName,
                    src.n_scan_flag,
                    src.n_hostgroup,
                    src.n_parallelism,
                    src.n_timeout,
                    src.n_seq,
                    Util.joinPath(src.path, 'reports', 'host_scan_report', 'nmap_result.txt'),
                    tar_file,
                    src.hs_port)
    else:
        exe = [toolName, '-Pn', '-s'+src.n_scan_flag, '--open', '--min-hostgroup', src.n_hostgroup,
               '--min-parallelism', src.n_parallelism, '--host-timeout', src.n_timeout, '-'+src.n_seq,
               '-oG', Util.joinPath(src.path, 'reports', 'host_scan_report', 'nmap_result.txt'),
               '-iL', tar_file, '-p', src.hs_port]
    src.subprocess.Popen(exe,
                         shell=False,
                         stdout=None,
                         stderr=src.subprocess.STDOUT).wait()


def hostsurvey(tar_file):
    to = isping = ports = proxy = ''
    if src.hs_timeout:
        to = ' -t ' + src.hs_timeout
    if src.hs_ping == 1:
        isping = ' -ping'
    if src.hs_port:
        ports = ' -p ' + src.hs_port
    if src.proxy_addr:
        proxy = ' -proxy ' + src.proxy_addr
    output = Util.joinPath(src.path, 'reports', 'host_scan_report', 'hostSurvey_result.txt')

    if src.OS == 'Windows':
        exe = './monster/HostScan/HostSurvey.exe  -f {0} -m port -o {1}{2}{3}{4}{5}'\
            .format(tar_file, output, to, isping, ports, proxy)
    else:
        exe = [Util.joinPath(src.path, 'monster', 'HostScan', 'HostSurvey'), '-f', tar_file, '-m', 'port', '-o', output, to, isping, ports, proxy]
    src.subprocess.Popen(exe,
                         shell=False,
                         stdout=None,
                         stderr=src.subprocess.STDOUT).wait()


def checkIP(f):
    toolName = 'nmap'
    if src.os.environ['PATH'].find('nmap') == -1:
        toolName = './monster/HostScan/nmap/nmap'
    out = Util.joinPath(src.path, 'reports', 'Host_scan_report', 'nmap_host_scan.txt')
    tmp = Util.joinPath(src.path, 'tmp', 'nmap_check_ip.tmp')

    if src.OS == 'Windows':
        exe = '{0} -Pn -sS -p 80 --open --min-hostgroup 4 --min-parallelism 1024 --host-timeout 30 -T4 -oG {1} -iL {2}'\
            .format(toolName, out, f)
    else:
        exe = [toolName, '-Pn', '-sS', '-p', '80', '--open', '--min-hostgroup', '4', '--min-parallelism', '1024',
               '--host-timeout', '30', '-T4', '-oG', out, '-iL', f]
    src.subprocess.Popen(exe,
                         shell=False,
                         stdout=None,
                         stderr=src.subprocess.STDOUT).wait()
    with open(out, 'r') as r:
        with open(tmp, 'a') as w:
            for line in r.readlines():
                if line.find('Status: Up') != -1:
                    w.write(line.split(' ')[1].strip() + '\n')
    return tmp


def gatherHost():
    hostDict = {}
    nmapRep = Util.joinPath(src.path, 'reports', 'host_scan_report', 'nmap_result.txt')
    hsRep = Util.joinPath(src.path, 'reports', 'host_scan_report', 'hostSurvey_result.txt')
    try:
        with open(nmapRep, 'r') as nmap:
            nmapList = nmap.readlines()
    except:
        print('[ERROR]HostScan:{} -> 打开出错.'.format(nmapRep))
    try:
        with open(hsRep, 'r') as hostsurvey:
            hsList = hostsurvey.readlines()
    except:
        print('[ERROR]HostScan:{} -> 打开出错.'.format(hsList))
        return
    for hs in hsList:         # url,ip,port,websign
        hs = hs.strip()
        if src.n_flag == 1:
            for n in nmapList:
                if n.find('Ports:') != -1:
                    if hs.split(',')[1] == n.split(' ')[1].strip():      # ip == ip
                        portList = n.split('Ports:')[1].strip().split(',')
                        for ps in portList:
                            if hs.split(',')[2] == ps.split('/')[0]:     # port == port
                                hostDict['url'] = hs.split(',')[0]       # url
                                hostDict['ip'] = hs.split(',')[1]        # ip
                                hostDict['port'] = ps.split('/')[0]      # port
                                hostDict['sign'] = ps.split('/')[4]      # sign
                                hostDict['websign'] = hs.split(',')[3]   # websign
                                hostDict['port'] = ps.split('/')[0]
                                hostDict['sign'] = ps.split('/')[4]
                                hostDict['fuzz'] = ''
                                Util.insertDB(tableName='hostscan', insert=hostDict)
        elif src.n_flag == 0:
            hostDict['url'] = hs.split(',')[0]   # url
            hostDict['ip'] = hs.split(',')[1]    # ip
            hostDict['port'] = hs.split(',')[2]  # port
            hostDict['sign'] = hs.split(',')[3]  # sign
            hostDict['websign'] = ''
            hostDict['fuzz'] = ''
            Util.insertDB(tableName='hostscan', insert=hostDict)


def start(mods):
    fname = Util.joinPath(src.path, 'tmp', 'live_ip.tmp')
    if src.os.path.isfile(fname):
        src.os.remove(fname)
    if "subdomain" in mods:
        print('[INFO]HostScan:检测到联动subdomain模块,将使用OneForAll的C段结果进行扫描,结果输出在./reports/host_scan_report/')
        cidr, c = Util.selectDB(rowName='cidr', tableName='suturemonster')
        with open(fname, 'a') as w:
            for i in cidr:
                w.write(str(i[0]).strip() + '\n')
        c.close()
    else:
        print('[INFO]HostScan:开始进行主机发现+端口扫描，结果输出在./reports/host_scan_report/')
        with open(Util.joinPath(src.path, 'reports', 'live.txt'), 'r') as r:
            lines = r.readlines()
        with open(fname, 'a') as w:
            for line in lines:
                w.write(line.split('>>')[1].strip() + '\n')
    if src.os.path.isfile(fname) and src.os.path.getsize(fname) == 0:
        print('[WARN]HostScan:未找到目标.')
        return

    while 1:
        if src.n_flag == 0:
            hostsurvey(fname)
            gatherHost()
            break
        elif src.n_flag == 1:
            if not src.os.path.isdir(Util.joinPath(src.path, 'monster', 'HostScan', 'nmap')) and \
                    src.os.environ['PATH'].find('nmap') == -1:
                print('[ERROR]HostScan:未检测到nmap,请将nmap放在monster目录下或加入环境变量.')
                print('[WARN]HostScan:仅使用HostSurvey进行扫描.')
                src.n_flag = 0
                continue
            ipfile = checkIP(fname)
            t = src.threading.Thread(target=hostsurvey, args=ipfile)
            t.start()
            nmap(ipfile)
            t.join()
            gatherHost()
            break
    return
