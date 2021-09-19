#!/usr/bin/python3
# coding=utf-8

"""
OneForAll subdomain brute module

:copyright: Copyright (c) 2019, Jing Ling. All rights reserved.
:license: GNU General Public License v3.0, see LICENSE for more details.
"""
import gc
import json
import time
import secrets

import exrex
import fire
import tenacity
from dns.exception import Timeout
from dns.resolver import NXDOMAIN, YXDOMAIN, NoAnswer, NoNameservers

import export
from common import utils
from config import settings
from common.module import Module
from modules import wildcard
from config.log import logger


def gen_subdomains(expression, path):
    """
    Generate subdomains

    :param  str  expression: generate subdomains expression
    :param  str  path: path of wordlist
    :return set  subdomains: list of subdomains
    """
    subdomains = set()
    with open(path, encoding='utf-8', errors='ignore') as fd:
        for line in fd:
            word = line.strip().lower()
            if len(word) == 0:
                continue
            if not utils.is_subname(word):
                continue
            if word.startswith('.'):
                word = word[1:]
            if word.endswith('.'):
                word = word[:-1]
            subdomain = expression.replace('*', word)
            subdomains.add(subdomain)
    size = len(subdomains)
    logger.log('DEBUG', f'The size of the dictionary generated by {path} is {size}')
    if size == 0:
        logger.log('ALERT', 'Please check the dictionary content!')
    else:
        utils.check_random_subdomain(subdomains)
    return subdomains


def gen_fuzz_subdomains(expression, rule, fuzzlist):
    """
    Generate subdomains based on fuzz mode

    :param  str  expression: generate subdomains expression
    :param  str  rule: regexp rule
    :param  str  fuzzlist: fuzz dictionary
    :return set  subdomains: list of subdomains
    """
    subdomains = set()
    if fuzzlist:
        fuzz_domain = gen_subdomains(expression, fuzzlist)
        subdomains.update(fuzz_domain)
    if rule:
        fuzz_count = exrex.count(rule)
        if fuzz_count > 10000000:
            logger.log('ALERT', f'The dictionary generated by this rule is too large: '
                                f'{fuzz_count} > 10000000')
        for fuzz_string in exrex.generate(rule):
            fuzz_string = fuzz_string.lower()
            if not fuzz_string.isalnum():
                continue
            fuzz_domain = expression.replace('*', fuzz_string)
            subdomains.add(fuzz_domain)
        utils.check_random_subdomain(subdomains)
    logger.log('DEBUG', f'Dictionary size based on fuzz mode: {len(subdomains)}')
    return subdomains


def gen_word_subdomains(expression, path):
    """
    Generate subdomains based on word mode

    :param  str  expression: generate subdomains expression
    :param  str  path: path of wordlist
    :return set  subdomains: list of subdomains
    """
    subdomains = gen_subdomains(expression, path)
    logger.log('DEBUG', f'Dictionary based on word mode size: {len(subdomains)}')
    return subdomains


def query_domain_ns_a(ns_list):
    logger.log('INFOR', f'Querying A record from authoritative name server: {ns_list} ')
    if not isinstance(ns_list, list):
        return list()
    ns_ip_list = []
    resolver = utils.dns_resolver()
    for ns in ns_list:
        try:
            answer = resolver.query(ns, 'A')
        except Exception as e:
            logger.log('ERROR', e.args)
            logger.log('ERROR', f'Query authoritative name server {ns} A record error')
            continue
        if answer:
            for item in answer:
                ns_ip_list.append(item.address)
    logger.log('INFOR', f'Authoritative name server A record result: {ns_ip_list}')
    return ns_ip_list


def query_domain_ns(domain):
    logger.log('INFOR', f'Querying NS records of {domain}')
    domain = utils.get_main_domain(domain)
    resolver = utils.dns_resolver()
    try:
        answer = resolver.query(domain, 'NS')
    except Exception as e:
        logger.log('ERROR', e.args)
        logger.log('ERROR', f'Querying NS records of {domain} error')
        return list()
    ns = [item.to_text() for item in answer]
    logger.log('INFOR', f'{domain}\'s authoritative name server is {ns}')
    return ns


def check_dict():
    if not settings.enable_check_dict:
        return
    sec = settings.check_time
    logger.log('ALERT', f'You have {sec} seconds to check '
                        f'whether the configuration is correct or not')
    logger.log('ALERT', f'If you want to exit, please use `Ctrl + C`')
    try:
        time.sleep(sec)
    except KeyboardInterrupt:
        logger.log('INFOR', 'Due to configuration incorrect, exited')
        exit(0)


def gen_result_infos(items, infos, subdomains, appear_times, wc_ips, wc_ttl):
    qname = items.get('name')[:-1]  # 去除最右边的`.`点号
    reason = items.get('status')
    resolver = items.get('resolver')
    data = items.get('data')
    answers = data.get('answers')
    info = dict()
    cnames = list()
    ips = list()
    ip_times = list()
    cname_times = list()
    ttls = list()
    is_valid_flags = list()
    have_a_record = False
    for answer in answers:
        if answer.get('type') != 'A':
            continue
        have_a_record = True
        ttl = answer.get('ttl')
        ttls.append(ttl)
        name = answer.get('name')  # 去除最右边的`.`点号
        cname = name[:-1].lower()  # 去除最右边的`.`点号
        cnames.append(cname)
        cname_num = appear_times.get(cname)
        cname_times.append(cname_num)
        ip = answer.get('data')
        ips.append(ip)
        ip_num = appear_times.get(ip)
        ip_times.append(ip_num)
        isvalid, reason = wildcard.is_valid_subdomain(ip, ip_num, cname, cname_num, ttl, wc_ttl, wc_ips)
        logger.log('TRACE', f'{ip} effective: {isvalid} reason: {reason}')
        is_valid_flags.append(isvalid)
    if not have_a_record:
        logger.log('TRACE', f'All query result of {qname} no A record{answers}')
    # 为了优化内存 只添加有A记录且通过判断的子域到记录中
    if have_a_record and all(is_valid_flags):
        info['resolve'] = 1
        info['reason'] = reason
        info['ttl'] = ttls
        info['cname'] = cnames
        info['ip'] = ips
        info['ip_times'] = ip_times
        info['cname_times'] = cname_times
        info['resolver'] = resolver
        infos[qname] = info
        subdomains.append(qname)
    return infos, subdomains


def stat_appear_times(result_path):
    logger.log('INFOR', f'Counting IP cname appear times')
    times = dict()
    logger.log('DEBUG', f'Reading {result_path}')
    with open(result_path) as fd:
        for line in fd:
            line = line.strip()
            try:
                items = json.loads(line)
            except Exception as e:
                logger.log('ERROR', e.args)
                logger.log('ERROR', f'Error parsing {result_path} '
                                    f'line {line} Skip this line')
                continue
            status = items.get('status')
            if status != 'NOERROR':
                continue
            data = items.get('data')
            if 'answers' not in data:
                continue
            answers = data.get('answers')
            for answer in answers:
                if answer.get('type') == 'A':
                    ip = answer.get('data')
                    # 取值 如果是首次出现的IP集合 出现次数先赋值0
                    value_one = times.setdefault(ip, 0)
                    times[ip] = value_one + 1
                    name = answer.get('data')
                    cname = name[:-1].lower()  # 去除最右边的`.`点号
                    # 取值 如果是首次出现的IP集合 出现次数先赋值0
                    value_two = times.setdefault(cname, 0)
                    times[cname] = value_two + 1
                if answer.get('type') == 'CNAME':
                    name = answer.get('data')
                    cname = name[:-1].lower()  # 去除最右边的`.`点号
                    # 取值 如果是首次出现的IP集合 出现次数先赋值0
                    value_three = times.setdefault(cname, 0)
                    times[cname] = value_three + 1
    return times


def deal_output(output_path, appear_times, wildcard_ips, wildcard_ttl):
    logger.log('INFOR', f'Processing result')
    infos = dict()  # 用来记录所有域名有关信息
    subdomains = list()  # 用来保存所有通过有效性检查的子域
    logger.log('DEBUG', f'Processing {output_path}')
    with open(output_path) as fd:
        for line in fd:
            line = line.strip()
            try:
                items = json.loads(line)
            except Exception as e:
                logger.log('ERROR', e.args)
                logger.log('ERROR', f'Error parsing {line} Skip this line')
                continue
            qname = items.get('name')[:-1]  # 去除最右边的`.`点号
            status = items.get('status')
            if status != 'NOERROR':
                logger.log('TRACE', f'Found {qname}\'s result {status} '
                                    f'while processing {line}')
                continue
            data = items.get('data')
            if 'answers' not in data:
                logger.log('TRACE', f'Processing {line}, {qname} no response')
                continue
            infos, subdomains = gen_result_infos(items, infos, subdomains,
                                                 appear_times, wildcard_ips,
                                                 wildcard_ttl)
    return infos, subdomains


def save_brute_dict(dict_path, dict_set):
    dict_data = '\n'.join(dict_set)
    if not utils.save_to_file(dict_path, dict_data):
        logger.log('FATAL', 'Saving dictionary error')
        exit(1)


def delete_file(dict_path, output_path):
    if settings.delete_generated_dict:
        dict_path.unlink()
    if settings.delete_massdns_result:
        output_path.unlink()


class Brute(Module):
    """
    OneForAll subdomain brute module

    Example：
        brute.py --target domain.com --word True run
        brute.py --targets ./domains.txt --word True run
        brute.py --target domain.com --word True --concurrent 2000 run
        brute.py --target domain.com --word True --wordlist subnames.txt run
        brute.py --target domain.com --word True --recursive True --depth 2 run
        brute.py --target d.com --fuzz True --place m.*.d.com --rule '[a-z]' run
        brute.py --target d.com --fuzz True --place m.*.d.com --fuzzlist subnames.txt run

    Note:
        --fmt csv/json (result format)
        --path   Result path (default None, automatically generated)


    :param str  target:     One domain (target or targets must be provided)
    :param str  targets:    File path of one domain per line
    :param int  concurrent: Number of concurrent (default 2000)
    :param bool word:       Use word mode generate dictionary (default False)
    :param str  wordlist:   Dictionary path used in word mode (default use ./config/default.py)
    :param bool recursive:  Use recursion (default False)
    :param int  depth:      Recursive depth (default 2)
    :param str  nextlist:   Dictionary file path used by recursive (default use ./config/default.py)
    :param bool fuzz:       Use fuzz mode generate dictionary (default False)
    :param bool alive:      Only export alive subdomains (default False)
    :param str  place:      Designated fuzz position (required if use fuzz mode)
    :param str  rule:       Specify the regexp rules used in fuzz mode (required if use fuzz mode)
    :param str  fuzzlist:   Dictionary path used in fuzz mode (default use ./config/default.py)
    :param bool export:     Export the results (default True)
    :param str  fmt:        Result format (default csv)
    :param str  path:       Result directory (default None)
    """
    def __init__(self, target=None, targets=None, concurrent=None,
                 word=False, wordlist=None, recursive=False, depth=None,
                 nextlist=None, fuzz=False, place=None, rule=None, fuzzlist=None,
                 export=True, alive=True, fmt='csv', path=None):
        Module.__init__(self)
        self.module = 'Brute'
        self.source = 'Brute'
        self.target = target
        self.targets = targets
        self.concurrent_num = concurrent or settings.brute_concurrent_num
        self.word = word
        self.wordlist = wordlist or settings.brute_wordlist_path
        self.recursive_brute = recursive or settings.enable_recursive_brute
        self.recursive_depth = depth or settings.brute_recursive_depth
        self.recursive_nextlist = nextlist or settings.recursive_nextlist_path
        self.fuzz = fuzz or settings.enable_fuzz
        self.place = place or settings.fuzz_place
        self.rule = rule or settings.fuzz_rule
        self.fuzzlist = fuzzlist or settings.fuzz_list
        self.export = export
        self.alive = alive
        self.fmt = fmt
        self.path = path
        self.bulk = False  # 是否是批量爆破场景
        self.domains = list()  # 待爆破的所有域名集合
        self.domain = str()  # 当前正在进行爆破的域名
        self.ips_times = dict()  # IP集合出现次数
        self.enable_wildcard = None  # 当前域名是否使用泛解析
        self.quite = False
        self.in_china = None

    def gen_brute_dict(self, domain):
        logger.log('INFOR', f'Generating dictionary for {domain}')
        dict_set = set()
        # 如果domain不是self.subdomain 而是self.domain的子域则生成递归爆破字典
        if self.word:
            self.place = ''
        if not self.place:
            self.place = '*.' + domain
        wordlist = self.wordlist
        main_domain = utils.get_main_domain(domain)
        if domain != main_domain:
            wordlist = self.recursive_nextlist
        if self.word:
            word_subdomains = gen_word_subdomains(self.place, wordlist)
            dict_set.update(word_subdomains)
        if self.fuzz:
            fuzz_subdomains = gen_fuzz_subdomains(self.place, self.rule, self.fuzzlist)
            dict_set.update(fuzz_subdomains)
        count = len(dict_set)
        logger.log('INFOR', f'Dictionary size: {count}')
        if count > 10000000:
            logger.log('ALERT', f'The generated dictionary is '
                                f'too large {count} > 10000000')
        return dict_set

    def check_brute_params(self):
        if not (self.word or self.fuzz):
            logger.log('FATAL', f'Please specify at least one brute mode')
            exit(1)
        if len(self.domains) > 1:
            self.bulk = True
        if self.fuzz:
            if self.place is None:
                logger.log('FATAL', f'No fuzz position specified')
                exit(1)
            if self.rule is None and self.fuzzlist is None:
                logger.log('FATAL', f'No fuzz rules or fuzz dictionary specified')
                exit(1)
            if self.bulk:
                logger.log('FATAL', f'Cannot use fuzz mode in the bulk brute')
                exit(1)
            if self.recursive_brute:
                logger.log('FATAL', f'Cannot use recursive brute in fuzz mode')
                exit(1)
            fuzz_count = self.place.count('*')
            if fuzz_count < 1:
                logger.log('FATAL', f'No fuzz position specified')
                exit(1)
            if fuzz_count > 1:
                logger.log('FATAL', f'Only one fuzz position can be specified')
                exit(1)
            if self.domain not in self.place:
                logger.log('FATAL', f'Incorrect domain for fuzz')
                exit(1)

    def init_dict_path(self):
        data_dir = settings.data_storage_dir
        if self.wordlist is None:
            self.wordlist = settings.brute_wordlist_path or data_dir.joinpath('subnames.txt')
        if self.recursive_nextlist is None:
            self.recursive_nextlist = settings.recursive_nextlist_path or data_dir.joinpath('subnames_next.txt')

    def main(self, domain):
        start = time.time()
        logger.log('INFOR', f'Blasting {domain} ')
        massdns_dir = settings.third_party_dir.joinpath('massdns')
        result_dir = settings.result_save_dir
        temp_dir = result_dir.joinpath('temp')
        utils.check_dir(temp_dir)
        massdns_path = utils.get_massdns_path(massdns_dir)
        timestring = utils.get_timestring()

        wildcard_ips = list()  # 泛解析IP列表
        wildcard_ttl = int()  # 泛解析TTL整型值
        ns_list = query_domain_ns(self.domain)
        ns_ip_list = query_domain_ns_a(ns_list)  # DNS权威名称服务器对应A记录列表
        if self.enable_wildcard is None:
            self.enable_wildcard = wildcard.detect_wildcard(domain)

        if self.enable_wildcard:
            wildcard_ips, wildcard_ttl = wildcard.collect_wildcard_record(domain, ns_ip_list)
        ns_path = utils.get_ns_path(self.in_china, self.enable_wildcard, ns_ip_list)

        dict_set = self.gen_brute_dict(domain)

        dict_name = f'generated_subdomains_{domain}_{timestring}.txt'
        dict_path = temp_dir.joinpath(dict_name)
        save_brute_dict(dict_path, dict_set)
        del dict_set
        gc.collect()

        output_name = f'resolved_result_{domain}_{timestring}.json'
        output_path = temp_dir.joinpath(output_name)
        log_path = result_dir.joinpath('massdns.log')
        check_dict()
        logger.log('INFOR', f'Running massdns to brute subdomains')
        utils.call_massdns(massdns_path, dict_path, ns_path, output_path,
                           log_path, quiet_mode=self.quite,
                           concurrent_num=self.concurrent_num)
        appear_times = stat_appear_times(output_path)
        self.infos, self.subdomains = deal_output(output_path, appear_times,
                                                  wildcard_ips, wildcard_ttl)
        delete_file(dict_path, output_path)
        end = time.time()
        self.elapse = round(end - start, 1)
        logger.log('ALERT', f'{self.source} module takes {self.elapse} seconds, '
                            f'found {len(self.subdomains)} subdomains of {domain}')
        logger.log('DEBUG', f'{self.source} module found subdomains of {domain}: '
                            f'{self.subdomains}')
        self.gen_result()
        self.save_db()
        return self.subdomains

    def run(self):
        logger.log('INFOR', f'Start running {self.source} module')
        if self.in_china is None:
            _, self.in_china = utils.get_net_env()
        self.domains = utils.get_domains(self.target, self.targets)
        for self.domain in self.domains:
            self.results = list()  # 置空
            all_subdomains = list()
            self.init_dict_path()
            self.check_brute_params()
            if self.recursive_brute:
                logger.log('INFOR', f'Start recursively brute the 1 layer subdomain'
                                    f' of {self.domain}')
            valid_subdomains = self.main(self.domain)

            all_subdomains.extend(valid_subdomains)

            # 递归爆破下一层的子域
            # fuzz模式不使用递归爆破
            if self.recursive_brute:
                for layer_num in range(1, self.recursive_depth):
                    # 之前已经做过1层子域爆破 当前实际递归层数是layer+1
                    logger.log('INFOR', f'Start recursively brute the {layer_num + 1} '
                                        f'layer subdomain of {self.domain}')
                    for subdomain in all_subdomains:
                        self.place = '*.' + subdomain
                        # 进行下一层子域爆破的限制条件
                        num = subdomain.count('.') - self.domain.count('.')
                        if num == layer_num:
                            valid_subdomains = self.main(subdomain)
                            all_subdomains.extend(valid_subdomains)

            logger.log('INFOR', f'Finished {self.source} module to brute {self.domain}')
            if not self.path:
                name = f'{self.domain}_brute_result.{self.fmt}'
                self.path = settings.result_save_dir.joinpath(name)
            # 数据库导出
            if self.export:
                export.export_data(self.domain,
                                   alive=self.alive,
                                   limit='resolve',
                                   path=self.path,
                                   fmt=self.fmt)


if __name__ == '__main__':
    fire.Fire(Brute)
