import src
from src import Util
"""
Awvs批量扫描脚本,可在配置文件设置扫描模式;
工作流程:
subdomain.tmp ---> [targets] ---> (target)
                       ^             |
                       L_____________|
                                     V
        Xray <--- [crawled] <--- AWVS(add target)
          |                          |
          V                          V
      [vul scan]                 [vul scan]
          |                          |
          V                          V
xray_vul_scan_report.html     Awvs_reports are on web side

@author B
"""
src.urllib3.disable_warnings(src.InsecureRequestWarning)
headers = {'Content-Type': 'application/json', "X-Auth": src.apikey}
with open(Util.joinPath(src.path, 'dictionary', 'user-agents.dict'), 'r') as ua:
    UA = ua.readlines()
# 添加扫描任务
def addTask(target):
    try:
        url = ''.join((src.awvs_url, '/api/v1/targets/add'))
        data = {"targets": [{"address": target, "description": ""}], "groups": []}
        r = src.requests.post(url, headers=headers, data=src.json.dumps(data), timeout=30, verify=False)
        result = src.json.loads(r.content.decode())
        return result['targets'][0]['target_id']
    except Exception as e:
        return e


# 删除全部扫描任务
def delTask():
    while 1:
        quer = '/api/v1/targets'
        try:
            r = src.requests.get(src.awvs_url + quer, headers=headers, timeout=30, verify=False)
            result = src.json.loads(r.content.decode())
            if int(result['pagination']['count']) == 0:
                print('[INFO]AWVS:已删除全部扫描目标。')
                return 0
            for targetsid in range(len(result['targets'])):
                targets_id = result['targets'][targetsid]['target_id']
                targets_address = result['targets'][targetsid]['address']
                try:
                    src.requests.delete(src.awvs_url + '/api/v1/targets/' + targets_id,
                                        headers=headers,
                                        timeout=30,
                                        verify=False)
                except Exception as e:
                    print('[ERROR]{0} -> {1}'.format(targets_address, e))
        except Exception as e:
            print('[ERROR]{0}{1} -> {2}'.format(src.awvs_url, quer, e))


# Awvs爬虫
def scan(target, profile_id):
    scanUrl = ''.join((src.awvs_url, '/api/v1/scans'))
    target_id = addTask(target)
    if target_id:
        data = {"target_id": target_id, "profile_id": profile_id, "incremental": False,
                "schedule": {"disable": False, "start_date": None, "time_sensitive": False}}
        try:
            configuration(target_id)
            response = src.requests.post(scanUrl, data=src.json.dumps(data), headers=headers, timeout=30, verify=False)
            result = src.json.loads(response.content)
            return result['target_id']
        except Exception as e:
            print('[ERROR] AWVS爬取出错 -> {}'.format(e))


# 基本配置
def configuration(target_id):
    proxy = False
    if src.awvs_proxy == "1": proxy = True
    configuration_url = ''.join((src.awvs_url, '/api/v1/targets/{}/configuration'.format(target_id)))
    data = {"scan_speed": src.scan_speed, "login": {"kind": "none"}, "ssh_credentials": {"kind": "none"}, "sensor": False,
            "user_agent": UA[src.random.randint(1, len(UA))].strip(), "case_sensitive": "auto",
            "limit_crawler_scope": True, "excluded_paths": [], "authentication": {"enabled": False},
            "proxy": {"enabled": proxy, "protocol": "http", "address": src.awvs_proxy_addr, "port": src.awvs_proxy_port},
            "technologies": [], "custom_headers": [], "custom_cookies": [], "debug": False,
            "client_certificate_password": "", "issue_tracker_id": "", "excluded_hours_id": ""}
    src.requests.patch(url=configuration_url, data=src.json.dumps(data), headers=headers, timeout=30, verify=False)


# 暂不支持自定义报告路径,需要手动登录web端下载
def run(mods):
    src.time.sleep(5)  # 等待xray启动
    tarFile = Util.joinPath(src.path, 'tmp', 'subdomain.tmp')
    if "subdomain" in mods:
        print('[INFO]AWVS:协同模式,将使用subdomain模块的结果作为目标.')
        while 1:
            src.time.sleep(5)
            s, c = Util.selectDB(rowName='url', tableName='suturemonster')
            if len(list(s)) != 0:
                c.close()
                break
            c.close()
        s, c = Util.selectDB(rowName='url', tableName='suturemonster')
        with open(tarFile, 'a') as w:
            for ul in s:
                w.write(str(ul[0]).strip() + '\n')
        c.close()
    else:
        print('[INFO]AWVS:独立模式,进程开始执行...')
        with open(Util.joinPath(src.path, 'reports', 'live.txt'), 'r') as r:
            with open(tarFile, 'a') as w:
                for line in r.readlines():
                    w.write(line.split('>>')[0].strip() + '\n')
    profile_id = "11111111-1111-1111-1111-1111111111" + src.awvs_model
    with open(tarFile, 'r', encoding='utf-8') as f:
        for target in f.readlines():
            if scan(target.strip(), profile_id):
                print("[INFO]AWVS:目标 -> {} 添加成功".format(target.strip()))
    print('[INFO]目标全部导入,等待xray扫描完成...')
    delTask()
    return
