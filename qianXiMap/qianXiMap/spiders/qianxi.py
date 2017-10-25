# -*- coding: utf-8 -*-
import json
import time
from datetime import date, timedelta
from qianXiMap.items import QianximapItem
import scrapy
import hashlib


class QianxiSpider(scrapy.Spider):
    name = "qianxi"
    # allowed_domains = ["heat.qq.com"]
    f_url = 'https://lbs.gtimg.com/maplbs/qianxi/'
    l_url = '.js?callback=JSONP_LOADER&_=%s' % str(round(time.time() * 1000))
    yesterday = (date.today() - timedelta(1)).strftime('%Y%m%d')
    dates = []
    start_urls = ['https://heat.qq.com/qianxi/js/data/city.js']

    def __init__(self, start_date=None, end_date=None, *args, **kwargs):
        super(QianxiSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date if start_date is None else date(
            *time.strptime(start_date, '%Y%m%d')[:3])
        self.end_date = date.today() - timedelta(1) if end_date is None else date(
            *time.strptime(end_date, '%Y%m%d')[:3])

    def get_dates(self):
        if self.start_date is not None:
            while self.start_date <= self.end_date:
                self.dates.append(self.start_date.strftime('%Y%m%d'))
                self.start_date = self.start_date + timedelta(1)
        else:
            self.dates.append(self.yesterday)

    def parse(self, response):
        if response.status == 200:
            cities = json.loads(response.text[7:-2])
            self.get_dates()
            for date_ in self.dates:
                index = 0
                s_date = '00000000' if date_ == self.yesterday else date_
                for c_name, c_info in cities.items():
                    try:
                        in_url = self.f_url + s_date + \
                            '/' + str(c_info[2]) + '06' + self.l_url
                        out_url = self.f_url + s_date + \
                            '/' + str(c_info[2]) + '16' + self.l_url
                        yield scrapy.Request(out_url, callback=self.parse_detail, meta={'date': date_, 'city': c_name, 'is_in': False, 'index': index})
                        index = index + 1
                        yield scrapy.Request(in_url, callback=self.parse_detail, meta={'date': date_, 'city': c_name, 'is_in': True, 'index': index})
                        index = index + 1
                    except Exception as err:
                        self.log('初次解析出错')
                        self.log(err)


    def parse_detail(self, response):
        if response.status == 200:
            items = json.loads(response.text[27:-3] + ']')
            for item in items:
                try:
                    md = hashlib.md5()
                    qianxi = QianximapItem()
                    qianxi['start_adr'] = item[0] if response.meta['is_in'] else response.meta['city']
                    qianxi['end_adr'] = response.meta['city'] if response.meta['is_in'] else item[0]
                    qianxi['count'] = item[1]
                    qianxi['car'] = item[2]
                    qianxi['train'] = item[3]
                    qianxi['airplane'] = item[4]
                    qianxi['date'] = response.meta['date']
                    qianxi['index'] = response.meta['index']

                    md.update(qianxi['start_adr'].encode())
                    md.update(b'-')
                    md.update(qianxi['end_adr'].encode())
                    md.update(b'-')
                    md.update(qianxi['date'].encode())
                    qianxi['id'] = md.hexdigest()
                    yield qianxi
                except Exception as err:
                    self.log('解析详细数据出错')
                    self.log(err)
