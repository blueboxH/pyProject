''' 对requests的session的封装 '''

import time
from functools import wraps
from random import uniform

import requests
from fake_useragent import UserAgent

from myTool.Mproxy import Mproxy
from myTool.Pcolor import print_green

try:
    # config 应该在执行脚本执行的同级目录中
    from config import HEADERS
except ImportError:
    HEADERS = None
try:
    from config import IS_USE_PROXY
    try:
        from config import PROXY_COL_NAME
    except ImportError:
        PROXY_COL_NAME = None
except ImportError:
    IS_USE_PROXY = False
    PROXY_COL_NAME = None


class MsessionReq:
    ''' 对requests.session()的简单装饰

        通过配置文件和参数对session请求的前后进行处理, 若什么都没有设置, 就相当于对session进行简单的异常处理, 若想实现和config 设置不一样的, 可以传入实例变量
        headers, proxy_col_name, my_proxy 覆盖类变量, 方法变量覆盖实例变量

        HEADERS : 决定是否带头部信息->通过配置文件设置类的headers属性, 无则不带, 若要覆盖使用headers 初始化对象
        IS_USE_PROXY : 决定是否使用代理->配置文件设置是否使用代理 True/False, 若要覆盖使用use_proxy
        PROXY_COL_NAME : 决定代理是否存储到数据库->存储有效代理信息的mongo集合名  name/None, 若要覆盖使用proxy_col_name
        usercookies : 决定是否登陆->登陆信息, 无则不登录
        validate : 决定是否验证->处理验证码并对MsessionReq实例进行修改,使其通过验证, 返回必要数据以便保存,
        >>>validate(referer_url:跳转到错误页面的页面, self:MsessionReq实例) -> {'is_continue': True/False, 'result':None/{'cookies':...,'headers':...}}
        'is_continue' 若为False, 则一个生命周期只验证一次, 'result'为None则表示验证失败
    '''

    headers = HEADERS
    # 表名
    proxy_col_name = PROXY_COL_NAME
    # Mproxy 代理工具类的实例化对象
    use_proxy = IS_USE_PROXY

    __is_validate = True

    def __init__(self, validate=None, usercookies=None, **kw):
        ''' 对必要的身份信息初始化, 甚至可以传入is_get_right_page 方法覆盖 '''
        self.params_tuple = (validate, usercookies)
        self.params_dict = dict(**kw)
        if len(kw) != 0:
            # 若想实现和config 设置不一样的, 可以在这里进行覆盖
            # 主要是覆盖headers, proxy_col_name, use_proxy
            for key, value in kw.items():
                self.__setattr__(key, value)

        self.session = requests.Session()
        # header
        if self.headers is not None:
            self.session.headers.update(self.headers)
        else:
            self.session.headers.update({'User-Agent': UserAgent().random})

        # proxy info
        if self.use_proxy:
            # 取到的代理信息
            self.my_proxy = Mproxy(self.proxy_col_name)
            self.proxy_info = self.my_proxy.proxy
            if self.proxy_col_name is not None:
                # proxy_col_name 不为空则从数据库提取
                cookie_ = self.proxy_info.get('cookies')
                header_ = self.proxy_info.get('headers')
                if header_ is not None:
                    self.session.headers.update(header_)
                if cookie_ is not None:
                    self.session.cookies.update(cookie_)
            self.session.proxies = self.proxy_info.get('proxy')

        self.validate = validate
        # 登陆了之后把self.usercookies 改为False, 避免二次登陆
        self.usercookies = usercookies

    def preprocessor(func):
        @wraps(func)
        def get_resp_wrapper(self, url, is_login='behind', retry=5, is_sleep=True, validate=None, **kwargs):
            ''' 对用session各种请求得到的结果进行预处理

            如: 请求页面是否需要登陆, 什么时候登陆, 错误处理, 是否处理验证码
            is_login : 'behind'-> 请求后登陆/'before'-> 请求前登陆/None-> 不登录, 优先级高于对象
            validate : None-> 调用对象的self.validate/False -> 优先级高于对象, 禁止验证/function -> 执行这个传入的validate
            retry : int 出错后重试次数
            is_sleep : 返回前是否sleep
            kwargs : 全部传入后续session请求
            '''
            if retry < 0:
                print_green('错误次数太多, 重新实例化并执行')
                return get_resp_wrapper(MsessionReq(*self.params_tuple, **self.params_dict), url, is_login=is_login, validate=validate, **kwargs)
            try:
                if is_login == 'before':
                    self.login()

                self.response = func(self, url, **kwargs)

                if self.is_get_right_page() is False:
                    print_green('302码, 代理被封:',
                                self.session.proxies['http'])
                    referer_url = self.response.history[0].url
                    self.session.headers.update({'Referer': referer_url})

                    if validate is not None:
                        # 方法
                        if validate is False:
                            self.__is_validate = False
                        else:
                            __validate = validate
                    else:
                        # 对象
                        if self.validate is None:
                            self.__is_validate = False
                        else:
                            __validate = self.validate

                    if self.__is_validate is True:
                        # 解决验证码
                        results = __validate(referer_url, self)

                        if results['is_continue'] is False:
                            MsessionReq.__is_validate = False

                        if results['result'] is not None:

                            self.proxy_info.update(results['result'])
                            # 重新请求链接
                            return get_resp_wrapper(self, url, is_login=is_login, validate=validate, **kwargs)

                    print_green('验证失败, 重新实例化并执行')
                    return get_resp_wrapper(MsessionReq(*self.params_tuple, **self.params_dict), url, is_login=is_login, validate=validate, **kwargs)

                # 成功获取页面
                if is_login == 'behind':
                    self.login()

                self.session.headers.update({'Referer': self.response.url})

                if is_sleep:
                    #在每次成功返回之前随机等待, 避免失败时的等待
                    time.sleep(uniform(1, 7))
                    print_green('succeed 正在使用代理:',
                                self.proxy_info['proxy']['http'])

                return self.response
            except Exception as err:
                print_green('get_resp_wrapper出错啦', err)
                # 不重新实例化, 传入原来self, 重新执行 preprocessor
                return get_resp_wrapper(self, url, is_login=is_login, retry=retry - 1, validate=validate, **kwargs)
        return get_resp_wrapper

    def is_get_right_page(self):
        ''' 判断是否获得正确页面, 若需要可重写
            这里默认你的链接指向页面就是你的目标页面, 故跳转即失败
        '''
        try:
            self.response.raise_for_status()
            if len(self.response.history) > 0:
                if self.response.history[0].status_code == 302:
                    return False
            return True
        except Exception as err:
            print_green('判断是否获得正确页面出错啦', err)
            return False

    def login(self):
        ''' 判断是否登陆以及登陆 '''
        try:
            # 有usercookies 且没有登陆信息
            if self.usercookies not in (None, False):
                print_green('登陆...')
                self.session.cookies.update(self.usercookies)
                self.usercookies = False
        except Exception as err:
            print_green('登陆出错啦', err)

    @preprocessor
    def get(self, url, **kwargs):
        return self.session.get(url, timeout=10, **kwargs)

    @preprocessor
    def post(self, url, **kwargs):
        return self.session.post(url, timeout=10, **kwargs)

    @preprocessor
    def head(self, url, **kwargs):
        return self.session.head(url, timeout=10, **kwargs)

    def __del__(self):
        if self.proxy_col_name is not None:
            if self.is_get_right_page() is True:
                self.my_proxy.save_proxy2mongo(self.proxy_info)


if __name__ == '__main__':
    myses = MsessionReq()

    res = myses.get('http://ip.cn')
    print(res.text)
