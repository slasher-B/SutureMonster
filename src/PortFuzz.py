import src
from src import Util
'''
使用hydra对一些登录入口进行弱口令爆破;
工作流程:
host_scan_report/p1,p2... ---> [ipList]
                                  |
                                  V
       ----- [Fuzz result] <--- hydra()
      |               |
      V               V
=======txt=======    allReports.db
user:xxx pwd:xxx
=================

@author B
'''
def hydra():
    for p in src.hs_port.split(','):
        if p.find('-') != -1:
            tmp = p.split('-')
            '''
            爆破参数配置,web端多数需要验证码,有生之年编写验证码绕过模块后解锁.
            配置里的端口参数如果是范围:    "0-100", 对应的参数配置为po;
            配置里的端口参数如果是单个端口: "100",   对应的参数配置为p;
            '''
            for po in range(int(tmp[0]), int(tmp[1]) + 1):
                if po == 21:port = 21; protocol = 'ftp://'  # ftp
                elif po == 22:port = 22; protocol = 'ssh://'  # ssh
                elif po == 23:port = 23; protocol = 'telnet://'  # telnet
                # elif po == 80:port = 80       # web manager
                # elif po == 81:port = 81
                # elif po == 82:port = 82
                # elif po == 83:port = 83
                # elif po == 84:port = 84
                # elif po == 85:port = 85
                # elif po == 86:port = 86
                # elif po == 87:port = 87
                # elif po == 88:port = 88
                # elif po == 89:port = 89
                elif po == 512:port = 512; protocol = 'rexec://'  # linux rexec
                elif po == 513:port = 513; protocol = 'rexec://'
                elif po == 514:port = 514; protocol = 'rexec://'
                elif po == 5900:port = 5900; protocol = 'vnc://'  # VNC
                elif po == 5901:port = 5901; protocol = 'vnc://'
                elif po == 5902:port = 5902; protocol = 'vnc://'
                # elif po == 8080:port = 8080  # Java-web manager
                # elif po == 8081:port = 8081
                # elif po == 8082:port = 8082
                # elif po == 8083:port = 8083
                # elif po == 8084:port = 8084
                # elif po == 8085:port = 8085
                # elif po == 8086:port = 8086
                # elif po == 8087:port = 8087
                # elif po == 8088:port = 8088
                # elif po == 8089:port = 8089
                else: continue
                hydraRun(port, protocol)
        else:
            p = int(p)
            if p == 25:port = 25; protocol = 'smtp://'  # smtp
            # elif p == 69:port = 69  # tftp
            elif p == 110:port = 110; protocol = 'pop3://'  # pop3
            elif p == 139:port = 139; protocol = 'smb://'  # smb
            elif p == 143:port = 143; protocol = 'imap://'  # imap
            elif p == 389:port = 389; protocol = 'ldap://'  # ldap
            elif p == 445:port = 445; protocol = 'smb://'  # smb
            # elif p == 1194:port = 1194  # open vpn
            # elif p == 1352:port = 1352  # lotus
            elif p == 1433:port = 1433; protocol = 'mssql://'  # sql-server
            # elif p == 1500:port = 1500  # ISPmanager
            # elif p == 1521:port = 1521; protocol = 'oracle-sid://'  # oracle  oracle-listener://
            # elif p == 1723:port = 1723  # pptp
            # elif p == 2082:port = 2082  # cPanel
            # elif p == 2082:port = 2082
            # elif p == 3128:port = 3128  # Squid
            elif p == 3306:port = 3306; protocol = 'mysql://'  # mysql
            # elif p == 3311:port = 3311  # kangle
            # elif p == 3312:port = 3312
            elif p == 3389:port = 3389; protocol = 'rdp://'  # windows rdp
            # elif p == 4848:port = 4848  # GlassFish
            # elif p == 5000:port = 5000  # DB2
            elif p == 5432:port = 5432; protocol = 'postgres://'  # Postgresql
            elif p == 6379:port = 6379; protocol = 'redis://'  # Redis
            # elif p == 7001:port = 7001  # webLogic
            # elif p == 7002:port = 7002
            # elif p == 7778:port = 7778  # Kloxo
            # elif p == 8000:port = 8000  # Ajenti
            # elif p == 8443:port = 8443  # Plesk
            # elif p == 9080:port = 9080  # WebSphere
            # elif p == 9081:port = 9081
            # elif p == 9090:port = 9090
            # elif p == 27017:port = 27017  # MongoDB
            # elif p == 27018:port = 27018
            else:continue
            hydraRun(port, protocol)


def hydraRun(port, protocol):
    tar_file = Util.joinPath(src.path, 'reports', 'host_scan_report', str(port))
    out = Util.joinPath(src.path, 'reports', 'port_fuzz_report', 'hydra.log')
    if src.os.path.isfile(out):
        src.os.remove(out)
    if src.os.path.isfile(tar_file):
        with open(tar_file, 'r') as t:
            for ip in t.readlines():
                if src.OS == 'Windows':
                    if src.hy_flag == 1:
                        dict_file = ' -C ' + src.hy_dictName
                    elif src.hy_flag == 0:
                        dict_file = ' -L ' + src.hy_userDictPath + \
                                    ' -P ' + src.hy_passDictPath
                    exe = './monster/thc-hydra/hydra -f -e ns -t {0} -s {1} -o {2} {3} {4}'\
                        .format(src.hy_thread, str(port), out, dict_file, protocol + ip)
                else:
                    exe = [Util.joinPath(src.path, 'monster', 'thc-hydra', 'hydra'), '-f', '-e', 'ns',
                           '-t', src.hy_thread,
                           '-s', str(port),
                           '-o', out]
                    if src.hy_flag == 1:
                        exe.extend(['-C', src.hy_dictName, protocol + ip])
                    elif src.hy_flag == 0:
                        exe.extend(['-L', src.hy_userDictPath, '-P', src.hy_passDictPath, protocol + ip])
                src.subprocess.Popen(exe,
                                     stdout=None,
                                     stderr=src.subprocess.STDOUT,
                                     shell=False).wait()
    if src.os.path.isfile(out):
        with open(out, 'r') as log:
            while 1:
                line = log.readline()
                if not line:break
                elif line.startswith('['):
                    print('[INFO]Hydra: {}'.format(line))
                    with open(Util.joinPath(src.path, 'reports', 'port_fuzz_report', 'hydra_report.txt'), 'a') as w:
                        w.write(line)


def gatherFUZZ():
    fuzzDict = {}
    resPath = Util.joinPath(src.path, 'reports', 'port_fuzz_report', 'hydra_report.txt')
    if src.os.path.isfile(resPath):
        s, c = Util.selectAllDB('hostscan')
        l = len(list(s))
        c.close()
        with open(resPath, 'r') as r:
            fuzzRes = r.readlines()
        for fuzz in fuzzRes:
            resList = fuzz.strip().split(' ')
            ip = resList[2]
            port = resList[0].split('][')[0].strip('[')
            fuzzDict['port'] = port
            fuzzDict['sign'] = resList[0].split('][')[1].strip(']')
            fuzzDict['fuzz'] = resList[5] + resList[6] + ' ' + resList[9] + resList[10]
            if l == 0:
                fuzzDict['url'] = ''
                fuzzDict['ip'] = ip
                fuzzDict['websign'] = ''
                Util.insertDB(tableName='hostscan', insert=fuzzDict)
            else:
                hostRes, cs = Util.selectDB('ip', 'hostscan')  # 单个where子句的权宜之计
                host_res = list(hostRes)
                cs.close()
                for host in host_res:
                    if host[0] == ip:
                        Util.updateDB(tableName='hostscan', updated=fuzzDict, k='port', v=port)
    else:
        print('[WARN]Hydra:没有爆破成功的目标,进程即将退出.')


def start():
    print('[INFO]Hydra:后台开始进行端口爆破，结果输出在./reports/port_fuzz_report/')
    try:
        hydra()
        gatherFUZZ()
    except Exception as e:
        print('[ERROR]Hydra:进程出错,即将退出 ->\n{}'.format(e))
    return
