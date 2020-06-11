import pymysql
import json
import requests
from fake_useragent import UserAgent
import time
import random
from retrying import retry
from sqlalchemy import create_engine

#连接数据库
db = pymysql.connect("localhost", "root", "38057674", "taobao", charset='utf8mb4') #编码utf8mb4：存储含表情的评论
cursor = db.cursor()


class GoodsComment():
    """
    定义获取商品评论的类
    """
    def __init__(self, itemid, sellerid, pagenum, interval):
        """
        初始化
        :param pagenum:商品的评论页数
        :param interval:间隔时间
        """
        # 随机的创建user_agent
        self.ua = UserAgent().random
        # 请求地址
        self.url = 'https://rate.taobao.com/feedRateList.htm'
        # 返回的数据格式
        self.callback = "jsonp_tbcrate_reviews_list"
        # 请求的来源
        self.referer = "https://item.taobao.com/item.htm"
        # 请求的cookie信息
        self.cookie = "cookie2=16450e96b87635edd21c8c23098ee16e; _tb_token_=59bb309e37883; tk_trace=oTRxOWSBNwn9dPyorMJE%2FoPdY8zfvmw%2Fq5hmBNkq3fFfIkz%2Bp6pXJBhANegSkYg0Wj02rNZ1LnIJvPe3YgKDlSp%2FnhwFeZ7ejyQD7SYAlQOWOCqN9%2B4JkUeTRl7IyIE%2FVvkyBxwiUrhAHNzSqJ1VeRZVtFE%2FVoKDslCc8HsIcY%2FsoW%2F240wjdFDLyOM3qy22dIAuyyPLbWLwjsGnKdK0qpw9frUbJH1LVOtqrnNcCQWZ21BxMnDGemJf%2Fxz203DVQ%2BSceixTKAPkJFjdNiGoBM%2B7Jw%3D%3D; _samesite_flag_=true; t=eb7e3e377ddf3017ed7bdbd075f22c82; thw=cn; hng=CN%7Czh-CN%7CCNY%7C156; _m_h5_tk=256c7a4c3468f9cf9ab3976cb0f4777e_1582207720076; _m_h5_tk_enc=2279a5391e7ea76e0d32ea71c347c240; mt=ci=0_0; cna=b5WFFR2YV0YCAdNHHAf7KxeS; v=0; enc=2R%2B5LqoA59X5sQMuom5oGltHQ1Avsy57fn5U9BYgqWR1i82dfH0Gia4i6IZGooYayZfUDlgP%2BR8dv%2Fi0MrOFvQ%3D%3D; tfstk=cFbFBnvIRyUUlrZNmETyF7L1TbLda0xk0VRJxixIPV7qFjvM3s4neC4LvCRvHPxh.; uc1=cookie14=UoTUOLFGSn0wIg%3D%3D; x5sec=7b22726174656d616e616765723b32223a22396335373865633339326533656362383064316566633232356638636439626143504771762f4946454b6174716365792b7450616967453d227d; l=dBgUhRSmqK_SOAQaBOfgqRyY8y_OFIOfGsPr79hg4ICPOYCkMAlCWZVhQmYDCnGV3savR3J6m7-0BqLaDyUIhEGfIqlBs2JNxdTpR; isg=BGJi0-ZvSPKdiVdlhfToL2hZs-jEs2bNvI1vIaz6oFX1fwb5lEB53W65q7uD795l"
        # 评论的页码数量
        self.pagenum = pagenum
        # 请求的间隔时间
        self.interval = int(interval)
        # 商品id信息
        self.itemid = itemid
        # 店铺的id信息
        self.sellerid = sellerid
        # 用于结束循环
        self.ifbreak = False

    def get_params(self):
        """
        获取请求的参数
        :return:
        """
        params = {
            "auctionNumId": self.itemid,  #宝贝ID
            "userNumId": self.sellerid,   #店铺ID
            "currentPageNum": self.pagenum ,  #评论页码
            "callback": self.callback,
            "folded" : "0"
            }
        return params

    def get_header(self):
        """
        获取请求头
        :return:
        """
        header = {
            "cookie": self.cookie,
            "referer": self.referer,
            "user-agent": self.ua
            }
        return header

    def timesleep(self):
        """
        随机选择间隔时间，避开某宝的反爬机制
        :return:
        """
        sleeptime_one = random.uniform(self.interval-5, self.interval) # random.uniform(x, y)表示随机生产一个介于x, y之间的数，包括x, 不包括y
        sleeptime_two = random.uniform(self.interval-2, self.interval+3)
        if self.pagenum % 2 == 0:
            sleeptime = sleeptime_two
        else:
            sleeptime = sleeptime_one
        print('sleeping ', str(sleeptime), ' seconds...')
        time.sleep(sleeptime)

    @retry(stop_max_attempt_number=5)
    def getinfo(self):
        """
        获取商品的详情信息
        :return:
        """
        params = self.get_params()
        header = self.get_header()
        try:
            response = requests.get(self.url, params=params, headers=header, timeout=12).content.decode('utf-8')[29:-2]
            result = json.loads(response)
            if len(result['comments']) > 0:
                return (result['comments'])
            else:
                print('没有更多页数')
                return False  #爬完
        except Exception as e:
            print('getinfo错误原因：',e)
            return False


    def save(self):
        """
        将数据存入数据库
        """
        comment = self.getinfo()   #结果可能为 正确信息、FALSE、None
        if comment:
            sql = 'INSERT INTO COMMENT() VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s)'
            for i in range(0, len(comment)):
                try:
                    append = comment[i]['append']
                    reply = comment[i]['reply']
                    if append:
                        append = comment[i]['append']['content'] #追加评论不为空
                    if reply: #回复不为空
                        reply = comment[i]['reply']['content']
                    if comment[i]['content'] == '此用户没有填写评价。':
                        continue
                    cursor.execute(sql, [self.itemid, comment[i]['user']['nick'], comment[i]['date'],comment[i]['content'], comment[i]['rate'], comment[i]['user']['vipLevel'], comment[i]['useful'], reply, append])
                    db.commit()
                except Exception as error:
                    print(i, '：save错误原因：', error)
                    db.rollback()#数据库错误
        else:
            self.ifbreak = True  #getinfo有问题

if __name__ == '__main__':
    itemid = ''
    sellerid = ''
    for j in range(1, 10000):
        print('第', j, '页评论')
        gc = GoodsComment(itemid, sellerid, j, 15)
        gc.save()
        if gc.ifbreak:
            break
        gc.timesleep()

