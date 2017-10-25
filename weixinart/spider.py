''' 模拟登陆+切换代理爬搜狗微信文章
    这是第一次结果, 用闭包的方法传递session
    代理永远在代理池里面取
    还没写完, 直接转到pro
'''
import os
import time
import pymongo
from random import uniform
import requests
from pyquery import PyQuery as pq
from requests.exceptions import RequestException

from config import *
from myTool.Pcolor import print_red

# 以后指向获取返回体的函数
get_response = None
client = pymongo.MongoClient()
db = client.wechat_article_db
article_col = db.article_col

#是否验证验证码
WHETHER_VALIDATE = True
#是否登陆
WHETHER_LOGIN = False

def get_proxies():
    ''' 获取到一个有效代理, 不需要再对返回的值进行判断'''
    try:
        resp = requests.get(PROXY_GETED_API)
        resp.raise_for_status
        if len(resp.text.split(':')) == 2:
            print('获取到有效代理: --', resp.text)
            return {
                'http': 'http://' + resp.text,
                'https': 'http://' + resp.text,
            }
        print_red('获取到无效代理', resp.text)
        return get_proxies()
    except:
        print_red('获取代理失败', resp.text)
        return get_proxies()


def validate(referer_url, err_count=1):
    ''' 输入验证码 '''

    print_red('开始验证..')
    if err_count == 5:
        print_red('验证次数太多, 重置代理')
        return False
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
            'login': 1 if WHETHER_LOGIN is True else 0
        }
        # 带上 SUV 必要cookie
        get_response(VALIDATE_SUV_URL, suv_params)

        params = {
            'tc': round(time.time() * 1000)
        }
        # 获取验证码图片
        resp = get_response(VALIDATE_IMG_URL, params)
        with open(IMG_FILE_NAME, 'wb') as img:
            img.write(resp.content)
        os.startfile(IMG_FILE_NAME)

        validate_code = input('请输入验证码:')

        if validate_code is '':
            print_red('刷新验证码~~')
            validate(referer_url)

        data = {
            'c': validate_code,
            'r': '/' + referer_url.split('/')[-1],
            'v': '5'
        }
        # 上传验证码
        response = get_response(VALIDATE_POST_URL, data=data, method='post')
        response.encoding = 'utf-8'
        if response.json().get('code') == 0:
            print_red('验证通过')
            return {'SNUID': response.json().get('id')}
        else:
            print_red('验证失败, 重新验证')
            return validate(referer_url, err_count + 1)
    except Exception as err:
        print_red('验证失败', err)
        return validate(referer_url, err_count + 1)


def set_session():
    ''' 获取session对象 '''
    with requests.Session() as session:
        session.headers.update(HEADERS)
        session.proxies = get_proxies()
        print_red('重置session对象')

        def get_resp(base_url, params=None, data=None, err_count=1, method='get', timeout=12.3):
            ''' 获得网页返回对象 '''
            print(err_count)
            if err_count == 5:
                print_red('错误次数太多, 重置代理')
                return set_response()(base_url, params)
            try:
                resp = session.request(
                    method=method, url=base_url, params=params, data=data, timeout=timeout)
                resp.raise_for_status()

                if len(resp.history) > 0:
                    if resp.url.split('/')[-2] == 'antispider':
                        # 经过了跳转, 且跳转后的页面为反爬页面, 表面代理被封
                        print_red('302码, 代理被封:', session.proxies['http'])
                        referer_url = resp.history[0].url
                        session.headers.update({'Referer': referer_url})
                        if WHETHER_VALIDATE is True:
                            # 解决验证码
                            result = validate(referer_url)
                            if result is not False:
                                session.cookies.update(result)
                                return get_response(base_url, params)

                        return set_response()(base_url, params)

                # 没有跳转, 或者跳转之后的页面不是反爬页面, 表示成功获取页面
                if base_url.split('/')[-1] == 'weixin':
                    session.headers.update({'Referer': resp.url})
                    if WHETHER_LOGIN is True and session.cookies.get(list(USERCOOKIE.keys())[0]) is None:
                        # 当只有账号的 cookie 时会报错, 所有写在带上别的cookie 之后
                        print_red('登陆...')
                        session.cookies.update(USERCOOKIE)
                    print_red('succeed 正在使用代理:', session.proxies['http'])

                    #在每次成功返回之前随机等待, 避免失败时的等待
                    time.sleep(uniform(1, 5))

                return resp
            except RequestException as err:
                print_red('获取页面内容出错', err)
                return get_resp(base_url, params, err_count + 1)
            except Exception as err:
                print_red('获取页面内容出错~~~', err)
                return get_resp(base_url, params, err_count + 1)
        return get_resp


def set_response():
    ''' 把新的 get_resp 函数赋给 get_response
    这个函数的目的是为了使 get_response 永远和最新的 get_resp 的值相同
    解决 get_response 一直指向第一次 get_resp 内存位置的问题
    '''
    global get_response
    get_response = set_session()
    return get_response


def parse_index_page(html):
    ''' 解析索引页 '''
    try:
        doc = pq(html)
        a_list = doc.items('a[id^="sogou_vr_11002601_title_"]')
        return [item.attr('href') for item in a_list]
    except Exception as err:
        print('解析索引页出错啦', err)


def parse_detail_page(html):
    ''' 解析详情页 '''
    try:
        doc = pq(html, parser='html')
        title = doc('#activity-name').text()
        post_time = doc('#post-date').text()
        wechat_name = doc('#post-user').text()
        wechat_ID = doc('p .profile_meta span').eq(0).text()
        wechat_desc = doc('p .profile_meta span').eq(1).text()
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


def save2mongo(data):
    ''' 储存单条数据 '''
    try:
        res = article_col.insert_one(data)
        return res.inserted_id
    except Exception as err:
        print_red('储存单条数据出错啦', err)

def main(page_num):
    # 对 get_response 函数进行初始化
    set_response()

    base_url = 'http://weixin.sogou.com/weixin'
    params = {
        'query': KEYWORD,
        's_from': 'input',
        'type': '2',
        'page': page_num,
        'ie': 'utf8',
        '_sug_type_': '0',
        '_sug_': 'n'
    }
    html = get_response(base_url, params).text
    results = parse_index_page(html)

    if results:
        for detail_url in results:
            detail_html = get_response(detail_url).text
            detail_data = parse_detail_page(detail_html)
            save2mongo(detail_data)


if __name__ == '__main__':
    # for x in range(1, 14):
    #     print(x, 'ci')
    #     main(x)
    main(1)
