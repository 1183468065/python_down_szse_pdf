from urllib import request, parse
import json
import random


def get_random_str(length):
    i = 0
    random_no = ''
    while i < length:
        random_no = random_no + str(random.randint(0, 9))
        i += 1

    return random_no


def download_pdf(download_url, save_path, file_name):
    try:
        request.urlretrieve(download_url, save_path, retrieveback(file_name))
    except Exception as e:
        print(file_name + '下载失败')
        print(e)


def retrieveback(file_name):
    print(file_name + "下载完成")


def get_annList(stock_arr, se_date):
    requestParam = {
        'channelCode': ['listedNotice_disc'],  # 不清楚这个参数是什么，应该是固定的
        'pageNum': 1,  # 根据需要修改
        'pageSize': 30,  # 根据需要修改
        'seDate': se_date,  # 起止时间，格式yyyy-MM-dd
        'stock': stock_arr,  # 代码/简称/拼音/标题关键字
        # 'bigIndustryCode': '',  # 行业编号A、B、C、D、E，各行业有不同的字母，如果必须话需要自己去网站上寻找，我这里就不一一展示了
        # 'plateCode': '',  # 板块，主板11，中小板12，创业板16
        'bigCategoryId': ['010301']  # 公告类别，不同的公告类别有不同的标号，我这里需要年度报告，根据不同的需要去修改
    }
    data = bytes(json.dumps(requestParam), encoding='utf-8')
    # random参数可能是验证，这里我们每次请求都生成一个随机数
    randomNo = get_random_str(16)
    header = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/74.0.3729.169 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    req = request.Request('http://www.szse.cn/api/disc/announcement/annList?random=0.' + randomNo, data=data,
                          headers=header,
                          method='POST')
    res = request.urlopen(req)
    response = json.loads(res.read().decode('utf-8'))
    # 下载地址
    base_url = "http://disc.static.szse.cn/download"
    ann_list = response['data']
    if len(ann_list) == 0:
        print('未查询到任何信息')
        return
    for model in ann_list:
        downUrl = base_url + model['attachPath']
        savePath = model['title'] + '.pdf'
        fileName = model['title']
        download_pdf(downUrl, savePath, fileName)


if __name__ == '__main__':
    print('选择类型：A（输入公司代码，下载不同时间内的该公司pdf），B（根据一个txt文件读取公司代码，下载不同时间内该公司pdf，txt格式参考readme）')
    type = input()
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
        print('B')
