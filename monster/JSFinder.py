import re
import random
import requests
from src import CheckUrl, Util
from concurrent.futures import ThreadPoolExecutor
from requests.packages import urllib3
from urllib.parse import urlparse
from bs4 import BeautifulSoup
'''
整合了JSFinder,但是光整合也没什么意思,就随手改了改,下面是原本的参数接口,可以与现在的接口进行对比;
===================================================================================================================
def parse_args():
	parser = argparse.ArgumentParser(epilog='\tExample: \r\npython ' + sys.argv[0] + " -u http://www.baidu.com")
	parser.add_argument("-u", "--url", help="The website")
	parser.add_argument("-c", "--cookie", help="The website cookie")
	parser.add_argument("-f", "--file", help="The file contains url or js")
	parser.add_argument("-ou", "--outputurl", help="Output file name. ")
	parser.add_argument("-os", "--outputsubdomain", help="Output file name. ")
	parser.add_argument("-j", "--js", help="Find in js file", action="store_true")
	parser.add_argument("-d", "--deep",help="Deep find", action="store_true")
	return parser.parse_args()
===================================================================================================================
'''
# Regular expression comes from https://github.com/GerbenJavado/LinkFinder
class JSFinder:
    def __init__(self, url, file,
                 outputurl=Util.joinPath('reports/subdomain_report/JSFinder.log'),
                 outputsubdomain=Util.joinPath('reports/subdomain_report/JSFinder_report.txt'),
                 js=True,
                 deep=True,
                 cookie=''):
        self.url = url
        self.cookie = cookie
        self.file = file
        self.outputurl = outputurl
        self.outputsubdomain = outputsubdomain
        self.js = js
        self.deep = deep
        with open(Util.joinPath('dictionary/user-agents.dict'), 'r') as ua:
            UA = ua.readlines()
        self.UA = UA

    def extract_URL(self, JS):
        pattern_raw = r"""
    	  (?:"|')                               # Start newline delimiter
    	  (
    		((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    		[^"'/]{1,}\.                        # Match a domainname (any character + dot)
    		[a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
    		|
    		((?:/|\.\./|\./)                    # Start with /,../,./
    		[^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
    		[^"'><,;|()]{1,})                   # Rest of the characters can't be
    		|
    		([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    		[a-zA-Z0-9_\-/]{1,}                 # Resource name
    		\.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    		(?:[\?|/][^"|']{0,}|))              # ? mark with parameters
    		|
    		([a-zA-Z0-9_\-]{1,}                 # filename
    		\.(?:php|asp|aspx|jsp|json|
    			 action|html|js|txt|xml)             # . + extension
    		(?:\?[^"|']{0,}|))                  # ? mark with parameters
    	  )
    	  (?:"|')                               # End newline delimiter
    	"""
        pattern = re.compile(pattern_raw, re.VERBOSE)
        result = re.finditer(pattern, str(JS))
        if result is None:
            return None
        js_url = []
        return [match.group().strip('"').strip("'") for match in result
                if match.group() not in js_url]

    # Get the page source
    def Extract_html(self, URL):
        headers = {'User-Agent': self.UA[random.randint(1, len(self.UA))].strip(),
                  'Cookie': self.cookie}
        try:
            s = requests.session()
            s.keep_alive = False
            raw = s.get(URL, headers=headers, timeout=(2, 3), verify=False)
            raw = raw.content.decode("utf-8", "ignore")
            return raw
        except:
            return None

    # Handling relative URLs
    def process_url(self, URL, re_URL):
        black_url = ["javascript:"]  # Add some keyword for filter url.
        URL_raw = urlparse(URL)
        ab_URL = URL_raw.netloc
        host_URL = URL_raw.scheme
        if re_URL[0:2] == "//":
            result = host_URL + ":" + re_URL
        elif re_URL[0:4] == "http":
            result = re_URL
        elif re_URL[0:2] != "//" and re_URL not in black_url:
            if re_URL[0:1] == "/":
                result = host_URL + "://" + ab_URL + re_URL
            else:
                if re_URL[0:1] == ".":
                    if re_URL[0:2] == "..":
                        result = host_URL + "://" + ab_URL + re_URL[2:]
                    else:
                        result = host_URL + "://" + ab_URL + re_URL[1:]
                else:
                    result = host_URL + "://" + ab_URL + "/" + re_URL
        else:
            result = URL
        return result

    def find_last(self, string, s):
        positions = []
        last_position = -1
        while True:
            position = string.find(s, last_position + 1)
            if position == -1: break
            last_position = position
            positions.append(position)
        return positions

    def find_by_url(self):
        if self.js is False:
            try:
                print("url:" + self.url)
            except:
                print("[ERROR]JSFinder:URL格式应为 -> https://www.example.com")
            html_raw = self.Extract_html(self.url)
            if html_raw is None:
                print("[ERROR]JSFinder:访问失败 -> " + self.url)
                return None
            html = BeautifulSoup(html_raw, "html.parser")
            html_scripts = html.findAll("script")
            script_array = {}
            script_temp = ""
            for html_script in html_scripts:
                script_src = html_script.get("src")
                if script_src is None:
                    script_temp += html_script.get_text() + "\n"
                else:
                    purl = self.process_url(self.url, script_src)
                    script_array[purl] = self.Extract_html(purl)
            script_array[self.url] = script_temp
            allurls = []
            for script in script_array:
                temp_urls = self.extract_URL(script_array[script])
                if len(temp_urls) == 0: continue
                for temp_url in temp_urls:
                    allurls.append(self.process_url(script, temp_url))
            result = []
            for singerurl in allurls:
                domain = urlparse(self.url).netloc
                positions = self.find_last(domain, ".")
                miandomain = domain
                if len(positions) > 1: miandomain = domain[positions[-2] + 1:]
                subdomain = urlparse(singerurl).netloc
                if miandomain in subdomain or subdomain.strip() == "":
                    if singerurl.strip() not in result:
                        result.append(singerurl)
            return result
        return sorted(set(self.extract_URL(self.Extract_html(self.url)))) or None

    def find_subdomain(self, urls, mainurl):
        url = ""
        domain = urlparse(mainurl).netloc
        miandomain = domain
        positions = self.find_last(domain, ".")
        if len(positions) > 1: miandomain = domain[positions[-2] + 1:]
        subdomains = []
        for url in urls:
            subdomain = urlparse(url).netloc
            if subdomain.strip() == "": continue
            if miandomain in subdomain:
                if subdomain not in subdomains:
                    subdomains.append(subdomain)
        print("[INFO]JSFinder:URL {0} -> 发现 {1} 条链接: ".format(url, str(len(subdomains))))
        return subdomains

    def find_by_url_deep(self):
        html_raw = self.Extract_html(self.url)
        if html_raw is None:
            print("[ERROR]JSFinder:连接失败 -> " + self.url)
            return None
        html = BeautifulSoup(html_raw, "html.parser")
        html_as = html.findAll("a")
        links = []
        for html_a in html_as:
            src = html_a.get("href")
            if src == "" or src is None: continue
            link = self.process_url(self.url, src)
            if link not in links:
                links.append(link)
        if links is []: return None
        urls = []
        for link in links:
            self.url = link
            temp_urls = self.find_by_url()
            if temp_urls is None: continue
            for temp_url in temp_urls:
                if temp_url not in urls:
                    urls.append(temp_url)
        return urls

    def find_by_file(self):
        with open(self.file, "r") as fobject:
            links = fobject.readlines()
        if not links: return None
        urls = []
        for link in links:
            if link.find('>>'):
                link = link.split('>>')[0]
            self.url = link
            temp_urls = self.find_by_url()
            if temp_urls:
                for temp_url in temp_urls:
                    if temp_url not in urls:
                        urls.append(temp_url)
        return urls, links

    # 最后输出
    def giveresult(self, urls, domian, links):
        if urls is None:return None
        print("[INFO]JSFinder:找到 {} 条链接:".format(str(len(urls))))
        content_url = ""
        content_subdomain = ""
        for url in urls:
            content_url += url + "\n"
        subdomains = self.find_subdomain(urls, domian)
        print("[INFO]JSFinder:开始验证域名存活性...")
        liveList = []
        deadList = []
        workers = 1
        if 2 < len(subdomains) <= 10: workers = 2
        elif 10 < len(subdomains) <= 50: workers = 5
        elif 50 < len(subdomains) <= 500: workers = 10
        elif 500 < len(subdomains) <= 1000: workers = 50
        elif 1000 < len(subdomains): workers = 70
        with ThreadPoolExecutor(max_workers=workers) as t:
            for subdomain in subdomains:
                for link in links:  # 新增过滤点
                    if link.find('>>'):
                        link = link.split('>>')[0]
                        if link.startswith('http'):
                            link = link.split('://')[1]
                    if subdomain.find(link) == -1:continue
                    content_subdomain += subdomain + "\n"
            for checker in content_subdomain.strip().split('\n'):
                result = t.submit(CheckUrl.checkLive, checker)
                flag, res = result.result()
                if flag:       liveList.append(res)
                elif not flag: deadList.append(res)
            CheckUrl.writeTo('dead.txt', deadList)
            # 可自定义日志输出路径
            with open(self.outputurl, "a", encoding='utf-8') as fobject:
                fobject.write(content_url)
            print("[INFO]JSFinder:输出搜索日志{}条".format(str(len(urls))))
            print("      Path:" + self.outputurl)
            # 自定义域名输出路径
            if self.outputsubdomain and not Util.joinPath('reports/subdomain_report/JSFinder_report.txt'):
                CheckUrl.writeTo(self.outputsubdomain, liveList)
                print("[INFO]JSFinder:输出域名{}条".format(str(len(liveList))))
                print("      Path:" + self.outputsubdomain)
            else:  # 默认输出路径
                with open(Util.joinPath('reports/subdomain_report/JSFinder_report.txt'), 'a') as writeTo:
                    for w in liveList:
                        writeTo.write(w + '\n')
                print("[INFO]JSFinder:输出域名{}条".format(str(len(liveList))))
                print("      Path:" + self.outputsubdomain)

    def run(self):
        urllib3.disable_warnings()
        print("[INFO]JSFinder:开始收集目标JS中的域名...")
        if self.file:
            urls, ls = self.find_by_file()
            self.giveresult(urls, urls[0], ls)
        elif self.url:
            u = self.url
            if self.deep is True:
                urls = self.find_by_url_deep()
            elif self.deep is False:
                urls = self.find_by_url()
            else:
                return False
            self.giveresult(urls, u, [u])
        else:
            print("[ERROR]JSFinder:请输入URL/URLlist.txt")
            return False
