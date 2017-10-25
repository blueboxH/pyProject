''' 代理的处理 '''
import pymongo
import requests

from myTool.setting import PROXY_DB, PROXY_GETED_API
from myTool.Pcolor import print_green


class Mproxy:

    def __init__(self, collection_name=None):
        self.collection_name = collection_name
        if self.collection_name is not None:
            self.client = pymongo.MongoClient()
            self.db = self.client[PROXY_DB]
            self.col = self.db[self.collection_name]

    def save_proxy2mongo(self, data):
        ''' 储存代理及相关信息到mongo
        data = {
            'proxy':{.:.},
            'cookies':{.:.},
            'headers':{.:.}
        }
        '''
        print_green('储存代理')
        try:
            if data.get('proxy') is None:
                raise ValueError('数据格式错误, 没有 proxy 键')
            if self.collection_name is not None:
                result = self.col.insert_one(data)
                return result.inserted_id
        except Exception as err:
            print_green('储存代理出错啦', err)

    @property
    def proxy(self):
        ''' 获取一个有效代理, 不需要再对返回的值进行判断
            传入一个集合名, 如果没有, 那么从代理池获取
        '''
        try:
            test_x = ''
            if self.collection_name is not None:
                test_x = '数据库没有代理,'
                print_green('从数据库获取代理')
                result = self.col.find_one_and_delete({})
                if result is not None:
                    return result

            print_green('%s 从代理池获取代理' % test_x)
            resp = requests.get(PROXY_GETED_API)
            resp.raise_for_status
            if len(resp.text.split(':')) == 2:
                return {'proxy': {
                    'http': 'http://' + resp.text,
                    'https': 'http://' + resp.text
                }}
            return self.proxy
        except Exception as err:
            print_green('获取代理出错啦', err)


    def __del__(self):
        if self.collection_name is not None:
            print_green('关闭代理数据库连接')
            self.client.close()

if __name__ == '__main__':
    pro = Mproxy('weixinart')
    print(pro.save_proxy2mongo({'proxy': 'test'}))
    print(pro.proxy)
