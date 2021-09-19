from src import Util, CheckUrl, SubDomain, DirScan, HostScan, SignScan, Xray, Awvs, PortFuzz
import src
'''
这是一个整合了多个工具的一个自动化信息收集工具,简称缝合怪;
本工具可用于收集子域名,扫描服务器目录,解析ip并扫描C段以及端口,联动xray+awvs进行漏洞扫描,整合hydra进行弱口令爆破;
在使用前设置好配置文件,就可以开始信息收集和完成初阶段的入侵了;
推荐模式：
1.-m subdomain dirscan hostscan signscan xray awvs hydra(默认,即不指定-m参数)
2.-m subdomain dirscan
3.-m xray awvs
4.-m hostscan signscan hydra
@author B
'''
def run(args, mlen):
    liveList = []
    deadList = []
    f = args.file
    m = args.mod
    o = args.out
    u = args.url
    target = ''
    # -m参数检查
    if len(m) > mlen:
        parser.error(parser.format_help())
        parser.exit(2)
    for i in m:
        if i not in mods:
            parser.error(parser.format_help())
            parser.exit(2)
    # -o参数检查
    if not o:
        o = Util.joinPath(src.path, 'reports', 'all_results-'+src.time.strftime("%y-%m-%d_%H-%M-%S")+'.xls')
    elif str(o).find('.xls') == -1:
        o = o + '.xls'
    else:
        father = src.os.path.abspath(src.os.path.dirname(o) + src.os.path.sep + '.')
        if src.os.path.isdir(father) is False:
            print("'{}' 目录不存在/无权限访问\n".format(o))
            parser.error(parser.format_help())
            parser.exit(2)
    # -f、-u参数检查
    if not f and not u:
        parser.error(parser.format_help())
    elif f:
        if f is None or not src.os.path.isfile(f):
            print("'{}' 不存在/无权限访问\n".format(f))
            parser.error(parser.format_help())
            parser.exit(2)
        target = f

    elif u:
        if not src.re.match(
                '^(?=^.{3,255}$)(https?://)[a-zA-Z\d][-a-zA-Z\d]{0,62}(\.[a-zA-Z\d][-a-zA-Z\d]{0,62})+$|^(?=^.{3,255}$)[a-zA-Z\d][-a-zA-Z\d]{0,62}(\.[a-zA-Z\d][-a-zA-Z\d]{0,62})+$',
                u):
            print("'{}' 格式错误,例：example.com OR http(s)://example.com\n".format(u))
            parser.error(parser.format_help())
            parser.exit(2)
        target = u
    print('[INFO]正在检查目标有效性...')
    if src.os.path.isfile(target):
        with open(target, 'r') as tar_file:
            tar_urls = tar_file.readlines()
        t_worker = 1
        if 2 < len(tar_urls) <= 10:       t_worker = 2
        elif 10 < len(tar_urls) <= 50:    t_worker = 5
        elif 50 < len(tar_urls) <= 500:   t_worker = 10
        elif 500 < len(tar_urls) <= 1000: t_worker = 50
        elif 1000 < len(tar_urls):        t_worker = 70
        with src.ThreadPoolExecutor(max_workers=t_worker) as t:
            for url in tar_urls:
                if not url.startswith('#'):  # 跳过注释行
                    url = url.strip()
                    r = t.submit(CheckUrl.checkLive, url)
                    flag, res = r.result()
                    if flag is True:
                        liveList.append(res)
                    elif flag is False:
                        deadList.append(res)
    else:
        flag, res = CheckUrl.checkLive(target)
        if flag is True:
            liveList.append(res)
        elif flag is False:
            deadList.append(res)
    if not liveList:
        print('[WARN]未发现存活目标,程序即将退出...')
        parser.exit(1)
    if deadList: src.CheckUrl.writeTo('dead.txt', deadList)
    src.CheckUrl.writeTo('live.txt', liveList)

    print("[INFO]目标已写入文件,启动模块...")
    # tmp=临时工作目录
    if src.os.path.exists(Util.joinPath(src.path, 'tmp')):
        src.shutil.rmtree(Util.joinPath(src.path, 'tmp'))
    if src.os.path.exists(Util.joinPath(src.path, 'reports', 'allReports.db')):
        src.os.remove(Util.joinPath(src.path, 'reports', 'allReports.db'))
    src.os.mkdir('tmp')
    Util.createDB()
    modules = [mod.lower() for mod in m]
    if "subdomain" not in modules:
        Util.setTmpFromLive('subdomain')  # set subdomain.tmp
        if "hostscan" in modules:
            Util.setTmpFromLive('live_ip')  # set live_ip.tmp

    # p.submit(SubDomain.start()) = 串行
    # p.submit(SubDomain.start) = 并行
    with src.ProcessPoolExecutor(max_workers=3) as p:
        if 'subdomain' in modules:
            # 启动subdomain模块
            p.submit(SubDomain.start())
        if 'dirscan' in modules:
            # 启动dirscan模块
            p.submit(DirScan.start(modules))
        if 'hostscan' in modules:
            # 启动hostscan模块
            p.submit(HostScan.start, modules)
        if 'signscan' in modules:
            # 启动signscan模块
            p.submit(SignScan.start, modules)
        if 'xray' in modules:
            # 启动xray模块
            p.submit(Xray.start)
        if 'awvs' in modules:
            # 启动awvs模块
            p.submit(Awvs.run, modules)
        if 'hydra' in modules:
            # 启动hydra模块
            p.submit(PortFuzz.start)
    print('[INFO]处理结果中,报告输出路径 -> {}'.format(o))
    Util.db2xls(opath=o)
    if src.os.path.isdir(Util.joinPath(src.path, 'tmp')):
        src.shutil.rmtree(Util.joinPath(src.path, 'tmp'))
    print('[INFO]所有任务完成.')


'''
主程序入口
'''
if __name__ == '__main__':
    banner = f"""
   _____       _                  __  __                 _
  / ____|     | |                |  \/  |               | |
 | (___  _   _| |_ _   _ _ __ ___| \  / | ___  _ __  ___| |_ ___ _ __
  \___ \| | | | __| | | | '__/ _ \ |\/| |/ _ \| '_ \/ __| __/ _ \ '__|
  ____) | |_| | |_| |_| | | |  __/ |  | | (_) | | | \__ \ ||  __/ |
 |_____/ \__,_|\__|\__,_|_|  \___|_|  |_|\___/|_| |_|___/\__\___|_|
                                                                (v1.0)
                                                          Author:__B__
-----------------------------------------------------------------------
    """
    print(banner)
    mods = ['subdomain', 'dirscan', 'hostscan', 'signscan', 'awvs', 'xray', 'hydra']
    parser = src.argparse.ArgumentParser('sm', add_help=False, usage='sm -h [-u http://example.com [-f targe.txt]] [-o result.html] [-m ...option]')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f', '--file', metavar='', type=str, help='输入文件名/绝对路径')
    parser.add_argument('-h', '--help', action='help', help='显示帮助信息')
    parser.add_argument('-m', '--mod', metavar='...modules', type=str,
                        nargs=src.argparse.REMAINDER,
                        default=mods,
                        help='选择模块,可以任意组合,可选项：'
                             '1.subdomain;'
                             '2.dirscan;'
                             '3.hostscan;'
                             '4.signscan;'
                             '5.awvs;'
                             '6.xray;'
                             '7.hydra;')
    parser.add_argument('-o', '--out', metavar='', type=str, help='指定输出综合结果的路径')
    group.add_argument('-u', '--url', metavar='', type=str, help='输入单个域名/网址')
    run(parser.parse_args(), len(mods))
