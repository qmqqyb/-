import json
import os
import pandas as pd
import requests
import re
import pymysql
from fake_useragent import UserAgent
from retrying import retry
import random
import time
from sqlalchemy import create_engine
import numpy as np

pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 5000)
pd.set_option('max_colwidth', 30)
pd.set_option('display.width', 1000)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)


# 淘宝标签excel文件保存路径
#标签类
class CommentTag():
    """
    定义一个获取标签的类
    """
    def __init__(self, itemid, interval):
        # 随机的创建一个user_agent
        self.ua = UserAgent().random
        # 请求的url地址
        self.url = "https://rate.tmall.com/listTagClouds.htm"
        # 请求来源地址
        self.referer = "https://detail.tmall.com/item.htm"
        # 请求间隔时间
        self.interval = interval
        # 请求的商品id
        self.itemid = itemid
        # 请求的cookie信息
        self.cookie = "cookie2=16450e96b87635edd21c8c23098ee16e; _tb_token_=59bb309e37883; tk_trace=oTRxOWSBNwn9dPyorMJE%2FoPdY8zfvmw%2Fq5hmBNkq3fFfIkz%2Bp6pXJBhANegSkYg0Wj02rNZ1LnIJvPe3YgKDlSp%2FnhwFeZ7ejyQD7SYAlQOWOCqN9%2B4JkUeTRl7IyIE%2FVvkyBxwiUrhAHNzSqJ1VeRZVtFE%2FVoKDslCc8HsIcY%2FsoW%2F240wjdFDLyOM3qy22dIAuyyPLbWLwjsGnKdK0qpw9frUbJH1LVOtqrnNcCQWZ21BxMnDGemJf%2Fxz203DVQ%2BSceixTKAPkJFjdNiGoBM%2B7Jw%3D%3D; _samesite_flag_=true; t=eb7e3e377ddf3017ed7bdbd075f22c82; thw=cn; hng=CN%7Czh-CN%7CCNY%7C156; _m_h5_tk=256c7a4c3468f9cf9ab3976cb0f4777e_1582207720076; _m_h5_tk_enc=2279a5391e7ea76e0d32ea71c347c240; mt=ci=0_0; cna=b5WFFR2YV0YCAdNHHAf7KxeS; v=0; enc=2R%2B5LqoA59X5sQMuom5oGltHQ1Avsy57fn5U9BYgqWR1i82dfH0Gia4i6IZGooYayZfUDlgP%2BR8dv%2Fi0MrOFvQ%3D%3D; tfstk=cFbFBnvIRyUUlrZNmETyF7L1TbLda0xk0VRJxixIPV7qFjvM3s4neC4LvCRvHPxh.; uc1=cookie14=UoTUOLFGSn0wIg%3D%3D; x5sec=7b22726174656d616e616765723b32223a22396335373865633339326533656362383064316566633232356638636439626143504771762f4946454b6174716365792b7450616967453d227d; l=dBgUhRSmqK_SOAQaBOfgqRyY8y_OFIOfGsPr79hg4ICPOYCkMAlCWZVhQmYDCnGV3savR3J6m7-0BqLaDyUIhEGfIqlBs2JNxdTpR; isg=BGJi0-ZvSPKdiVdlhfToL2hZs-jEs2bNvI1vIaz6oFX1fwb5lEB53W65q7uD795l"
        # 数据库的密码
        self.password = '38057674'
        # 数据库名称
        self.database = 'taobao'
        # 保存的文件名称
        self.sheetname = 'commenttag'

    def get_params(self):
        """
        请求的参数信息
        """
        params = {
        "itemId": self.itemid,
        "isAll": "true",
        "isInner": "true"
        }
        return params

    def get_header(self):
        """
        请求的头信息
        """
        header = {
            "cookie": self.cookie,
            "referer": self.referer,
            "user-agent": self.ua,
            }
        return header

    def timesleep(self):
        """
        随机选择间隔时间，避开某宝的反爬机制
        :return:
        """
        sleeptime_one = random.uniform(self.interval-5, self.interval) # random.uniform(x, y)表示随机生产一个介于x, y之间的数，包括x, 不包括y
        sleeptime_two = random.uniform(self.interval-2, self.interval+3)
        sleeptime_list = [sleeptime_one, sleeptime_two]
        sleeptime = random.choice(sleeptime_list)
        print('sleeping ', str(sleeptime), 'seconds...')
        time.sleep(sleeptime)

    @retry(stop_max_attempt_number=5)
    def get_tag_info(self):
        """
        获取商品的评论标签信息
        """
        params = self.get_params()
        header = self.get_header()
        try:
            response = requests.get(self.url, params=params, headers=header, timeout=12)
            tag_match = re.search('\((.*?)}}\)', response.text)
            tag_str = tag_match.group(1) + '}}'
            result = json.loads(tag_str)
            # for i in range(0, len(result['tags']['tagClouds'])):
            #     print(result['tags']['tagClouds'][i]['tag'], result['tags']['tagClouds'][i]['count'])
            if result:
                return result['tags']['tagClouds']
            else:
                return False
        except Exception as e:
            print('getinfo错误原因：', e)
            return False



    def _save_mysql(self):
        """
        将json格式的数据转化后保存到mysql数据库中
        :return:
        """
        # 创建mysql数据库连接
        engine = create_engine("mysql+pymysql://{}:{}@{}/{}?charset={}".format('root', self.password, 'localhost', self.database,'utf8'))
        # 创建链接
        conn = engine.connect()
        # 获得数据
        tag_list = self.get_tag_info()
        tag_df = pd.DataFrame(tag_list)
        tag_df['itemid'] = self.itemid
        print(tag_df)
        # cols = df['tag'].tolist()
        # tag_df = pd.DataFrame([np.array(df['count'])], columns=cols)
        # tag_df['itemid'] = self.itemid
        # print(tag_df)
        # 存入数据
        tag_df.to_sql(name=self.sheetname, con=conn, if_exists='append', index=False)

if __name__ == '__main__':
    itemid = '612646625588'
    co_tag = CommentTag(itemid, 8)
    co_tag._save_mysql()
    co_tag.timesleep()
