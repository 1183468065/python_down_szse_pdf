from urllib import request, parse
import json
import math
import os
import sys
from main import ThunderDownload

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

# https://github.com/1183468065
# 巨潮资讯网
# 1、根据stock查询orgId
# 2、查询列表 递归翻页下载
# 3、完事
# 下载地址

down_url = "http://static.cninfo.com.cn/"
# 接口地址
interface_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
orgId_url = "http://www.cninfo.com.cn/new/information/topSearch/query"
# 默认page_size
default_page_size = 30  # 巨潮资讯网没有地方修改此字段，最好不要该
# 文件默认路径
defaule_file_path = 'JCZXW_PDF/'
# 公司代码共六位，补全stock用
len_correct = 6
# 某些资源不好的尝试调用迅雷下载，但是大批量下载的时候会丢失下载任务
use_thunder = False
# 文件名中过滤掉不需要下载的文件
exclude_file_arr = ['摘要']


def retrieveback(file_name, save_path):
    print(file_name + "下载完成," + save_path)


def get_orgId(keyWord, maxNum=10):
    requestParam = {
        'keyWord': keyWord,  # 根据需要修改
        'maxNum': maxNum,  # 好像默认就是10
    }
    req_data = bytes(parse.urlencode(requestParam, encoding='utf-8'), encoding='utf-8')
    req = request.Request(orgId_url, data=req_data, method="POST")
    res = request.urlopen(req)
    response = json.loads(res.read().decode('utf-8'))
    # 这是一个list，只拿出第一个就可以了
    if len(response) != 0:
        return response[0]['orgId']
    else:
        return None


def get_annList(stock, se_date, pageNum=1, pageSize=default_page_size):
    org_id = get_orgId(stock)
    requestParam = {
        'pageNum': pageNum,  # 根据需要修改
        'pageSize': pageSize,  # 根据需要修改
        'seDate': se_date,  # 起止时间，格式yyyy-MM-dd
        'stock': stock + ',' + org_id,  # 代码,org_id
        'tabName': 'fulltext',  # 应该是根据不同的tblname查询不同的模块，这里固定
        'category': 'category_ndbg_szsh',  # 这啥玩意，不同类型？
        'column': 'szse'  # ？
    }
    data = bytes(parse.urlencode(requestParam, encoding='utf-8'), encoding='utf-8')
    header = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/74.0.3729.169 Safari/537.36'
    }
    req = request.Request(interface_url, data=data,
                          headers=header,
                          method='POST')
    res = request.urlopen(req)
    response = json.loads(res.read().decode('utf-8'))
    ann_list = response['announcements']
    if len(ann_list) == 0:
        print('未查询到任何信息')
        return
    # 总计数，用来翻页，没找到字段，自己算吧
    total_count = response['totalAnnouncement']
    if total_count == 0:
        print('未查询到任何信息')
        return

    total_page = math.ceil(total_count / pageSize)

    print("pageNo = " + str(pageNum))
    # 递归翻页
    if total_page != pageNum:
        get_annList(stock, se_date, pageNum + 1, pageSize)
    download_from_annList(ann_list)


def download_from_annList(ann_list):
    for model in ann_list:
        downUrl = down_url + model['adjunctUrl']
        fileName = model['secCode'] + model['secName'] + model['announcementTitle'] + '.pdf'
        fileName = check_filename(fileName)
        savePath = defaule_file_path + fileName
        need_down = check_file_need_down(fileName)
        if not need_down:
            print('过滤掉文件：' + fileName)
            continue
        exist = check_file_is_exist(savePath)
        if exist:
            print(savePath + '已存在')
            continue
        if use_thunder:
            ThunderDownload.thunder_download(downUrl, fileName)
        else:
            download_pdf(downUrl, savePath, fileName)


# 某些文件名中有非法字符，替换一下即可
def check_filename(filename):
    if '*' in filename:
        filename = filename.replace('*', '')
    return filename


def check_file_is_exist(save_path):
    if not os.path.exists(defaule_file_path):
        os.makedirs(defaule_file_path)
    if os.path.exists(save_path):
        return True
    else:
        return False


def check_file_need_down(filename):
    for exclude in exclude_file_arr:
        if exclude in filename:
            return False
    return True


def download_pdf(download_url, save_path, file_name):
    try:
        request.urlretrieve(download_url, save_path, retrieveback(file_name, save_path))
    except Exception as e:
        print(file_name + '下载失败')
        print(e)


def read_file_as_stock(filename):
    if not os.path.exists(filename):
        raise Exception('未找到该文件')
    stock_arr = []
    with open(filename) as file:
        line = file.readline()
        while len(line) > 0:
            if line.strip() not in stock_arr:
                if line.strip() != '':
                    stock_arr.append(line.strip())
            line = file.readline()
    # 此处得到txt元数据，因为公司代码共六位，判断代码是否正确，不正确的前面补0，生成正确公司代码
    stock_arr_correct = []
    for stock in stock_arr:
        if len(stock) > len_correct:
            print(stock + '代码不正确')
        elif len(stock) < len_correct:
            source_len = len(stock)
            diff_len = len_correct - source_len
            i = 0
            while i < diff_len:
                stock = '0' + stock
                i += 1
            stock_arr_correct.append(stock)
        else:
            stock_arr_correct.append(stock)
    return stock_arr_correct


if __name__ == '__main__':
    print('选择类型：A（输入公司代码，下载不同时间内的该公司pdf），B（根据一个txt文件读取公司代码，下载不同时间内该公司pdf，txt格式参考readme）')
    type = input()
    print('是否使用迅雷下载(y/n)(某些资源不好的尝试调用迅雷下载，但是大批量下载的时候可能会丢失下载任务)')
    use_thunder = True if input() == 'y' else False
    if type.upper() == 'A':
        print('输入公司代码')
        stockCode = input()
        print('输入查询开始时间，时间格式xxxx-xx-xx')
        dataBetween = input()
        print('输入查询截止时间，时间格式xxxx-xx-xx')
        dataAnd = input()
        seDate = [dataBetween, dataAnd]
        stockArr = [stockCode]
        get_annList(stockArr, seDate)
    elif type.upper() == 'B':
        print('输入文件名')
        filename = input()
        try:
            stock_arr = read_file_as_stock(filename)
            print('输入查询开始时间，时间格式xxxx-xx-xx')
            dataBetween = input()
            # dataBetween = '2009-01-01'
            print('输入查询截止时间，时间格式xxxx-xx-xx')
            dataAnd = input()
            # dataAnd = '2013-12-31'
            seDate = dataBetween + "~" + dataAnd
            print('公司代码：')
            print(stock_arr)
            for stock in stock_arr:
                get_annList(stock, seDate)

        except Exception as e:
            print(e)
            exit()
