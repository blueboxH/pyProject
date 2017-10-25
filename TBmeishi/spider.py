''' selenium '''
import sqlite3
import time
from timeit import timeit

from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

from myTool.Pcolor import print_blue, print_green, print_rd, print_red
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        WebDriverException)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

service_args = ['--load-images=false', '--disk-cache=true']
driver = webdriver.PhantomJS(service_args=service_args)
# driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 10)
con = sqlite3.connect('taobao.db')
con.execute('CREATE TABLE IF NOT EXISTS meishi(id INTEGER primary key AUTOINCREMENT, title TEXT UNIQUE, price REAL, dealCnt INTEGER, isServiceFree TEXT, shopname TEXT, location TEXT, image TEXT, url TEXT)')
cursor = con.cursor()

URL = 'https://www.taobao.com'
KEYWORD = '美食'


def search(url, keyword):
    ''' search '''
    try:
        driver.get(url)
        input = wait.until(EC.presence_of_element_located((By.ID, 'q')))
        input.clear()
        input.send_keys(keyword, Keys.ENTER)
        total = wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, 'total')))
        print(int(total.text.split()[1]))
        return int(total.text.split()[1])
    except WebDriverException as e:
        print_rd('搜索关键词出错:', e)
        search(url, keyword)


def goto_the_page(page_num):
    ''' 跳转到第几页 '''
    try:
        page_input = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'J_Input')))
        page_input.clear()
        page_input.send_keys(page_num, Keys.ENTER)
        ActionChains(driver).send_keys(Keys.END).perform()
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_num)))
        return True
    except TimeoutError:
        print_rd('加载超时:', page_num)
        goto_the_page(page_num)
    except Exception as e:
        print_rd('跳转页面出错:', page_num, e)
        goto_the_page(page_num)


def save_to_db(product):
    ''' 保存到数据库 '''
    try:
        cursor.execute(
            "INSERT INTO meishi values (null, ?, ?, ?, ?, ?, ?, ?, ?)", (product['title'], product['price'], product['deal_cnt'], product['is_service_free'], product['shop_name'], product['location'], product['image'], product['url']))
        con.commit()
        if cursor.rowcount is not -1:
            return True
        else:
            return False
    except sqlite3.IntegrityError:
        print('数据重复')
        return False
    except Exception as e:
        print('储存到数据库出错啦', e)
        return False


def parse_details_html_by_bs4():
    ''' 用bs4解析 '''
    try:
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '.J_MouserOnverReq')))
        html = driver.page_source
        soup = BeautifulSoup(html, 'html5lib')
        items = soup.find_all('div', class_='J_MouserOnverReq')
        for item in items:
            result = {}
            image_ele = item.select_one('.pic a img')

            result['title'] = item.select_one('.title a').text.strip()
            result['image'] = image_ele.get('src', image_ele.get('data-src'))
            result['price'] = item.select_one('.price strong').text
            result['deal_cnt'] = item.select_one('.deal-cnt').text[:-3]
            result['is_service_free'] = '包邮' if item.select(
                '.icon-service-free') else '不包邮'
            result['url'] = item.select_one('.title a')['href']
            result['shop_name'] = item.select_one('.shopname ').text.strip()
            result['location'] = item.select_one('.location ').text

            print_red(' ' * 20, items.index(item),
                      '*' * 20, '正在用BeautifulSoup解析', '*' * 20, '保存到数据库: %s' % ('成功' if save_to_db(result) else '失败',))
        return len(items)
    except TimeoutError as e:
        print_rd('等待超时', e)
        parse_details_html_by_bs4()
    except Exception as e:
        print_rd('parse__by_bs4 出错啦', e)


def parse_details_html_by_pq():
    ''' 用pyquery解析 '''
    try:
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '.J_MouserOnverReq')))
        html = pq(driver.page_source, parser='html')
        # items = html.find('.J_MouserOnverReq')
        items = html.find('#mainsrp-itemlist .items .item')
        for item in items.items():
            result = {}
            image = item.find('.pic img').attr('data-src')

            result['image'] = image if image else item.fing(
                '.pic img').attr('src')
            result['title'] = item.find('.title a').text().strip()
            result['price'] = item.find('.price strong').text()
            result['deal_cnt'] = item.find('.deal-cnt').text()[:-3]
            result['is_service_free'] = '包邮' if item.has_class(
                'icon-service-free') else '不包邮'
            result['url'] = item.find('.title a').attr('href')
            result['shop_name'] = item.find('.shopname ').text().strip()
            result['location'] = item.find('.location ').text()

            print_blue(
                ' ' * 20, items.index(item[0]), '*' * 20, '正在用PyQuery解析', '*' * 20, '保存到数据库: %s' % ('成功' if save_to_db(result) else '失败',))
        return len(items)
    except TimeoutError as e:
        print_rd('等待超时', e)
        parse_details_html_by_bs4()
    except Exception as e:
        print_rd('parse_by_pq 出错啦', e)


def has_element(element, selector):
    ''' 判断是否存在一个元素 '''
    try:
        res = element.find_element_by_css_selector(selector)
        return res
    except NoSuchElementException:
        return False


def parse_details_html_by_selenium():
    ''' 用selenium解析 '''
    try:
        items = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '.J_MouserOnverReq')))
        # items = driver.find_elements_by_class_name('J_MouserOnverReq')

        for item in items:
            result = {}
            image_ele = item.find_element_by_class_name('J_ItemPic')
            image = image_ele.get_attribute('data-src')

            result['image'] = image if image else image_ele.get_attribute(
                'src')
            result['title'] = item.find_element_by_class_name(
                'title').text.strip()
            result['url'] = item.find_element_by_class_name(
                'J_ClickStat').get_attribute('href')
            result['price'] = item.find_element_by_css_selector(
                '.price strong').text
            result['deal_cnt'] = item.find_element_by_class_name(
                'deal-cnt').text[:-3]
            # 这种写法是分析特性,不具有普遍性
            # result['is_service_free'] = True if len(item.find_elements_by_css_selector('.row-1 > div'))==3 else False

            # 封装判断element是否存在的方法,简单粗暴,目的直接
            result['is_service_free'] = '包邮' if has_element(
                item, '.icon-service-free') else '不包邮'
            result['shop_name'] = item.find_element_by_class_name(
                'shopname').text.strip()
            result['location'] = item.find_element_by_class_name(
                'location').text
            print_green(' ' * 20, items.index(item), "*" * 20, '正在用selenium解析',
                        '*' * 20, '保存到数据库: %s' % ('成功' if save_to_db(result) else '失败',))
        return len(items)

    except TimeoutError as e:
        print_rd('等待超时', e)
        parse_details_html_by_selenium()
    except Exception as e:
        print_rd('parse__by_selenium 出错啦', e)


def main():
    ''' main '''
    try:

        total = search(URL, KEYWORD)
        ActionChains(driver).send_keys(Keys.END).perform()
        time.sleep(3)
        # print_rd(parse_details_html_by_bs4())
        print_rd(parse_details_html_by_pq())
        # print(parse_details_html_by_selenium())
        for page_num in range(2, total + 1):
            if goto_the_page(page_num):
                if page_num % 3 == 0:
                    # result = parse_details_html_by_selenium()
                    run_time = timeit('parse_details_html_by_selenium()',
                                      setup='from __main__ import parse_details_html_by_selenium', number=1)
                elif page_num % 3 == 1:
                    # result = parse_details_html_by_pq()
                    run_time = timeit(
                        'parse_details_html_by_pq()', setup='from __main__ import parse_details_html_by_pq', number=1)
                else:
                    # result = parse_details_html_by_bs4()
                    run_time = timeit(
                        'parse_details_html_by_bs4()', setup='from __main__ import parse_details_html_by_bs4', number=1)
                print(page_num, '解析用时:', run_time)
    except Exception:
        print_rd('main 函数出错了')
    finally:
        cursor.close()
        con.close()
        driver.close()


if __name__ == '__main__':
    print('star')
    main()
