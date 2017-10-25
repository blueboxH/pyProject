''' 爬取bing背景图片 '''

import json
import re
import sys
import time

import requests

from datetime import date, timedelta
from config import IMGPATH, LASTDAY

base_url = 'https://cn.bing.com/'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
}

def get_html(url, params=None):
    try:
        res = requests.get(url, params=params, headers=headers)
        res.raise_for_status()
        if 'image' in res.headers['Content-Type'].split('/'):
            return res.content
        return res.text
    except Exception as err:
        print('获取页面错误', err)


def get_IID_IG():
    try:
        html = get_html(base_url)
        iid = re.search(r'data-ajaxiid="(\d+?)"', html).group(1)
        ig = re.search(r'IG:"(\w+?)"', html).group(1)
        return 'SERP.'+iid, ig
    except Exception as err:
        print('获取IID, IG 错误', err)


def get_des(current_date, IID, IG, istoday=True):
    ''' eg: current_date=20170924 '''
    try:
        url = base_url+'cnhp/life?'
        params = {
            'intlF': '',
            'IID': IID,
            'IG': IG
        }
        if not istoday:
            params['currentDate'] = current_date
        html = get_html(url, params)
        des = re.search(r'id="hplaSnippet">(.*?)</div>', html).group(1)
        return des
    except Exception as err:
        print('获得详细描述信息出错', err)


def get_img_info(today, lastday):
    try:
        now = round(time.time() * 1000)
        url = base_url + 'HPImageArchive.aspx?'
        num_ = today - lastday
        num = 15 if num_.days >= 16 else num_.days
        params = {
            'format': 'js',
            'idx': 0,
            'n': num,
            'nc': now,
            'pid': 'hp'
        }
        html = get_html(url, params=params)
        images = json.loads(html)['images']
        if num > 8:
            params['idx'] = 7
            params['n'] = num - 7
            html2 = get_html(url, params=params)
            images.extend(json.loads(html2)['images'][1:])
        IID, IG = get_IID_IG()
        for index, img in enumerate(images):
            current_date_ = today - timedelta(index)
            current_date = int(current_date_.strftime('%Y%m%d'))
            if index == 0:
                des = get_des(current_date, IID, IG)
            des = get_des(current_date, IID, IG, False)
            try:
                title = img['copyright']
                name = title.split('，')[0].split()[0]
                enddate = img['enddate']
                url = base_url[:-1] + img['url']
                yield name, title, enddate, url, des
            except Exception as e:
                print('循环获得第 {} 张图片失败'.format(index), e)
    except Exception as err:
        print('获取图片信息失败', err)


def download(img_infoes):
    is_first = True
    for name, title, enddate, url, des in img_infoes:
        try:
            file_name = IMGPATH + name

            with open(file_name+'.jpg', 'wb') as im:
                im.write(get_html(url))
            with open(file_name+'.txt', 'w', encoding='utf-8') as f:
                f.write(title+'\r\n'+des)
            if is_first:
                is_first = False
                with open(sys.path[0]+'\\config.py', encoding='utf-8') as co:
                    lines = co.readlines()
                    for index, x in enumerate(lines):
                        if 'LASTDAY' in x:
                            old = re.search(r'LASTDAY\s?=\s?(\d+)$', x.strip()).group(1)
                            lines[index] = x.replace(old, str(enddate))

                            break
                with open(sys.path[0]+'\\config.py', 'w', encoding='utf-8') as co_:
                    co_.writelines(lines)
            print(name, '下载成功...')
        except Exception as err:
            print('下载出错', err)


def main():
    today = date.today()
    lastday = date(*time.strptime(str(LASTDAY), '%Y%m%d')[:3])
    if today > lastday:
        img_infoes = get_img_info(today, lastday)
        download(img_infoes)
    else:
        print('今日美图已下载')


if __name__ == '__main__':
    main()
