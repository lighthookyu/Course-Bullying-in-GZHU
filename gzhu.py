import json
import requests
import re
import execjs
from lxml import html


def get_rsa(un, psd, lt):
    js_res = requests.get('https://newcas.gzhu.edu.cn/cas/comm/js/des.js')
    context = execjs.compile(js_res.text)
    result = context.call("strEnc", un + psd + lt, '1', '2', '3')
    return result


class GZHU(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = requests.session()

        self.xkkz_dict = {
            # '通识': [],
            # '体育': [],
            # '主修': [],
        }
        # key:['主修课程', '板块课(体育4)', '通识选修', '其他特殊课程']
        # 每个value大概是：['01', 'D454960F86CF7DFDE053206411AC34BB', '2020', '6590']
        # 代表：kklxdm、xkkz_id、njdm_id、zyh_id

        self.jg_id = ''
        self.bh_id = ''
        self.ccdm = ''
        self.kklxdm = ''
        self.njdmId = ''
        self.xbm = ''
        self.xkkzId = ''
        self.xkxnm = ''
        self.xkxqm = ''
        self.xqh_id = ''
        self.xsbj = ''
        self.xslbdm = ''
        self.zyfx_id = ''
        self.zyh_id = ''
        self.jxbzb = ''

        self.bklx_id = ''
        self.rwlx = ''
        self.xkly = ''
        self.xklc = ''  # 选课轮次
        self.sfkknj = ''
        self.sfkkzy = ''
        self.sfkgbcx = ''
        self.tykczgxdcs = ''
        self.rlkz = ''

        self.xkzgbj = ''

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
            # 'Accept': 'application/json, text/javascript, */*; q=0.01',
            # 'Accept-Encoding': 'gzip, deflate',
            # 'Accept-Language': 'zh-CN,zh;q=0.9',
            # 'Cache-Control': 'no-cache',
            # 'Connection': 'keep-alive',
            # 'Content-Length': '340',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Host': 'jwxt.gzhu.edu.cn',
            'Origin': 'http://jwxt.gzhu.edu.cn',
            # 'Pragma': 'no-cache',
            'Referer': 'http://jwxt.gzhu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default'
                       '&su={}'.format(self.username),
        }
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
        }

    def login(self):
        new_cas_url = 'https://newcas.gzhu.edu.cn/cas/login'
        res = self.client.get(new_cas_url, timeout=None)
        lt = re.findall(r'name="lt" value="(.*)"', res.text)

        login_form = {
            'rsa': get_rsa(self.username, self.password, lt[0]),
            'ul': len(self.username),
            'pl': len(self.password),
            'lt': lt[0],
            'execution': 'e1s1',
            '_eventId': 'submit',
        }

        resp = self.client.post(new_cas_url, data=login_form, timeout=None)
        # print('[debug]:{}'.format(resp.url))
        selector = html.fromstring(resp.text)
        if selector.xpath('//title/text()')[0] == '融合门户':
            jwxt_login = 'http://jwxt.gzhu.edu.cn/sso/driot4login'
            res = self.client.get(url=jwxt_login, headers=self.base_headers, timeout=None)
            return True
        else:
            return False

    def xuan_ke(self):
        """
        教务系统初始化，需要选课开放的时候才会返回True,
        获取
            jg_id:32位哈希值
            bh_id:9位数字

        :return:
            设置self.jg_id: 后续查询需要用到，
        """

        jwxt_url = 'http://jwxt.gzhu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html?' \
                   'gnmkdm=N253512&layout=default&su={}'.format(self.username)
        resp = self.client.get(url=jwxt_url, headers=self.base_headers, timeout=None)

        # print('[debug]:{}'.format(resp.text))

        if '本学期选课要求' in resp.text:
            selector = html.fromstring(resp.text)
            self.jg_id = selector.xpath('//input[@name="jg_id_1"]/@value')[0]
            self.bh_id = selector.xpath('//input[@name="bh_id"]/@value')[0]
            self.ccdm = selector.xpath('//input[@name="ccdm"]/@value')[0]
            # self.kklxdm = selector.xpath('//input[@name="firstKklxdm"]/@value')[0]
            self.njdmId = selector.xpath('//input[@name="firstNjdmId"]/@value')[0]
            self.xbm = selector.xpath('//input[@name="xbm"]/@value')[0]
            # self.xkkzId = selector.xpath('//input[@name="firstXkkzId"]/@value')[0]
            self.xkxnm = selector.xpath('//input[@name="xkxnm"]/@value')[0]
            self.xkxqm = selector.xpath('//input[@name="xkxqm"]/@value')[0]
            self.xqh_id = selector.xpath('//input[@name="xqh_id"]/@value')[0]
            self.xsbj = selector.xpath('//input[@name="xsbj"]/@value')[0]
            self.xslbdm = selector.xpath('//input[@name="xslbdm"]/@value')[0]
            self.zyfx_id = selector.xpath('//input[@name="zyfx_id"]/@value')[0]
            self.zyh_id = selector.xpath('//input[@name="zyh_id"]/@value')[0]

            # 这个参数第二轮出现，第一轮和第三轮暂时不清楚
            self.jxbzb = selector.xpath('//input[@name="jxbzb"]/@value')[0]

            tab_data = selector.xpath('//a[@data-toggle="tab"]/@onclick')
            tab_label = selector.xpath('//a[@data-toggle="tab"]/text()')
            for i in range(len(tab_label)):
                self.xkkz_dict.update({
                    tab_label[i]: tab_data[i][18:-2].split("','")
                    # queryCourse(this,'01','D454960F86CF7DFDE053206411AC34BB','2020','6590')
                    # 变成
                    # ['01', 'D454960F86CF7DFDE053206411AC34BB', '2020', '6590']
                })
            return True
        else:
            return False

    def get_tab_data(self, block: str):
        """
        刷新该tab下的数据
        :param block: 关键字包含就行
        :return:
        """
        for i in self.xkkz_dict.keys():
            if block in i:
                # 根据xkkz_id刷新几个数据：bklx、xkly、rwlx。每次请求都要调用的
                jwxt_url = 'http://jwxt.gzhu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbDisplay.html?' \
                           'gnmkdm=N253512&layout=default&su={}'.format(self.username)
                data = {
                    'xkkz_id': self.xkkz_dict[i][1],
                    'xszxzt': '1',
                    'kspage': '0',
                    'jspage': '0',
                }
                resp = self.client.post(url=jwxt_url, data=data, headers=self.base_headers, timeout=None)
                selector = html.fromstring(resp.text)
                self.bklx_id = selector.xpath('//input[@name="bklx_id"]/@value')[0]
                self.rwlx = selector.xpath('//input[@name="rwlx"]/@value')[0]
                self.xkly = selector.xpath('//input[@name="xkly"]/@value')[0]
                self.xklc = selector.xpath('//input[@name="xklc"]/@value')[0]
                self.sfkknj = selector.xpath('//input[@name="sfkknj"]/@value')[0]
                self.sfkkzy = selector.xpath('//input[@name="sfkkzy"]/@value')[0]
                self.sfkgbcx = selector.xpath('//input[@name="sfkgbcx"]/@value')[0]
                self.tykczgxdcs = selector.xpath('//input[@name="tykczgxdcs"]/@value')[0]
                self.rlkz = selector.xpath('//input[@name="rlkz"]/@value')[0]

                if self.xklc == '2':
                    self.xkzgbj = selector.xpath('//input[@name="xkzgbj"]/@value')[0]

                # 返回kklxxdm、xkkzid
                return self.xkkz_dict[i][0], self.xkkz_dict[i][1],

    def search_kch(self, keyword: str, block: str) -> list or None:
        """

        :param keyword:搜索关键词
        :param block: 三个板块：主修课程、体育课程、通识选修
        :return:
        """
        search_url = 'http://jwxt.gzhu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html?gnmkdm=N253512' \
                     '&su={}'.format(self.username)

        # 都要刷新
        kklxxdm, xkkzid = self.get_tab_data(block)

        data = {
            'bh_id': self.bh_id,
            'bklx_id': self.bklx_id,
            'ccdm': self.ccdm,
            'filter_list[0]': str(keyword),     # 这里输入中文
            'jg_id': self.jg_id,
            'jspage': '10',
            'kkbk': '0',
            'kkbkdj': '0',
            'kklxdm': kklxxdm,
            'kspage': '1',
            'njdm_id': self.njdmId,
            'rlkz': self.rlkz,
            'rwlx': self.rwlx,
            'sfkcfx': '0',
            'sfkgbcx': self.sfkgbcx,
            'sfkknj': self.sfkknj,
            'sfkkzy': self.sfkkzy,
            'sfkxq': '0',
            'sfrxtgkcxd': '1',
            'sfznkx': '0',
            'tykczgxdcs': self.tykczgxdcs,
            'xbm': self.xbm,
            'xkly': self.xkly,
            'xkxnm': self.xkxnm,
            'xkxqm': self.xkxqm,
            'xqh_id': self.xqh_id,
            'xsbj': self.xsbj,
            'xslbdm': self.xslbdm,
            'zdkxms': '0',
            'zyfx_id': self.zyfx_id,
            'zyh_id': self.zyh_id,
        }
        if self.xklc != '1':
            data.update(
                {
                    "xkzgbj": self.xkzgbj,
                    "jxbzb": self.jxbzb,
                }
            )
        resp = self.client.post(url=search_url, data=data, headers=self.base_headers, timeout=None)
        # print('[debug]:{}'.format(resp.url))
        search_result = json.loads(resp.text)['tmpList']
        try:
            search_data = []
            for data in search_result:
                search_data.append({
                    'course_name': data['kcmc'],    # 课程名称：大学体育4
                    'kch_id': data['kch_id'],   # 课程号ID：00121704
                    'jxbmc': data['jxbmc'],     # 教学班名称：(2021-2022-2)-00121704-27
                    'xf': data['xf'],           # 学分： 1.0
                    'totalResult': data['yxzrs'],  # 已选人数：0
                    # 'found': True               # 作为已查找到的标记
                })
            return search_data
            # [{
            #   'course_name':'xxx',
            #   'kch_id': '1234',
            #   ...
            # },...]
        except Exception as e:
            print('SEARCH_ERROR:{}'.format(e))
            return None

    def query_task(self, keyword: str, kch: str, block: str) -> list or None:
        """
        根据课程号查询具体课程
        :return:
        """
        query_task_url = 'http://jwxt.gzhu.edu.cn/jwglxt/xsxk/zzxkyzbjk_cxJxbWithKchZzxkYzb.html?gnmkdm=N253512' \
                         '&su={}'.format(self.username)
        kklxxdm, xkkzid = self.get_tab_data(block)

        data = {
            'bh_id': self.bh_id,
            'bklx_id': self.bklx_id,
            'ccdm': self.ccdm,
            'cxbj': '0',      # 重修标记
            'filter_list[0]': str(keyword),
            'fxbj': '0',      # 辅修标记
            'jg_id': self.jg_id,    # 机构id？
            'kch_id': kch,  # 课程号
            'kkbk': '0',
            'kkbkdj': '0',
            'kklxdm': kklxxdm,
            'njdm_id': self.njdmId,     # 年级代码
            'rlkz': self.rlkz,
            'rwlx': self.rwlx,  # 找不到,应该可以写死
            'sfkcfx': '0',
            'sfkknj': self.sfkknj,
            'sfkkzy': self.sfkkzy,
            'sfkxq': '0',
            'sfznkx': '0',
            'xbm': '1',
            'xkkz_id': xkkzid,
            'xkly': self.xkly,      # 选课xx？ 0/2
            'xkxnm': self.xkxnm,
            'xkxqm': self.xkxqm,
            'xqh_id': self.xqh_id,
            'xsbj': self.xsbj,
            'xslbdm': self.xslbdm,
            'zdkxms': '0',    # ?
            'zyfx_id': self.zyfx_id,
            'zyh_id': self.zyh_id,  # 专业代号
        }
        # output = self.change_data(data)
        resp = self.client.post(url=query_task_url, data=data, headers=self.headers, timeout=None)
        # print(resp)
        kc_result = json.loads(resp.text)
        try:
            query_data = []
            for data in kc_result:
                query_data.append({
                    'do_jxb_id': data['do_jxb_id'],     # 选课教学班id，64位哈希值
                    'jsxx': re.findall(r'/(.*)/', data['jsxx'])[0],               # 教师信息：103526/纪彦屹/讲师（高校）
                    # 'totalResult': data['totalResult'], # 推测是已选人数：0
                    'jxbrl': data['jxbrl'],             # 教学班容量：31
                    'success': False,                   # 选课成功标记
                    # 这里添加的信息是课程类型刷新的时候改变的信息,post_do_jxb需要用到
                    'kklxdm': kklxxdm,
                    'xkkzid': xkkzid,
                    'bklx_id': str(self.bklx_id),
                    'rwlx': str(self.rwlx),
                    'xkly': str(self.xkly),
                    'msg': '',  # 存放后面选课返回的信息作为备注
                })
            return query_data
        except Exception as e:
            print('QUERY ERROR:{}'.format(e))
            return None

    def post_do_jxb(self, daixuan_data: dict, ):
        print('正在选课:{}'.format(daixuan_data['course_name']))
        submit_url = 'http://jwxt.gzhu.edu.cn/jwglxt/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html?gnmkdm=N253512' \
                     '&su={}'.format(self.username)
        kcmc = '({kch}){cn}+-+{xf}+学分'.format(kch=daixuan_data['kch_id'], cn=daixuan_data['course_name'],
                                              xf=daixuan_data['xf'])
        data = {
            'cxbj': '0',
            'jxb_ids': daixuan_data['do_jxb_id'],
            'kch_id': daixuan_data['kch_id'],
            'kcmc': kcmc,
            'kklxdm': daixuan_data['kklxdm'],
            'njdm_id': self.njdmId,
            'qz': '0',
            'rlkz': self.rlkz,
            'rlzlkz': '1',
            'rwlx': daixuan_data['rwlx'],
            'sxbj': '1',
            'xkkz_id': daixuan_data['xkkzid'],
            'xklc': self.xklc,
            'xkxnm': self.xkxnm,    # 这个不会变
            'xkxqm': self.xkxqm,
            'xxkbj': '0',   # todo 注意这个值
            'zyh_id': self.zyh_id,
        }
        resp = self.client.post(url=submit_url, data=data, headers=self.base_headers, timeout=None)

        submit_result = json.loads(resp.text)
        if submit_result['flag'] == '1':
            # 选课成功
            return True, 'success'
        elif submit_result['flag'] == '0':
            # 选课失败
            return False, submit_result['msg']
        elif submit_result['flag'] == '-1':
            return False, '课程已满'
        else:
            # 不明原因失败
            return False, 'SUBMIT ERROR'

    def tuike(self):
        pass
