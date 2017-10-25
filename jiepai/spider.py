"""爬取街拍美图 """
import json
import os
import re
import sqlite3
import time

from multiprocessing import pool
from sqlite3 import InterfaceError
from pandas.io.sql import DatabaseError
import pandas
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from _md5 import md5
from config import *


def get_page_contents(url, err, params=''):
    """请求页面内容"""
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return res.text
        return None
    except RequestException as error:
        print(error)
        print(err, url)
        time.sleep(3)
        get_page_contents(url, params, err)


def parse_html_index(html):
    """解析索引页内容"""
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data['data']:
            yield item['article_url']


def download_image(url):
    """传入图片url,下载图片,返回图片路径"""

    try:
        res = requests.get(url)
        if res.status_code == 200:
            image_path = '{0}\\{1}.{2}'.format(
                IMAGE_PATH, md5(res.content).hexdigest(), 'jpg')
            if not os.path.exists(image_path):
                with open(image_path, 'wb') as ima:
                    print("正在下载图片:", url)
                    ima.write(res.content)
                    ima.close()
            else:
                print('图片已下载', url)
            return image_path
    except RequestException as error:
        print(error)
        print('下载图片失败:', url)
        time.sleep(3)
        download_image(url)


def parse_html_detail(html, url):
    """解析详情页内容"""
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.select('title')[0].text
    images_pattern = re.compile('gallery: (.*)siblingList', re.S)
    result = re.search(images_pattern, html)
    if result:
        data = json.loads(result.group(1)[:-6])
        if data and 'sub_images' in data.keys():
            sub_images = data['sub_images']
            images = [item['url'] for item in sub_images]
            return {
                'title': title,
                'url': url,
                'images': images
            }
        return None
    return None


def save_to_db(info):
    ''' 传入一个待储存数据(dic),把这个数据存入数据库 '''
    data_frame = pandas.DataFrame(info)
    try:
        with sqlite3.connect(DB_NAME) as db:
            try:
                res = pandas.read_sql_query(
                    'select `url` from %s' % TABLE_NAME, con=db)

                if info['url'] in res.to_dict()['url'].values():
                    data_frame.to_sql(TABLE_NAME, con=db, if_exists='append')
                    print("详情页存入成功:", info['title'])
                else:
                    print("详情页已存入数据库", info['title'])
            except DatabaseError as error:
                print(error)
                data_frame.to_sql(TABLE_NAME, con=db)
                print("详情页存入成功:", info['title'])
    except InterfaceError as error:
        print(error)
        print("存储数据失败", data_frame)


def main(offset):
    """主函数"""
    print("正在请求第%s页" % offset)
    params = {
        'offset': offset,
        'format': 'json',
        'keyword': KEYWORD,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 3
    }
    index_url = 'http://www.toutiao.com/search_content/'
    index_html = get_page_contents(index_url, '请求索引页出错', params)
    if index_html:
        for url in parse_html_index(index_html):
            details_html = get_page_contents(url, '请求详情页出错')
            print("请求详情页成功", url)
            if details_html:
                info = parse_html_detail(details_html, url)
            if info:
                images_dic = {image_url: download_image(
                    image_url) for image_url in info['images']}
                info["images"] = images_dic
                save_to_db(info)


if __name__ == '__main__':
    input("start:")
    groups_ = [x * 20 for x in range(PAGE_START, PAGE_END + 1)]
    pool_ = pool.Pool()
    pool_.map(main, groups_)
    # main(0)
