# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class QianximapItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    start_adr = scrapy.Field()
    end_adr = scrapy.Field()
    count = scrapy.Field()
    car = scrapy.Field()
    train = scrapy.Field()
    airplane = scrapy.Field()
    date = scrapy.Field()
    index = scrapy.Field()


