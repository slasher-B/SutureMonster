import src
import monster.JSFinder
from monster.OneForAll.oneforall import OneForAll
from src import CheckUrl, Util

'''
整合oneforall+jsfinder协同爆破子域名,
工作流程:
JSFinder <-------
   |            ^
   V            |
live.txt ---> [urls] ---> OneForAll ---> [reports into db]

@author B
'''
def oneforall():
    s = OneForAll(targets=Util.joinPath(src.path, 'tmp', 'subdomain.tmp'),
                  port=src.ofa_port,
                  alive=src.ofa_alive,
                  req=True,
                  path=src.ofa_path,
                  takeover=False)
    s.run()


def jsFinder(url=None, file=None, cookie=""):
    jsf = monster.JSFinder.JSFinder(url=url, file=file, cookie=cookie)
    jsf.run()


def gather(resPath):
    db = {}
    for dicts in Util.readFromCSV(resPath):
        if dicts.get('status').startswith('4') or \
                dicts.get('reason').find('Not Found') != -1 or \
                dicts.get('reason').find('Error') != -1:
            continue
        db['url'] = dicts['url']
        db['subdomain'] = dicts['subdomain']
        db['ip'] = dicts['ip']
        db['web_port'] = dicts['port']
        db['status'] = dicts['status']
        db['title'] = dicts['title']
        db['sign'] = dicts['banner']
        db['cidr'] = dicts['cidr']
        db['address'] = dicts['addr']
        db['isp'] = dicts['isp']
        db['folders'] = ''
        Util.insertDB('suturemonster', db)
        db.clear()


def start():
    if src.ofa_flag == 1:
        tmp = []
        wtmp = []
        cookie = ""
        upath = Util.joinPath(src.path, 'reports', 'live.txt')
        if src.jf_cookie: cookie = src.jf_cookie
        jsFinder(file=upath, cookie=cookie)
        fpath = Util.joinPath(src.path, 'reports', 'subdomain_report', 'JSFinder_report.txt')
        try:
            with open(fpath, 'r') as r:
                for jsRes in r.readlines():
                    flag, u = CheckUrl.checkLive(jsRes)
                    if not flag: continue
                    tmp.append(u.strip())
            with open(upath, 'r') as rl:
                for alive in rl.readlines():
                    tmp.append(alive.split('>>')[0].strip())
            tmp = list(set(tmp))
            src.os.remove(upath)
            CheckUrl.writeTo('live.txt', tmp)
            with open(upath, 'r') as r:
                with open(Util.joinPath(src.path, 'tmp', 'subdomain.tmp'), 'a') as w:
                    for line in r:
                        w.write(line.split('>>')[0].strip() + '\n')
        except:
            print('[ERROR]SubDomain:' + fpath + '文件打开出错!!!')
        oneforall()
    else:
        oneforall()
    resPath = Util.joinPath(src.path, 'all_subdomain_result.csv')
    if src.os.path.isfile(resPath):
        gather(resPath)
    return
