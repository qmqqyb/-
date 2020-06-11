import requests
import re
import os
import json

# cookies序列化文件
COOKIES_FILE_PATH = 'taobao_login_cookies.txt'

class UsernameLogin():
    def __init__(self ,s):
        """
        账号登录对象
        :param username: 用户名
        :param ua: 淘宝的ua参数
        :param TPL_password2: 加密后的密码
        """
        # 检查是否需要验证码的URL
        self.nick_check_url = 'https://login.taobao.com/member/request_nick_check.do?_input_charset=utf-8'
        # 验证淘宝用户名密码和url
        self.verify_password_url = 'https://login.taobao.com/member/login.jhtml'
        # 访问st码的url
        self.vst_url = 'https://login.taobao.com/member/vst.htm?st={}'
        # 个人淘宝主页
        self.my_taobao_url = 'https://i.taobao.com/my_taobao.htm'
        # 淘宝用户名
        self.username = 'qmqqyb'
        # 淘宝关键参数，包含用户浏览器等一些信息，很多地方会使用，从浏览器或者抓包工具中获得，可重复使用
        self.ua = '122#qBE8MDXXEEJaREpZMEpJEJponDJE7SNEEP7rEJ+/f9t/2oQLpo7iEDpWnDEeK51HpyGZp9hBuDEEJFOPpC76EJponDJL7gNpEPXZpJRgu4Ep+FQLpoGUEJLWn4yP7SQEEyuLpEROIrf1prZCnaRx9kb/oUdNYsqjNduTadOVWWBKu9Kh9V4BuA7CVWwFl6fro9xVzFdxhQdCsX4qbw3qLy4RC0HiO+6KxKurhr+GiifQ/j6JUhTJB+lnyi7LGaYuqlOzWZgUV43dQzEpsuADqMfpnekpZW9kTPbEELXAO42zlELV4CmD7W3bEEpxngR4eN/Yi+mr8Cp6+DPEyFfOefMOwzVanSbWuO5EELGA8oL6JNEEyBfDqMfbDEpCnSL1ul0EDLVr8CpUJzbEyF3mqW32E5pamMp1uOZWELXr8ytkalYEmtWTTTz4p5asp5ofpQftM0+LnjQx3giiuhlr8fKV7r7P6bMRO8eTjBS3gw0dafmv/xi+1eRaupEm2HSlPfgBH+RuTCMOo0eGM+I/rNnJ6RN/AW7upUHCMI+1+n+SMgUUod2p9DFIgEIlPQp+AyNjK0uigdJ76rJ9mNzACeAqDxhzpijR6atHJ6qWcsXWxthftnjFP1z1DfkD7tTiN5hPesBplL0UbWmCNl5KXF3fzx/N1Yn3euS8TH2srJJlXp8veSCRckylnx9/aBFR8iP/55y+WriEOaEWpYscDBpmQv/PgmD0M+ImpxIPPUpSnb3EPVcZmsc4QSiiD/9zI3NbjWRCSi/7JAXeHRoPYZmDlvEwnA+ktTuniOxaUjibseB22g4qBzFGOFbXmA4n0ahO7IkuV1Z1aiDPVVvdaR/vfvAai6ImBV66+gXTSjqToWNJp9icNfQpVV5mMVhseCD4fxajvW1Fyy1n76rTvIFn4oimgC/ikxleMk1Qzcq1i3R45zC+kWDC/+l0Fm4bdPp5NYQCuO8z99M/vVVz9jlkXPhtMnfIVlOGvBq0JYA5QrLDjPH8vwZBZuuOjjXhNhU6DK/OJxn/KQuQ7HX4DzY5+zMIlpsGq1fz6bJ60IAABVAe6iW6QWOWvImXXFgUTPafCsi4oqVzj30MmZiBs+OcpwKgRTHPT3caqeOZ2y98qtgw5JfvXt4='
        # 加密后的密码，从浏览器或者抓包工具中复制，可重复使用
        self.TPL_password2 = '1182d5f82682bd2e0990747301a449f3e8f9380f7162170a2d130bb98d3fe3b91e97a879c3834d375b6a3806fef59c0033245a8f394e49ba1d1c2a352e6d98872cd634c73ce20c9dfba4e0b11e223ac003f33b87c349177e5072627ace7edd014a7209951e03ce58a67b1e568969171ef2fff832260c84a87e6d435c101994f2'
        #请求超长时间
        self.timeout = 3
        # session对象，用于共享cookie
        self.session = s



    def _nick_check(self):
        """
        检测账号是否需要验证码
        :return:
        """
        data = {
            'username': self.username,
            'ua': self.ua
        }
        try:
            resp = self.session.post(self.nick_check_url, data=data, timeout=self.timeout)
        except Exception as e:
            print('检测是否需要验证码请求失败，原因：{}'.format(e))
            return True
        needcode = resp.json()["needcode"]
        print('是否需要验证码验证：{}'.format(needcode))
        return needcode


    def verify_password(self):
        # print(self.TPL_password2)
        verify_password_headers = {
            'connection': 'keep-alive',
            'cache-control': 'max-age = 0',
            'origin': 'https://login.taobao.com',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'referer': 'https://login.taobao.com/member/login.jhtml?spm=a21bo.2017.754894437.1.5af911d9KVp31G&f=top&redirectURL=https%3A%2F%2Fwww.taobao.com%2F'
        }
        # 登录taobao.com提交的数据
        verify_password_data = {
            'TPL_username': self.username,
            'ncoToken': '611a693413adab5bba8d7cd57099a2b79824862f',
            'slideCodeShow': 'false',
            'useMobile': 'false',
            'lang': 'zh_CN',
            'loginsite': 0,
            'newlogin': 0,
            'TPL_redirect_url': 'https://www.taobao.com/',
            'from': 'tbTop',
            'fc': 'default',
            'style': 'default',
            'keyLogin': 'false',
            'qrLogin': 'true',
            'newMini': 'false',
            'newMini2': 'false',
            'loginType': '3',
            'gvfdcname': '10',
            'gvfdcre': '68747470733A2F2F7777772E74616F62616F2E636F6D2F',
            'TPL_password_2': self.TPL_password2,
            'loginASR': '1',
            'loginASRSuc': '1',
            'oslanguage': 'zh - CN',
            'sr': '1920 * 1080',
            'naviVer': 'chrome | 78.03904108',
            'osACN': 'Mozilla',
            'osAV': '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'osPF': 'win32',
            'appkey': '00000000',
            'mobileLoginLink': 'https://login.taobao.com/member/login.jhtml?spm=a21bo.2017.754894437.1.5af911d9lDPMz1&f=top&redirectURL=https://www.taobao.com/&useMobile=true',
            'showAssistantLink': '',
            'um_token': 'T72DBC8493ABBADB88213AA06817EC3BB7B92BF54723EBD3307820CBDC9',
            'ua': self.ua
        }
        try:
            resp = self.session.post(self.verify_password_url, headers=verify_password_headers, data=verify_password_data, timeout=self.timeout)
            resp.raise_for_status()
            # 提取st码地址
            st_token_url = re.search(r'<script src="(.*?)"></script>', resp.text).group(1)
        except Exception as e:
            print('验证用户名和密码请求失败，原因：{}'.format(e))
            return None
        # 提取成功返回
        if st_token_url:
            print('验证用户名和密码请求成功，st码申请地址：{}'.format(st_token_url))
            return st_token_url
        else:
            print('用户名验证失败，请更换data参数')
            return None


    def apply_st(self):
        """
        申请st码
        :return: st码
        """
        apply_st_url = self.verify_password()
        try:
            st_resp = self.session.get(apply_st_url)
            # print(st_resp.text)
        except Exception as e:
            print('申请st码失败，原因：')
            raise e
        st_match = re.search(r'{"code":200,"data":{"st":"(.*?)"}}', st_resp.text)
        if st_match:
            print('获取st码成功, st码：{}'.format(st_match.group(1)))
            return st_match.group(1)
        else:
            raise RuntimeError('获取st码失败')



    def _load_cookies(self):
        """
        检查cookies
        :return:True or False
        """
        # 1.判断cookies序列化文件是否存在
        if not os.path.exists(COOKIES_FILE_PATH):
            return False
        # 2.加载cookies
        self.session.cookies = self._deserialization_cookies()
        # 3.判断cookies是否过期
        try:
            self.get_taobao_nick_name()
        except Exception as e:
            os.remove(COOKIES_FILE_PATH)
            print('cookies过期，删除cookies文件')
            return False
        print('加载淘宝cookies成功')
        return True


    def _serialization_cookies(self):
        """
        保存cookies,将cookies序列化
        :return:cookies
        """
        cookies_dic = requests.utils.dict_from_cookiejar(self.session.cookies)
        with open(COOKIES_FILE_PATH, 'w+', encoding='utf-8') as file:
            json.dump(cookies_dic, file)


    def _deserialization_cookies(self):
        """
        读取cookies,反序列化
        :return:
        """
        with open(COOKIES_FILE_PATH, 'r+', encoding='utf-8') as file:
            cookies_dict = json.load(file)
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            return cookies


    def get_taobao_nick_name(self):
        """
        获取淘宝昵称
        :return:昵称
        """
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        try:
            resp = self.session.get(self.my_taobao_url, headers = headers)
            resp.raise_for_status()
        except Exception as e:
            print('获取淘宝主页失败，原因：')
            raise e
        # 获取淘宝昵称
        nick_name_match = re.search(r'<input id="mtb-nickname" type="hidden" value="(.*?)"/>', resp.text)
        if nick_name_match:
            print('congratulation for your success:{}'.format(nick_name_match.group(1)))
            return nick_name_match.group(1)
        else:
            raise RuntimeError('获取淘宝昵称失败，原因：{}'.format(resp.text))


    def login(self):
        """
        使用st码登录
        :return:淘宝主页链接
        """
        print("开始模拟登录淘宝.......")
        # 加载cookies文件
        if self._load_cookies():
            return True
        # 判断是否需要滑块
        self._nick_check()
        st = self.apply_st()
        headers = {
            'host': 'login.taobao.com',
            'connection': 'keep-Alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        try:
            response = self.session.get(self.vst_url.format(st), headers=headers)
            response.raise_for_status()
        except Exception as e:
            print('st登录请求失败，原因：')
            raise e
        # 登录成功，跳转淘宝主页链接
        # print(response.text)
        my_taobao_match = re.search(r'top.location.href = "(.*?)"', response.text)
        if my_taobao_match:
            print('淘宝登录成功，跳转链接{}'.format(my_taobao_match.group(1)))
            self._serialization_cookies()
            self.get_taobao_nick_name()
            return True
        else:
            raise RuntimeError('登录失败！response:{}'.format(response.text))

if __name__ == '__main__':
    s = requests.session()
    mytaobao = UsernameLogin(s)
    mytaobao.login()



































