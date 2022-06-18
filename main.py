import gzhu
import os
import configparser
import time
from datetime import datetime


class Version(object):
    def __init__(self):
        self.version = '1.3'
        self.release_date = '2022/06/18'
        self.latest_ver = ''
        self.latest_rel_date = ''


class Config(object):
    def __init__(self):
        self.config_ini = configparser.ConfigParser()
        self.file_path = os.path.join(os.path.abspath('.'), '配置信息.ini')
        self.config_ini.read(self.file_path, encoding='utf-8')
a
        base_info = dict(self.config_ini.items('baseinfo'))
        # self.mode1time = base_info['mode1time']
        self.username = base_info['username']
        self.password = base_info['password']
        self.startTime = base_info['starttime']

        # 将三个字典的值str->list
        self.mode1 = self.re_flash('mode1')
        self.mode2 = self.re_flash('mode2')
        self.mode3 = self.re_flash('mode3')

    def re_flash(self, section: str) -> dict:
        """

        :rtype: dict
        """
        data = dict(self.config_ini.items(section))
        for k in data:
            data[k] = data[k].split(',')
        return data

    def set_config(self):
        un = input('输入登录融合门户的学号 > ')
        pw = input('输入登录融合门户的密码 > ')
        self.config_ini.set('baseinfo', 'username', un)
        self.config_ini.set('baseinfo', 'password', pw)

        while True:
            md = input(' 1 - 自动抢课\n 2 - 捡漏模式\n 3 - 替换模式\n 输入你使用的模式前面的数字代号 > ')
            if md in '123':
                md = 'mode' + md
                break
            else:
                print('模式输入错误')

        i = 1   # 计数器
        while True:
            print('目前正在设置第{}个教学班设置'.format(i))
            jxb = input('输入你要选的教学班号 > ').strip()  # 去掉前后空格
            bl = input('输入该教学班对应的板块:主修/体育/通识  (输入中文文字) > ').strip()
            self.config_ini.set(md, str(i), '{},{}'.format(jxb, bl))

            end_mark = input('输入0结束录入, 输入其他继续录入 > ')
            if end_mark == '0':
                self.config_ini.write(open(self.file_path, 'w', encoding='utf-8'))
                break
            i += 1


def print_data(data: list):
    for detail in data:
        print('课程名称:{course_name}  学分:{xf}分  教师:{jsxx}  容量:{total_result}/{jxbrl}  选课状态:{success}'
              '  课程号:{kch}  备注:{msg}'.format(course_name=detail['course_name'], xf=detail['xf'],
                                             jsxx=detail['jsxx'], total_result=detail['totalResult'],
                                             jxbrl=detail['jxbrl'], success=detail['success'],
                                             kch=detail['kch_id'], msg=detail['msg']))


def get_daixuan_info(xuanke_data: dict) -> list:
    # 待选信息
    daixuan_info = []
    for key in xuanke_data:
        jxbh = xuanke_data[key][0]  # 教学班号
        block = xuanke_data[key][1]  # 板块

        search_data = g.search_kch(jxbh, block)
        if len(search_data) != 0:
            # 不同教学班共用一个课程号，所以取第一个即可
            query_data = g.query_task(jxbh, search_data[0]['kch_id'], block)

            """
            如果正常,search_data应该有这些key
            'course_name': data['kcmc'],        # 课程名称：大学体育4
            'kch_id': data['kch_id'],           # 课程号ID：00121704
            'jxbmc': data['jxbmc'],             # 教学班名称：(2021-2022-2)-00121704-27
            'xf': data['xf']                    # 学分： 1.0
            'do_jxb_id': data['do_jxb_id'],     # 选课教学班id，64位哈希值
            'jsxx': data['jsxx'],               # 教师信息：103526/纪彦屹/讲师（高校）
            'totalResult': data['totalResult'], # 推测是已选人数：0
            'jxbrl': data['jxbrl']              # 教学班容量：31
            'found': True,                      # 作为已查找到的标记
            'block': '通识',                     # 板块区分
            """
            # 这里发生了转换,sd的类型从list转为dict
            all_data = {}
            all_data.update(search_data[0])
            all_data.update(query_data[0])
            all_data.update({'block': block})
            daixuan_info.append(all_data)
        else:
            search_data = {
                'course_name': '',
                'kch_id': jxbh,
                'jxbmc': '',
                'xf': '',
                'do_jxb_id': '',
                'jsxx': '',
                'totalResult': '',
                'jxbrl': '',
                # 'found': False
                'success': False,  # 选课成功标记
                'kklxdm': '',
                'xkkzid': '',
                'bklx_id': '',
                'rwlx': '',
                'xkly': '',
                'msg': '',  # 存放后面选课返回的信息作为备注
            }
            daixuan_info.append(search_data)
    # [{'cousrse_name':"...",...},{...},...]
    return daixuan_info


def xuanke1(xuanke_data: dict):
    if g.xuan_ke():
        daixuan_info = get_daixuan_info(xuanke_data=xuanke_data)
        try_time = 1
        while True:
            print(''.center(30, '='))
            print('{time}  正在进行第{tt}次轮询'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), tt=try_time))
            for daixuan in daixuan_info:
                if daixuan['course_name'] == '':
                    print('教学班号:{}查找无结果'.format(daixuan['kch_id']))
                    continue
                if daixuan['success'] is not True:
                    if (daixuan['totalResult'] < daixuan['jxbrl']) or ('通识' in daixuan['block']):
                        status, msg = g.post_do_jxb(daixuan)
                        daixuan['success'] = status
                        daixuan['msg'] = msg
                        print('{time}  {cn}选课成功'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                        cn=daixuan['course_name']))
                    else:
                        daixuan['success'] = True
                        daixuan['msg'] = '已满且为非通选课，已跳过'
                        print('{cn}已满且为非通选课，已跳过'.format(cn=daixuan['course_name']))
                        continue
            # 判断是否全部选完
            success_mark = []
            for daixuan in daixuan_info:
                success_mark.append(daixuan['success'])
            if False not in success_mark:
                print('全部选课完成'.center(30, '='))
                print_data(daixuan_info)
                break
            time.sleep(10)
            try_time += 1
        return
    else:
        print('选课系统暂未开放，5s后继续重复调用')
        time.sleep(5)
        xuanke1(xuanke_data=xuanke_data)


def xuanke2(xuanke_data: dict):
    try_time = 1
    while True:
        daixuan_info = get_daixuan_info(xuanke_data=xuanke_data)
        print(''.center(15, '-'))
        print('{time}  正在进行第{tt}次轮询'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), tt=try_time))
        for daixuan in daixuan_info:
            if daixuan['course_name'] == '':
                print('教学班号:{}查找无结果'.format(daixuan['kch_id']))
                continue
            if daixuan['success'] is not True:
                status, msg = g.post_do_jxb(daixuan)
                daixuan['success'] = status
                daixuan['msg'] = msg
                if status:
                    print('{time}  {cn}选课成功'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                    cn=daixuan['course_name']))
                else:
                    if msg == '一门课程只能选一个教学班，不可再选！':  # 没有必要再选下去，因此直接化成True即可
                        daixuan['success'] = True
                    print('{time}  {cn}选课失败  原因：{msg}'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                              cn=daixuan['course_name'], msg=daixuan['msg']))
        # 判断是否全部选完
        success_mark = []
        for daixuan in daixuan_info:
            success_mark.append(daixuan['success'])
        if try_time % 10 == 0:
            print('\n\n')
            print(''.center(30, '='))
            print_data(daixuan_info)
        if False not in success_mark:
            print('\n\n')
            print('全部选课完成'.center(30, '='))
            print_data(daixuan_info)
            break
        time.sleep(0.1)
        try_time += 1


def xuanke3(xuanke_data: dict):
    try_time = 1
    while True:
        daixuan_info = []
        for d in xuanke_data:
            tmp = {
                '1': [xuanke_data[d][0], xuanke_data[d][2]],
                '2': [xuanke_data[d][1], xuanke_data[d][2]],
            }
            row_data = get_daixuan_info(xuanke_data=tmp)
            daixuan_info.append(row_data)
        print(daixuan_info)
        print(''.center(15, '-'))
        print('{time}  正在进行第{tt}次轮询'.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), tt=try_time))


        try_time += 1


if __name__ == '__main__':
    bannerstr = r"""

 _     ___ ____ _   _ _____ _   _  ___   ___  _  __
| |   |_ _/ ___| | | |_   _| | | |/ _ \ / _ \| |/ /
| |    | | |  _| |_| | | | | |_| | | | | | | | ' / 
| |___ | | |_| |  _  | | | |  _  | |_| | |_| | . \ 
|_____|___\____|_| |_| |_| |_| |_|\___/ \___/|_|\_\
"""
    menustr = """
    Course-Bullying-in-GZHU
    0:配置信息助手
    1:登录教务系统
    2:关于信息(!)
    9:退出                                                   
"""
    verinfo = Version()
    while True:
        os.system('cls')
        print(bannerstr)
        print(menustr)
        choice_menu = input('\n输入操作前面的数字标号，按回车确定 > ')

        if choice_menu == '0':
            config = Config()
            config.set_config()
        elif choice_menu == '1':
            config = Config()
            print('正在登录教务系统中...')
            g = gzhu.GZHU(config.username, config.password)
            if g.login():
                # g.xuan_ke() 执行各种初始化操作，但这需要选课系统的开放。
                print('\n登录成功!当前用户为{un}'.format(un=config.username))
                while True:
                    print('1：自动抢课\n2：捡漏模式（推荐）\n3：替换模式（还没做）\n99：返回主界面')
                    choice_xuanke = input('请输入选课模式,按回车确定 > ')
                    if choice_xuanke == '1':
                        import schedule
                        schedule.every().day.at(config.startTime).do(xuanke1, xuanke_data=config.mode1)
                        print('已设定于{}开始抢课'.format(config.startTime))
                        while True:
                            schedule.run_pending()
                            time.sleep(5)

                    elif choice_xuanke == '2':
                        if g.xuan_ke():
                            xuanke2(config.mode2)
                        else:
                            print('选课系统未开放！')
                            os.system('pause')
                            continue

                    elif choice_xuanke == '3':
                        # xuanke3(config.mode3)
                        print('模式3还没做!')
                        os.system('pause')
                        continue

                    elif choice_xuanke == '99':
                        break

                    else:
                        print('输入有误!')
                        os.system('pause')
                        continue
                    os.system('pause')
            else:
                print('登录失败!请检查用户名和密码是否正确!高峰时期可多试几次！')
                os.system('pause')
        elif choice_menu == '2':
            os.system('cls')
            infostr = """
    GZHU抢课脚本,{rel_data}
    对于任何使用问题或讨论，请联系wuhuqifei@lighthook.xyz
    注意:使用请严格遵守法律法规和学校规章制度
    
    简单可以，简陋不行。
    """.format(rel_data=verinfo.release_date)
            print(bannerstr)
            print(infostr)
            os.system('pause')
        else:
            os._exit(0)

