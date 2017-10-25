''' 用request爬取淘宝,re解析 '''

import re
import sqlite3

import requests
from requests import RequestException


def get_html(url, query_params):
    ''' get_html '''
    try:
        res = requests.get(url, params=query_params)
        res.raise_for_status()
        res.encoding = res.apparent_encoding
        print(res.url)
        return res.text
    except RequestException as e:
        print('获取页面出错', e)
        return None

def hex_to_chr(string):
    ''' 把一个字符串中的十六进制转换成对应字符  例如:"\\u4e2d" 转换成 "中" 字'''
    try:
        reg = re.compile(r'\\u([0-9a-f]{4})', re.S)
        return reg.sub(lambda x: chr(int(x.group(1), 16)), string)
    except Exception as e:
        print('hex_to_chr出错啦', e)

def parser_page(html):
    ''' 解析页面 '''
    try:
        reg = re.compile(r'","title":"(.*?)",.*?"pic_url":"(.*?)",.*?"detail_url":"(.*?)",.*?"view_price":"([\d\.]*?)",.*?"view_fee":"([\d\.]*?)",.*?"item_loc":"(.*?)",.*?"view_sales":"(\d*?)[\u4e00-\u9fa5]*?",.*?"nick":"(.*?)",', re.S)
        del_reg = re.compile(r'<[\s\w/=]*>')
        matches = reg.finditer(html)
        for match in matches:
            if match:
                product = {
                    "title" : del_reg.sub('', hex_to_chr(match.group(1))),
                    "pic_url" : hex_to_chr(match.group(2)),
                    "detail_url" : hex_to_chr(match.group(3)),
                    "price" : match.group(4),
                    "is_service_free" : '包邮' if match.group(5)== '0.00' else '不包邮',
                    "location" : hex_to_chr(match.group(6)),
                    "deal_cnt" : match.group(7),
                    "shop_name" : hex_to_chr(match.group(8)),
                }
                if save_to_db(product):
                    print('存储成功')
    except Exception as e:
        print('解析页面出错啦', e)


def save_to_db(product):
    ''' 保存数据到数据库 '''
    try:
        with sqlite3.connect('taobao.db') as con:
            cur = con.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS diannao(title TEXT UNIQUE, price REAL, dealCnt INTEGER, isServiceFree TEXT, shopname TEXT, location TEXT, image TEXT, url TEXT)')
            cur.execute("INSERT INTO diannao values (?, ?, ?, ?, ?, ?, ?, ?)", (product['title'], product['price'], product['deal_cnt'], product['is_service_free'], product['shop_name'], product['location'], product['pic_url'], product['detail_url']))
            con.commit()
            if cur.rowcount is not -1:
                return True
            else:
                return False
    except sqlite3.IntegrityError:
        print('数据重复')
        return False
    except Exception as e:
        print('储存到数据库出错啦', e)
        return False

def main(offset):
    ''' main '''
    url = 'https://s.taobao.com/search'
    query_params = {
        'q': '电脑',
        'sort':'sale-desc',
        's': offset,
        # 'imgfile': '',
        # 'commend': 'all',
        # 'ssid': 's5 - e',
        # 'search_type': 'item',
        # 'sourceId': 'tb.index',
        # 'spm': 'a21bo.50862.201856 - taobao - item.1',
        # 'ie': 'utf8',
        # 'initiative_id': 'tbindexz_20170914',
    }
    html = get_html(url, query_params)
    parser_page(html)
    # print(html)

if __name__ == '__main__':
    from multiprocessing import pool
    offsets = [s*44 for s in range(101)]
    pool.Pool(4).map(main, offsets)
