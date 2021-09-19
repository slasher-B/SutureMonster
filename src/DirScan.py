import src
from src import Util
'''
整合DirSearch,用于目录扫描
执行逻辑:
1.协同模块subdomain:
    使用subdomain模块的结果作为目标进行扫描;
2.不协同subdomain/单独运行dirsearch:
    检查是否存在live.txt并且文件里有内容,存在则开始扫描目录,不存在则退出进程;

工作流程:
live.txt ---> [urls] ---> dirSearch() ---> [folders]
                ^                              |
                |                              V
             subdomain                   allReports.db 

@author: B
'''
def dirSearch(mods):
    tarFile = Util.joinPath(src.path, 'tmp', 'subdomain.tmp')
    if src.os.path.isfile(tarFile):
        src.os.remove(tarFile)
    if "subdomain" in mods:
        print('[INFO]DirSearch:协同模式,将使用subdomain模块生成的结果...')
        subdomain, c = Util.selectDB(rowName='url', tableName='suturemonster')
        with open(tarFile, 'a') as w:
            for row in subdomain:
                w.write(str(row[0]).strip() + '\n')
        c.close()
    else:
        print('[INFO]DirSearch:独立模式,准备运行dirsearch...')
        with open(Util.joinPath(src.path, 'reports', 'live.txt'), 'r') as r:
            with open(tarFile, 'a') as w:
                for u in r:
                    w.write(u.split('>>')[0].strip() + '\n')
    if src.os.path.isfile(tarFile) and src.os.path.getsize(tarFile) == 0:
        print('[WARN]DirScan:未找到目标,进程即将退出.')
        src.sys.exit(1)
    src.dirsearch.Program(tar_file=tarFile,
                          proxy=src.proxy_addr,
                          extensions=src.ds_extensions,
                          threads=int(src.ds_threads),
                          status_code=src.ds_exclude_status_code,
                          regex=src.ds_exclude_regex,
                          output_file=Util.joinPath(src.path, 'reports', 'dir_scan_report', 'batch.txt'))


def gatherDIR():
    db = {}
    ulist = []
    if not src.os.path.isfile(Util.joinPath(src.path, 'reports', 'dir_scan_report', 'batch.txt')):
        print('[WARN]DirScan:未扫描到存活目录,进程即将退出.')
        src.sys.exit(1)
    with open(Util.joinPath(src.path, 'reports', 'dir_scan_report', 'batch.txt'), 'r') as read_dir:
        ds_data = read_dir.readlines()
    r, c = Util.selectAllDB('suturemonster')
    r = len(list(r))
    c.close()
    for data in ds_data:
        if data.startswith('2'):
            res = data.split('B ')[1].strip()  # http://url.com:port/folder
            protocol = res.split('://')[0]
            domain = res.split('://')[1].split('/')[0]
            if domain.split(':')[1] == '80' or '443':
                domain = domain.split(':')[0]
            ulist.append((protocol + '://' + domain).strip())
    for url in list(set(ulist)):
        db['folders'] = ''
        tmp = []
        for da in ds_data:
            if da.startswith('2'):
                res = da.split('B ')[1].strip()  # http://url.com:port/folder
                protocol = res.split('://')[0]
                domain = res.split('://')[1].split('/')[0]
                wport = domain.split(':')[1].strip()
                if domain.split(':')[1] == '80' or '443':
                    domain = domain.split(':')[0]
                if url == (protocol + '://' + domain).strip():
                     tmp.append(res.split('://')[1].split('/')[1].strip() + ',' + wport)  # folders,web_port -> tmp
        for t in list(set(tmp)):
            db['web_port'] = t.split(',')[1]
            db['folders'] += '/' + t.split(',')[0] + '\n'  # tmp -> db
        if r != 0:
            Util.updateDB(tableName='suturemonster', updated=db, k='url', v=url)
        else:
            db['subdomain'] = db['ip'] = db['title'] = db['sign'] = db['cidr'] = db['address'] = db['isp'] = ''
            db['url'] = url
            db['status'] = '200'
            Util.insertDB('suturemonster', insert=db)


def start(mods):
    resPath = Util.joinPath(src.path, 'reports', 'dir_scan_report', 'batch.txt')
    if src.os.path.isfile(resPath):
        src.os.remove(resPath)
    dirSearch(mods=mods)
    gatherDIR()
    return
