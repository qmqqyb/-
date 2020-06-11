from urllib import parse
import re
import os
import pandas as pd
import time
from sqlalchemy import create_engine
import json
import requests
import random
from login import UsernameLogin
from retrying import retry
from queue import Queue

# cookies序列化文件
COOKIES_FILE_PATH = 'taobao_login_cookies.txt'
# 爬取商品详情的excel文件
GOODS_EXCEL_PATH = 'router_spider_goods.xlsx'
# 关闭警告
requests.packages.urllib3.disable_warnings()


class GoodsSpider():
    """
    爬取淘宝网页的商品的类
    """
    def __init__(self, data, database, password, sheetname, goods_pages, itemid_q1, itemid_q2, sellerid_q):
        # 关键字解析
        self.keyword = parse.urlencode(data)
        # 超时时间
        self.timeout = 15
        # 存放商品id的队列
        self.itemid_q1 = itemid_q1
        # 存放商品id的队列
        self.itemid_q2 = itemid_q2
        # 存放店铺id的队列
        self.sellerid_q = sellerid_q
        # 数据库
        self.database = database
        # 数据库密码
        self.password = password
        # 存入数据库的名字
        self.sheetname = sheetname
        # 爬取的页数
        self.goods_pages = goods_pages
        # 创建一个session对象
        self.s = requests.session()
        # 淘宝登录
        mytaobao = UsernameLogin(self.s)
        mytaobao.login()


    def spider_goods(self, goods_page):
        """
        爬取淘宝商品的方法
        :param page:淘宝商品分页参数
        :return:商品信息的Json字符串
        """
        p = goods_page * 44
        # 搜索链接, q表示关键词，p = page * 44页码标签
        search_url = 'https://s.taobao.com/search?' + str(self.keyword) + '&imgfile=&js=1&stats_click=search_radio_all%3A1&initiative_id=staobaoz_20200329&ie=utf8&bcoffset=3&ntoffset=3&p4ppushleft=1%2C48&s=' + str(p)
        print(search_url)
        # 请求头
        headers = {
            'referer': 'https://s.taobao.com/',
            'user - agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        }
        response = self.s.get(search_url, headers=headers, verify=False, timeout=self.timeout)
        # print(response.text)
        goods_match = re.search(r'g_page_config = {(.*?)}};', response.text).group(1)
        goods_match = '{'+ goods_match + '}}'
        # print(goods_match)
        return goods_match

    @retry(stop_max_attempt_number=5)
    def get_goods_info(self, goods_page):
        """
        解析json格式，并提取商品的标题、价格、商家地址、销量、评价
        :return:商品详情列表
        """
        goods_str = self.spider_goods(goods_page)
        goods_json = json.loads(goods_str)
        goods_items = goods_json['mods']['itemlist']['data']['auctions']
        goods_list = []
        for goods_item in goods_items:
            self.itemid_q1.put(goods_item['nid'])
            self.itemid_q2.put(goods_item['nid'])
            self.sellerid_q.put(goods_item['user_id'])
            goods = {
                'category': goods_item['category'],
                'itemId': goods_item['nid'],
                'sellerId': goods_item['user_id'],
                'title': goods_item['raw_title'],
                'price': goods_item['view_price'],
                'location': goods_item['item_loc'],
                'sales': goods_item['view_sales'],
                'comment_count': goods_item['comment_count'],
                'nick': goods_item['nick'],
                'isTmall': goods_item['shopcard']['isTmall']
            }
            goods_list.append(goods)
        # print(goods_list)
        return goods_list

    def _save_excel(self, goods_page):
        """
        将json根式保存为excel文件
        :param goods_list:商品数据
        :param startrow:数据写入开始行
        :return:
        """
        goods_list = self.get_goods_info(goods_page)
        # pandas没有对excel的数据写入追加模式，只能先读后写
        if os.path.exists(GOODS_EXCEL_PATH):
            df = pd.read_excel(GOODS_EXCEL_PATH)
            df = df.append(goods_list)
        else:
            df = pd.DataFrame(goods_list)
            # print(df)
        writer = pd.ExcelWriter(GOODS_EXCEL_PATH)
        # columns参数用于制定生成的excel中列的顺序
        df.to_excel(excel_writer=writer, columns=['category', 'title', 'price', 'location', 'sales', 'comment_url', 'comment_count', 'user_id'], index=True, encoding='utf-8', sheet_name='router')
        writer.save()
        writer.close()

    def _save_mysql(self, goods_page):
        """
        将json格式的数据转化后保存到mysql数据库中
        :return:
        """
        # 创建mysql数据库连接
        engine = create_engine("mysql+pymysql://{}:{}@{}/{}?charset={}".format('root', self.password, 'localhost', self.database,'utf8'))
        # 创建链接
        conn = engine.connect()
        # 获得数据
        goods_list = self.get_goods_info(goods_page)
        df = pd.DataFrame(goods_list)
        # 存入数据
        if goods_page == 0:
            df.to_sql(name=self.sheetname, con=conn, if_exists='replace', index=False)
        else:
            df.to_sql(name=self.sheetname, con=conn, if_exists='append', index=False)


    def batch_spider_goods(self):
        """
        批量爬取淘宝商品
        :return:
        """
        # 写入数据前先清空之前的数据
        if os.path.exists(GOODS_EXCEL_PATH):
            os.remove(GOODS_EXCEL_PATH)
        # 批量爬取，先爬取3页
        # 大概率会出现滑块验证，不能爬取全部
        for goods_page in range(self.goods_pages):
            print('第%d商品页' % (goods_page + 1))
            # 传入分页参数，循环爬取数据
            try:
                self._save_mysql(goods_page)
                # 时间间隔设置
                time.sleep(random.randint(10, 15))
            except Exception as e:
                print('爬取第' + str(goods_page + 1) + '失败，原因:'.format(e))


if __name__ == '__main__':
    itemid_q1 = Queue()# 用于存放商品的id
    itemid_q2 = Queue()  # 用于存放商品的id
    sellerid_q = Queue()# 用于存放店铺id
    keyword = str(input('Input your keyword:'))
    sheetname = str(input('Input your sheetname:'))
    data = {'q': keyword}
    goods_pages = int(input('请输入你要爬取的页数：'))
    database = str(input('请输入你要存入的数据库名称：'))
    password = str(input('请输入数据库密码：'))
    gs = GoodsSpider(data, database, password, sheetname, goods_pages, itemid_q1, itemid_q2, sellerid_q)
    gs.batch_spider_goods()
