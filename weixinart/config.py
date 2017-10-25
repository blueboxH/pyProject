HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    'Upgrade-Insecure-Requests': '1',
    'Host': 'weixin.sogou.com',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
}
IS_USE_PROXY = True

# 储存有效代理信息的集合名
PROXY_COL_NAME = 'weixinart'
# 文章集合名
ARTICLE_COL_NAME = 'pyspider'
KEYWORD = 'python爬虫'
IMG_FILE_NAME = 'code.png'

USERCOOKIE = {
    'ppinf': '***',
    'pprdig': '***',
    'sgid': '***'
}

PROXY_GETED_API = 'http://localhost:5000/get'

VALIDATE_POST_URL = 'http://weixin.sogou.com/antispider/thank.php'
VALIDATE_IMG_URL = 'http://weixin.sogou.com/antispider/util/seccode.php'
VALIDATE_SUV_URL = 'http://pb.sogou.com/pv.gif'








url_test = 'http://weixin.sogou.com/weixin?query=%E9%85%92%E5%BA%97%E5%8E%A8%E6%88%BF%E6%8E%92%E7%83%9F%E7%AE%A1%E9%81%93&_sug_type_=&s_from=input&_sug_=n&type=2&page=1&ie=utf8'
proxies_test = {'http': 'http://111.13.109.27:80', 'https': 'http://111.13.109.27:80'}
