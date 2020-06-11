from goods_spider import GoodsSpider
from comments_spider import GoodsComment
from comments_tag_spider import CommentTag
from queue import Queue
import threading
import pandas as pd
import time

def goods_spider(data, database, password, sheetname, goods_pages, itemid_q1, itemid_q2, sellerid_q):
    gs = GoodsSpider(data, database, password, sheetname, goods_pages, itemid_q1, itemid_q2, sellerid_q)
    gs.batch_spider_goods()


def comments_spider(itemid_q1, sellerid_q):
    while True:
        itemid = itemid_q1.get()
        sellerid = sellerid_q.get()
        for j in range(1, 10000):
            print('第', j, '页评论')
            gc = GoodsComment(itemid, sellerid, j, 8)
            gc.save()
            if gc.ifbreak:
                break
            gc.timesleep()

def comments_tag_spider(itemid_q2):
    while True:
        itemid = itemid_q2.get()
        co_tag = CommentTag(itemid, 6)
        co_tag._save_mysql()


def multithreading(data, database, password, sheetname, goods_pages):
    itemid_q1 = Queue()# 用于存放商品的id
    itemid_q2 = Queue()# 用于存放商品的id
    sellerid_q = Queue()# 用于存放店铺id
    t1 = threading.Thread(target=goods_spider, args=(data, database, password, sheetname, goods_pages, itemid_q1, itemid_q2, sellerid_q))
    t1.start()
    # t1.join()
    t2 = threading.Thread(target=comments_spider, args=(itemid_q1, sellerid_q))
    t2.start()
    t3 = threading.Thread(target=comments_tag_spider, args=(itemid_q2, ))
    t3.start()


if __name__ == '__main__':
    keyword = str(input('Input your keyword:'))
    sheetname = str(input('Input your sheetname:'))
    data = {'q': keyword}
    goods_pages = int(input('请输入你要爬取的页数：'))
    database = str(input('请输入你要存入的数据库名称：'))
    password = str(input('请输入数据库密码：'))
    multithreading(data, database, password, sheetname, goods_pages)