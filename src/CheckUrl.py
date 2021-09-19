import src
from src import Util
'''
检查目标是否能够访问
@author B
'''
# 将有效的url和解析成ip的域名写入文件
def writeTo(fname, ulist):
    if fname == 'live.txt':
        tmp = []
        with open(Util.joinPath(src.path, 'reports', 'live.txt'), 'a') as f:
            for u in list(set(ulist)):
                host = str(u).split("://")[1].strip('/')
                if not src.re.match(
                        '^(?:(?:1[0-9][0-9]\.)|(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.)){3}(?:(?:1[0-9][0-9])|(?:2[0-4][0-9])|(?:25[0-5])|(?:[1-9][0-9])|(?:[0-9]))$',
                        host):
                    host = src.socket.gethostbyname(host)
                f.write(u + '>>' + host + '\n')
                tmp.append(u + '>>' + host)
        # 重新写入文件
        with open(Util.joinPath(src.path, 'reports', 'live.txt'), 'w+') as rewrite:
            for read in rewrite.readlines():
                tmp.append(read)
            for w in list(set(tmp)):
                rewrite.write(w + '\n')
    elif fname == 'dead.txt':
        tmp = []
        with open(Util.joinPath(src.path, 'reports', 'dead.txt'), 'a') as f:
            for u in list(set(ulist)):
                f.write(u + '\n')
                tmp.append(u)
        # 重新写入文件
        with open(Util.joinPath(src.path, 'reports', 'dead.txt'), 'w+') as rewrite:
            for read in rewrite.readlines():
                tmp.append(read)
            for w in list(set(tmp)):
                rewrite.write(w + '\n')


# 检查可访问的url
def checkLive(url):
    url = str(url).strip()
    http = url
    if not url.startswith('http'):
        http = 'http://' + url
    with open(Util.joinPath(src.path, 'dictionary', 'user-agents.dict'), 'r') as ua:
        UA = ua.readlines()
    headers = {
        'User-Agent': UA[src.random.randint(1, len(UA))].strip(),
    }
    s = src.requests.session()
    s.keep_alive = False
    try:
        resp = s.get(url=http, headers=headers, timeout=(2, 3), verify=False)
        if str(resp.status_code).startswith('2'):
            return True, http
        else:
            if url.startswith('http'):
                https = url.replace('http', 'https')
            else:
                https = 'https://' + url
            print('[INFO]转换为https -> ' + url)
            try:
                r = src.requests.get(url=https, headers=headers, timeout=(3, 5), verify=False)
                if str(r.status_code).startswith('2'):
                    return True, https
                else:
                    return False, url + '>>' + str(r.status_code)
            except Exception as er:
                print('[ERROR]https请求出错 -> {0}\n  {1}'.format(https, er))
                return False, url + '>>with ERROR'
    except Exception as e:
        print('[ERROR]http请求出错 -> {0}\n  {1}'.format(http, e))
        return False, url + '>>with ERROR'
