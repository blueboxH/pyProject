''' 模拟登陆+切换代理爬搜狗微信文章
    第三次改进版, 在类里面全局传递session, 写了个装饰器对普通请求添加功能
    有效代理连同cookie写进mongo
'''
import os
import queue
import threading
import time
from random import uniform

import pymongo
import requests
from pyquery import PyQuery as pq
from requests.exceptions import RequestException

from config import *
from myTool.MsessionReq import MsessionReq
from myTool.Pcolor import print_red


def validate(referer_url, obj, err_count=1):
    ''' 输入验证码 '''

    print_red('开始验证..')
    if err_count == 5:
        print_red('验证次数太多, 重置代理')
        return {'is_continue': True, 'result': None}
    try:
        suv_params = {
            'uigs_productid': 'vs_web',
            'terminal':	'web',
            'vstype':	'weixin',
            'pagetype':	'index',
            'channel':	'index_pc',
            'type':	'weixin_search_pc',
            'uigs_t': round(time.time() * 1000),
            # 'uigs_uuid': 1508335333023009,
            'login': 1 if obj.usercookies is True else 0
        }
        # 带上 SUV 必要cookie
        obj.get(VALIDATE_SUV_URL, params=suv_params, is_sleep=False)

        params = {
            'tc': round(time.time() * 1000)
        }
        # 获取验证码图片
        resp = obj.get(VALIDATE_IMG_URL, params=params, is_sleep=False)
        with open(IMG_FILE_NAME, 'wb') as img:
            img.write(resp.content)
        os.startfile(IMG_FILE_NAME)

        validate_code = input('请输入验证码:')

        if validate_code is '':
            print_red('刷新验证码~~')
            validate(referer_url, obj)

        data = {
            'c': validate_code,
            'r': '/' + referer_url.split('/')[-1],
            'v': '5'
        }
        # 上传验证码
        response = obj.post(VALIDATE_POST_URL, data=data, is_sleep=False)
        response.encoding = 'utf-8'
        if response.json().get('code') == 0:
            print_red('验证通过')
            snuid = response.json().get('id')
            obj.session.cookies.update({'SNUID': snuid})
            return {
                'is_continue': True,
                'result': {
                    'cookies':
                        {'SNUID': snuid,
                         'SUV': obj.session.cookies.get('SUV')}
                }
            }
        else:
            print_red('验证失败, 重新验证')
            return validate(referer_url, obj, err_count + 1)
    except Exception as err:
        print_red('验证失败', err)
        return validate(referer_url, obj, err_count + 1)


def parse_index_page(html, page_num):
    ''' 解析索引页 '''
    try:
        doc = pq(html)
        a_list = doc.items('a[id^="sogou_vr_11002601_title_"]')
        page = doc('#pagebar_container > span').text()
        if page == str(page_num):
            return [item.attr('href') for item in a_list]
        return False
    except Exception as err:
        print('解析索引页出错啦', err)


def parse_detail_page(html):
    ''' 解析详情页 '''
    try:
        # js_profile_qrcode > div > p:nth-last-child(2) > span

        doc = pq(html, parser='html')
        title = doc('#activity-name').text()
        post_time = doc('#post-date').text()
        wechat_name = doc('#post-user').text()
        wechat_ID = doc(
            '#js_profile_qrcode > div > p:nth-last-child(2) > span').text()
        wechat_desc = doc(
            '#js_profile_qrcode > div > p:nth-last-child(1) > span').text()
        img_urls = doc('#js_content img').map(
            lambda i, e: pq(e).attr('data-src'))[1:]
        article_html = doc('#js_content').outer_html()
        article_content = doc('#js_content').text()
        return {
            'title': title,
            'time': post_time,
            'wechat_name': wechat_name,
            'wechat_ID': wechat_ID,
            'wechat_desc': wechat_desc,
            'img_urls': img_urls,
            'article_html': article_html,
            'article_content': article_content,
        }
    except Exception as err:
        print('解析详情页出错啦', err)


def save_art2mongo(article_col, data):
    ''' 储存单条数据 '''
    try:
        res = article_col.insert_one(data)
        return res.inserted_id
    except Exception as err:
        print_red('储存数据出错啦', err)


def put_link(link_que, page_range):
    ''' 把详情页链接加入队列

    page_range: tuple 爬取页码的范围
    '''
    base_url = 'http://weixin.sogou.com/weixin'
    # sessionReq = MsessionReq(validate=validate, usercookies=USERCOOKIE)
    sessionReq = MsessionReq(validate=validate)
    try:
        for page_num in range(*page_range):
            st = time.time()

            params = {
                'query': KEYWORD,
                's_from': 'input',
                'type': '2',
                'page': page_num,
                'ie': 'utf8',
                '_sug_type_': '0',
                '_sug_': 'n'
            }
            html = sessionReq.get(base_url, params=params).text
            links = parse_index_page(html, page_num)
            if links is False:
                break
            if links:
                for link in links:
                    if link is not None and not link_que.full():
                        link_que.put(link)

                end = time.time()
                print_red('详情页 %s 加入队列, 用时>> %.2f' % (page_num, end - st))
            else:
                print_red('空详情页')
    except Exception as err:
        print_red('详情页链接加入队列出错啦', err)


def get_link(link_que):
    ''' 获取详情页内容并放入详情页队列 '''
    try:
        sessionReq = MsessionReq(proxy_col_name=None)
        with pymongo.MongoClient() as client:
            db = client.wechat_article_db
            article_col_name = ARTICLE_COL_NAME
            article_col = db[article_col_name]
            while True:
                st = time.time()

                link = link_que.get()
                if link is None:
                    break
                detail_html = sessionReq.get(link).text
                detail_data = parse_detail_page(detail_html)
                if detail_data:
                    detail_data.update({'url': link})
                    save_art2mongo(article_col, detail_data)
                thread_name = threading.current_thread().name

                end = time.time()
                print_red('剩余 %s 页>> %s 获取详情页用时>> %.2f' %
                          (link_que.qsize(), thread_name, end - st))
                link_que.task_done()
    except Exception as err:
        print_red('获取详情页出错啦', err)


def run(customer_num, page_range=(1, 101)):
    ''' customer_num: 消费者线程数
        page_range: 索引页范围
    '''
    start_time = time.time()
    link_que = queue.Queue(60)

    customers = []
    for x in range(customer_num):
        customer = threading.Thread(target=get_link, args=(link_que,))
        customers.append(customer)
        customer.start()

    put_link(link_que, page_range)

    link_que.join()
    print_red('任务全部完成_>_ _>_')

    for y in range(customer_num):
        link_que.put(None)

    for customer in customers:
        customer.join()
    end_time = time.time()
    print_red('cost %.2f seccond' % (end_time - start_time,))


if __name__ == '__main__':
    run(7, page_range=(1, 2))
