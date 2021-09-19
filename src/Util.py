import src
'''
结果汇总,使用sqlite;
id integer primary key:插入null实现自增主键id,一个参数都不能换;
@author B
'''
def createDB():
    conn = src.sqlite3.connect(joinPath(src.path, 'reports', 'allReports.db'))
    c = conn.cursor()
    sql1 = '''
    create table suturemonster
    (id integer primary key,
    url varchar(50),
    subdomain varchar(50),
    ip varchar(20),
    web_port varchar(10),
    status varchar(10),
    title varchar(100),
    sign varchar(100),
    cidr varchar(20),
    address varchar(100),
    isp varchar(20),
    folders varchar(255)
    );
    '''
    sql2 = '''
    create table hostscan
    (id integer primary key,
    url varchar(100),
    ip varchar(20),
    port varchar(20),
    sign varchar(100),
    websign varchar(100),
    fuzz varchar(100)
    );
    '''
    c.execute(sql1)
    c.execute(sql2)
    conn.commit()
    conn.close()


def insertDB(tableName, insert=None):
    if insert is None:
        insert = {}
    conn = src.sqlite3.connect(joinPath(src.path, 'reports', 'allReports.db'))
    c = conn.cursor()
    if tableName == 'suturemonster':
        sql = 'insert into suturemonster ' \
              '(id, url, subdomain, ip, web_port, status, title, sign, cidr, address, isp, folders) ' \
              'values ({0},"{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}");' \
            .format("null", insert['url'], insert['subdomain'], insert['ip'], insert['web_port'], insert['status'],
                    insert['title'], insert['sign'], insert['cidr'], insert['address'], insert['isp'], insert['folders'])
    elif tableName == 'hostscan':
        sql = 'insert into hostscan ' \
              '(id, url, ip, port, sign, websign, fuzz) ' \
              'values ({0},"{1}","{2}","{3}","{4}","{5}","{6}");'\
            .format("null", insert['url'], insert['ip'], insert['port'], insert['sign'], insert['websign'], insert['fuzz'])
    else:
        return False
    c.execute(sql)
    conn.commit()
    conn.close()


def removeDB(tableName):
    conn = src.sqlite3.connect(joinPath(src.path, 'reports', 'allReports.db'))
    c = conn.cursor()
    sql = 'drop table main.{};'.format(tableName)
    c.execute(sql)
    conn.commit()
    conn.close()


def updateDB(tableName, updated=None, k='1', v='1'):
    if updated is None:
        updated = {}
    conn = src.sqlite3.connect(joinPath(src.path, 'reports', 'allReports.db'))
    c = conn.cursor()
    if tableName == 'suturemonster':
        up = ''
        count = 0
        for key in updated.keys():
            if key == 'url':
                count += 1
                if count > 1: up += ','
                up += 'url="{}"'.format(updated['url'])
            if key == 'subdomain':
                count += 1
                if count > 1: up += ','
                up += 'subdomain="{}"'.format(updated['subdomain'])
            if key == 'ip':
                count += 1
                if count > 1: up += ','
                up += 'ip="{}"'.format(updated['ip'])
            if key == 'web_port':
                count += 1
                if count > 1: up += ','
                up += 'web_port="{}"'.format(updated['web_port'])
            if key == 'status':
                count += 1
                if count > 1: up += ','
                up += 'status="{}"'.format(updated['status'])
            if key == 'title':
                count += 1
                if count > 1: up += ','
                up += 'title="{}"'.format(updated['title'])
            if key == 'sign':
                count += 1
                if count > 1: up += ','
                up += 'sign="{}"'.format(updated['sign'])
            if key == 'cidr':
                count += 1
                if count > 1: up += ','
                up += 'cidr="{}"'.format(updated['cidr'])
            if key == 'address':
                count += 1
                if count > 1: up += ','
                up += 'address="{}"'.format(updated['address'])
            if key == 'isp':
                count += 1
                if count > 1: up += ','
                up += 'isp="{}"'.format(updated['isp'])
            if key == 'folders':
                count += 1
                if count > 1: up += ','
                up += 'folders="{}"'.format(updated['folders'])
        sql = 'update suturemonster ' \
              'set {0} ' \
              'where {1}="{2}";' \
            .format(up, k, v)
    elif tableName == 'hostscan':
        up = ''
        count = 0
        for key in updated:
            if key == 'url':
                count += 1
                if count > 1: up += ','
                up += 'url="{}"'.format(updated['url'])
            if key == 'ip':
                count += 1
                if count > 1: up += ','
                up += 'ip="{}"'.format(updated['ip'])
            if key == 'port':
                count += 1
                if count > 1: up += ','
                up += 'port="{}"'.format(updated['port'])
            if key == 'sign':
                count += 1
                if count > 1: up += ','
                up += 'sign="{}"'.format(updated['sign'])
            if key == 'websign':
                count += 1
                if count > 1: up += ','
                up += 'websign="{}"'.format(updated['websign'])
            if key == 'fuzz':
                count += 1
                if count > 1: up += ','
                up += 'fuzz="{}"'.format(updated['fuzz'])
        sql = 'update hostscan ' \
              'set {0} ' \
              'where {1}="{2}";'\
            .format(up, k, v)
    else:
        return False
    c.execute(sql)
    conn.commit()
    conn.close()


def selectDB(rowName, tableName, k='', v=''):
    conn = src.sqlite3.connect(joinPath(src.path, 'reports', 'allReports.db'))
    c = conn.cursor()

    if k == '' and v == '': wh = ''
    else: wh = ' where {0}="{1}"'.format(k, v)
    sql = 'select {0} from {1}{2};'.format(rowName, tableName, wh)

    result = c.execute(sql)
    return result, conn


def selectAllDB(tableName):
    conn = src.sqlite3.connect(joinPath(src.path, 'reports', 'allReports.db'))
    c = conn.cursor()
    sql = 'select * from {};'.format(tableName)
    result = c.execute(sql)
    return result, conn


def readFromCSV(path):
    if str(path).find('.csv') == -1:
        print('[ERROR]{}不是csv文件!!'.format(path))
        return
    data = []
    with src.codecs.open(path, 'r', 'gbk') as r:
        for reader in src.csv.DictReader(r):
            data.append(reader)
    return data


def getColumnNames(conn, tableName):
    cur = conn.cursor()
    return cur.execute('pragma table_info({});'.format(tableName))

# sqlite的游标有状态,遍历一次后返回空值
def writeXLS(sheet, columns, data):
    for col, column in enumerate(columns):
        sheet.write(0, col, column[1])
    dataList = []
    for i in data: dataList.append(i)
    if dataList:
        for r, row in enumerate(dataList):
            for v, value in enumerate(row):
                sheet.write(r+1, v, value)


def db2xls(opath):
    # 获取所有数据和列名
    s1, c1 = selectAllDB('suturemonster')
    s2, c2 = selectAllDB('hostscan')
    columns1 = getColumnNames(conn=c1, tableName='suturemonster')
    columns2 = getColumnNames(conn=c2, tableName='hostscan')
    # 创建excel
    wb = src.xlwt.Workbook(encoding='utf-8')
    sheet1 = wb.add_sheet('webServers')
    sheet2 = wb.add_sheet('hosts')
    writeXLS(sheet=sheet1, columns=columns1, data=s1)
    writeXLS(sheet=sheet2, columns=columns2, data=s2)
    c1, c2.close()
    wb.save(opath)


def joinPath(*ps):
    if ps:
        resPath = src.os.path.join(*ps)
    else:
        resPath = src.path
    return resPath


def setTmpFromLive(fname):
    liveTXT = joinPath(src.path, 'reports', 'live.txt')
    if src.os.path.isfile(liveTXT) != -1 and \
            src.os.path.getsize(liveTXT) != 0:
        with open(liveTXT, 'r') as ch:
            with open(joinPath(src.path, 'tmp', fname + '.tmp'), 'a') as wp:
                row = 0
                if fname == 'subdoamin':row = 0
                if fname == 'live_ip':row = 1
                for r in ch.readlines():
                    wp.write(r.split('>>')[row].strip() + '\n')
