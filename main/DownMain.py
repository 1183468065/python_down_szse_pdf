from urllib import request
import json
import random
import math
import os

from main.ThunderDownload import thunder_download

# 下载地址
base_url = "http://disc.static.szse.cn/download"
# 接口地址
interface_url = "http://www.szse.cn/api/disc/announcement/annList"
# 随机数位数
random_len = 16
# 默认page_size
default_page_size = 30
# 文件默认路径
defaule_file_path = 'PDF/'
# 公司代码共六位，补全代码用
len_correct = 6
# 某些资源不好的尝试调用迅雷下载，但是大批量下载的时候会丢失下载任务
use_thunder = False
# 文件名中过滤掉不需要下载的文件
exclude_file_arr = ['2008', '2013']


def get_random_str(length):
    i = 0
    random_no = ''
    while i < length:
        random_no = random_no + str(random.randint(0, 9))
        i += 1

    return random_no


def retrieveback(file_name, save_path):
    print(file_name + "下载完成," + save_path)


def get_annList(stock_arr, se_date, pageNum=1, pageSize=default_page_size):
    requestParam = {
        'channelCode': ['listedNotice_disc'],  # 不清楚这个参数是什么，应该是固定的
        'pageNum': pageNum,  # 根据需要修改
        'pageSize': pageSize,  # 根据需要修改
        'seDate': se_date,  # 起止时间，格式yyyy-MM-dd
        'stock': stock_arr,  # 代码/简称/拼音/标题关键字
        # 'bigIndustryCode': '',  # 行业编号A、B、C、D、E，各行业有不同的字母，如果必须话需要自己去网站上寻找，我这里就不一一展示了
        # 'plateCode': '',  # 板块，主板11，中小板12，创业板16
        'bigCategoryId': ['010301']  # 公告类别，不同的公告类别有不同的标号，我这里需要年度报告，根据不同的需要去修改
    }
    data = bytes(json.dumps(requestParam), encoding='utf-8')
    # random参数可能是验证，这里我们每次请求都生成一个随机数
    randomNo = get_random_str(random_len)
    header = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/74.0.3729.169 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    req = request.Request(interface_url + '?random=0.' + randomNo, data=data,
                          headers=header,
                          method='POST')
    res = request.urlopen(req)
    response = json.loads(res.read().decode('utf-8'))
    ann_list = response['data']
    if len(ann_list) == 0:
        print('未查询到任何信息')
        return
    # 总计数，用来翻页
    total_count = response['announceCount']
    if total_count == 0:
        print('未查询到任何信息')
        return

    total_page = math.ceil(total_count / pageSize)

    print("pageNo = " + str(pageNum))
    # 递归翻页
    if total_page != pageNum:
        get_annList(stock_arr, se_date, pageNum + 1, pageSize)
    download_from_annList(ann_list)


def download_from_annList(ann_list):
    for model in ann_list:
        downUrl = base_url + model['attachPath']
        fileName = model['secCode'][0] + model['title'] + '.pdf'
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
            thunder_download(downUrl, fileName)
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
    print('是否使用迅雷下载(y/n)')
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
            # dataBetween = input()
            dataBetween = '2009-01-01'
            print('输入查询截止时间，时间格式xxxx-xx-xx')
            # dataAnd = input()
            dataAnd = '2013-12-31'
            seDate = [dataBetween, dataAnd]
            print('公司代码：')
            print(stock_arr)
            get_annList(stock_arr, seDate)
        except Exception as e:
            print(e)
            exit()
