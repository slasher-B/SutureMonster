import src
from src import Util
'''
subdomain模块的oneforall自带服务器banner识别,hostsurvey同样也有banner识别功能;
在不使用subdomain模块的情况下可以启用signscan模块进行banner识别,
两个模块都启用则选择subdomain模块的banner识别功能;
默认情况下signscan模块请求的端口数量要比subdomain多很多;

工作流程:
subdomain ---> [websign] ---> allReports.db
live.txt ---> [url] ---> subdomain.tmp ---> SignScan
                                             |  |
          ------------------------------------  V
          |                              allReports.db
          V
==========txt==========
url1,ip,port1,websign1
url1,ip,port2,websign2
url2,ip,port1,websign1
...
=======================

@author B
'''
def hostSurvey():
    to = isping = proxy = ''
    output = Util.joinPath(src.path, 'reports', 'websign_report', 'SignScan_report.txt')
    tar_file = Util.joinPath(src.path, 'tmp', 'subdomain.tmp')
    if src.os.path.isfile(tar_file):
        src.os.remove(tar_file)
    with open(Util.joinPath(src.path, 'reports', 'live.txt'), 'r') as r:
        with open(tar_file, 'a') as w:
            for line in r.readlines():
                w.write(line.split('>>')[0].strip() + '\n')

    if src.OS == 'Windows':
        if src.hs_timeout:
            to = ' -t ' + src.hs_timeout
        if src.hs_ping:
            isping = ' -ping'
        if src.proxy_addr:
            proxy = ' -proxy ' + src.proxy_addr
        exe = './monster/HostScan/HostSurvey.exe -f {0} -m sign -o {1}{2}{3}{4}'\
            .format(tar_file, output, to, isping, proxy)
    else:
        exe = [Util.joinPath(src.path, 'monster', 'HostScan', 'HostSurvey'),
               '-f', tar_file, '-m', 'sign', '-o', output, isping]
        if src.hs_timeout:
            exe.append('-t')
            exe.append(src.hs_timeout)
        if src.proxy_addr:
            exe.append('-proxy')
            exe.append(src.proxy_addr)
    src.subprocess.Popen(exe,
                         shell=False,
                         stdout=None,
                         stderr=src.subprocess.STDOUT).wait()


def gatherSIGN():
    webSignDict = {}
    with open(Util.joinPath(src.path, 'reports', 'websign_report', 'SignScan_report.txt'), 'r') as r:
        signRes = r.readlines()
    s, c = Util.selectAllDB(tableName='hostscan')
    for webSign in signRes:
        webSignDict['port'] = webSign.split(',')[2]
        webSignDict['websign'] = webSign.split(',')[3]
        if len(list(s)) == 0:
            webSignDict['url'] = webSign.split(',')[0]
            webSignDict['ip'] = webSign.split(',')[1]
            Util.insertDB(tableName='hostscan', insert=webSignDict)
        else:
            for i in s:
                if i[0] == webSign.split(',')[1] or i[2] == webSign.split(',')[1]:
                    Util.updateDB(tableName='hostscan', updated=webSignDict,
                                  k='ip', v=webSign.split(',')[1])
    c.close()


def start(mods):
    if "subdomain" not in mods:
        print('[INFO]SignScan:开始进行web指纹扫描，结果输出在./reports/host_scan_report/')
        hostSurvey()
        gatherSIGN()
    else:
        print('[INFO]SignScan:检测到联动subdomain模块,web指纹扫描将使用OneForAll,结果输出在./reports/subdomain_report/')
        pass
    return
