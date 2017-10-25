# weixinart

对[搜狗微信](http://weixin.sogou.com/weixin?query=%E9%85%92%E5%BA%97%E5%8E%A8%E6%88%BF%E6%8E%92%E7%83%9F%E7%AE%A1%E9%81%93&_sug_type_=&s_from=input&_sug_=n&type=2&page=1&ie=utf8)系列页面进行爬取

`spider:` 这是我写的一个早期版本, 只是完成了对网页的定向爬取, 输入验证码, 更换代理, 数据存到mongodb

`spiderPro:` pro版封装了自己的工具模块myTool, 另外使用多线程, 用queue在线程间传递数据, 图片为爬取一页运行结果
