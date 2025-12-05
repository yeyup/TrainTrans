import time,os,sys,datetime,re,itertools,warnings,shutil  # 导入所需的库
def input0(prompt):
    while True:
        var = input('(必须)'+prompt).strip()  # 读取输入并去掉两端空格
        if var:  # 检查输入是否非空
            return var  # 返回有效输入
def input1(prompt, default=15):
    while True:
        var = input(prompt).strip()  # 读取输入并去掉两端空格
        if not var:  # 如果用户没有输入内容，设定为默认值
            var = str(default)
        var = list(map(int, var.split(',')))  # 将输入转化为整数列表
        varnum = len(var)   # 统计中转间隔数个数
        if varnum > 1 and varnum < vianum:  # 检查中转站数与中转间隔数的匹配
            print("中转站数与中转间隔数不匹配，请再试一次。")
        else:
            return var, varnum
def input2(prompt):  # 定义一个函数用于输入时间格式(小时:分钟)，确保输入的格式正确
    pattern = r'^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$|^$'  # 时间格式正则表达式
    while True:
        var = input(prompt).strip()
        if re.match(pattern, var):  # 校验输入格式是否符合要求
            return var
print("查询火车中转换乘方案，请输入以下内容：")
froms = input0('1.出发站：')
to = input0('2.到达站：')
via = input0('3.中转站，多个请用","分开：').split(',')
vianum = len(via)
while True:
    date = input('4.乘车日期，如20241230，不输入则为两周后：').strip()
    if not date:  # 如果没有输入，则设定为两周后
        date = (datetime.datetime.now()+datetime.timedelta(days=14)).strftime("%Y%m%d")
    try:
        date = datetime.datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")  # 格式化日期
        break
    except ValueError:
        print("输入错误，请再试一次。")
out = input0('5.输出文件：')
gapmin, gapminnum = input1('6.中转间隔最少分钟数，不输入则为15，多个请用","分开：')
gapmax, gapmaxnum = input1('7.中转间隔最多分钟数，不输入则为60，多个请用","分开：', 60)
check = True if input('8.是否检查可用车票，不输入则为否：') != '' else False  # 检查是否检查可用车票
depstart = input2("9.出发时间不早于，如06:30，不输入则不筛选：")
depend = input2("10.出发时间不晚于，如09:00，不输入则不筛选：")
arrstart = input2("11.到达时间不早于，如15:15，不输入则不筛选：")
arrend = input2("12.到达时间不晚于，如20:59，不输入则不筛选：")
tmp = out + 'tmptmp'  # 临时文件路径

# Starting
import pandas as pd
from selenium import webdriver  # 使用selenium进行网页交互
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from contextlib import redirect_stdout  # 重定向标准输出
paths = os.path.dirname(os.path.abspath(__file__))
def dt():  # 获取当前时间的辅助函数
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
def parse_train_info(input_file, check_left=False):  # 解析火车信息
    current_title = "";current_strong = [];aria_labels = [];aria_price = "";l = 0  # 初始化
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    pattern = r'<tbody id="queryLeftTable">'  # 分割内容，获取 tbody 开始后的部分
    tbody_content = content.split(pattern)[1]  # 获取匹配后的内容
    modified_content = re.sub(r'<', r'\n<', tbody_content)  # 添加换行符以处理HTML内容
    modified_content = re.sub(r'>', r'>\n', modified_content)
    filtered_lines = [l for l in modified_content.splitlines() if l.strip() and l != '--' and l != ' ' and not l.startswith('</')]   # 过滤掉空行和不需要的行
    while l < len(filtered_lines):
        line = filtered_lines[l].strip()
        title_match = re.match(r'.*<a title="(.*)"', line)  # 检查行是否含有列车标题
        if title_match:
            if current_title:
                tmp_strong = '\t'.join(current_strong[:4])
                print(f"{current_title}\t{tmp_strong}\t{aria_seat}\t{aria_price}\t{aria_left}\t{','.join(aria_labels).replace('，', '').replace('票价', '').replace('余票', '')}")
                current_title = "";current_strong = [];aria_labels = [];aria_price = ""   # 重置
            current_title = filtered_lines[l+1].strip()
            l += 2;continue
        strong_match = re.match(r'<strong(.*)', line)  # 检查<strong>行
        if strong_match:
            current_strong.append(filtered_lines[l+1].strip())
            l += 2;continue
        aria_match = re.search(r'aria-label="([^"]+)"', line)  # 检查余票信息
        if current_title and aria_match:
            aria_info = aria_match.group(1)
            labels = aria_info.split("，")
            seat = labels[1].split("票价")[0].strip()  # 获取座位信息
            price = labels[1].split("票价")[1].replace("元","").strip()  # 获取票价
            left = labels[2].replace("余票", "").strip()  # 获取余票信息
            if aria_price:  # 如果已有票价信息
                if not check_left or (left != "无" and left != "候补"):  # 判断是否需要检查余票
                    if float(aria_price) > float(price):  # 只保留最低票价
                        aria_price = price;aria_seat = seat;aria_left = left
            else:
                aria_price = price;aria_seat = seat;aria_left = left
            aria_labels.append(aria_info.split("列车，")[1].strip())
            l += 1;continue
        if line == "以下为同车车次变更接续方案(无需下车换乘)":
            if current_title:
                tmp_strong = '\t'.join(current_strong[:4])
                print(f"{current_title}\t{tmp_strong}\t{aria_seat}\t{aria_price}\t{aria_left}\t{','.join(aria_labels).replace('，', '').replace('票价', '').replace('余票', '')}")
            break
        l += 1
def subset(n=3):  # 生成组合信息
    subset = []
    element = list(range(1, n+1))
    for i in range(1, n+1):
        subset.extend(itertools.combinations(element, i))
    return subset
def transfer_plan(train1, train2, output, gapmin=15, gapmax=60):  # 处理中转方案
    warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)
    df1 = pd.read_csv(train1, sep='\t', header=None)
    df2 = pd.read_csv(train2, sep='\t', header=None)
    colnum = len(df1.columns) // 9 - 1
    stations = set(df1[df1[0] != '-----'][df1.columns[2 + 9 * colnum]])  # 获取唯一的站点，并排除掉无效行
    results = []
    for station in stations:  # 过滤每个列车关于当前站的信息
        tr1_filtered = df1[(df1.apply(lambda x: all(y != '-----' for y in x), axis=1)) & (df1[df1.columns[2 + 9 * colnum]] == station)]
        tr2_filtered = df2[(df2.apply(lambda x: all(y != '-----' for y in x), axis=1)) & (df2[1] == station)]
        tr1_filtered['Minutes'] = tr1_filtered[tr1_filtered.columns[4 + 9 * colnum]].apply(  # 将时间列转换为分钟数
            lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
        tr2_filtered['Minutes'] = tr2_filtered[3].apply(lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
        for _, tr1 in tr1_filtered.iterrows():
            for _, tr2 in tr2_filtered.iterrows():
                if (tr1['Minutes'] + gapmin <= tr2['Minutes'] <= tr1['Minutes'] + gapmax):  # 判断两个火车的时间差在设定范围内
                    results.append(list(tr1.drop('Minutes')) + list(tr2.drop('Minutes')))
    with open(output, 'w', encoding='utf-8') as out_file:  # Write results to output file
        for res in results:
            out_file.write('\t'.join(map(str, res)) + '\n')
def get_score(infile, outfile, check_left=False):  # 根据得分获取最终结果
    df = pd.read_csv(infile, sep='\t', header=None)
    colidx = df.shape[1] // 9
    if check_left:  # 根据留票条件过滤数据
        df = df[~df[[i * 9 + 7 for i in range(colidx)]].isin(['无','候补']).any(axis=1)]
    starttime = df[3].apply(lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
    endtime = df[colidx * 9 - 5].apply(lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
    elapstime = [(j - i + 1440) if (j <= i) else (j - i) for i, j in zip(starttime, endtime)]  # 计算经过的时间
    sumprice = df[[i * 9 + 6 for i in range(colidx)]].sum(axis=1)  # 计算总票价
    sumtime = [f"{i // 60:02}:{i % 60:02}" for i in elapstime]  # 将时间差格式化为小时:分钟
    df.insert(0,'score',elapstime * sumprice)
    df.insert(0,'price',sumprice)
    df.insert(0,'time',sumtime)
    df.sort_values(by=['score','price'], ascending=[True,True]).to_csv(outfile, sep='\t', header=False, index=False, mode='a')  # 按照得分和票价进行升序排序，并写入到输出文件
print(f"[{dt()}] 处理中。")
os.makedirs(tmp, exist_ok=True)  # 创建临时目录
stationlst = [froms, *via, to]  # 构造站点列表
os.environ['PULSE_SERVER'] = ''  # 处理音频
options = webdriver.ChromeOptions()  # 设置Chrome选项
options.add_argument('--headless --no-sandbox --mute-audio')  # 启动无头浏览器
options.binary_location = paths+os.sep+"chrome"+os.sep+"chrome.exe"  # 指定chrome路径
service = Service(executable_path=paths+os.sep+"chromedriver"+os.sep+"chromedriver.exe")  # 指定chromedriver路径
driver = webdriver.Chrome(service=service, options=options)
driver.get('https://kyfw.12306.cn/otn/leftTicket/init')
time.sleep(1)
driver.implicitly_wait(0.1)
for s in range(vianum+1):
    for s2 in range(s+1, vianum+2):
        print(f"[{dt()}]正在查询{date} {stationlst[s]}->{stationlst[s2]}。")
        driver.find_element(By.ID,'fromStationText').click()
        driver.find_element(By.ID,'fromStationText').clear()
        driver.find_element(By.ID,'fromStationText').send_keys(stationlst[s])  # 输入出发站
        driver.find_element(By.ID,'fromStationText').send_keys(Keys.ENTER)
        driver.find_element(By.ID,'toStationText').click()
        driver.find_element(By.ID,'toStationText').clear()
        driver.find_element(By.ID,'toStationText').send_keys(stationlst[s2])  # 输入到达站
        driver.find_element(By.ID,'toStationText').send_keys(Keys.ENTER)
        driver.find_element(By.ID,'train_date').click()
        driver.find_element(By.ID,'train_date').clear()
        driver.find_element(By.ID,'train_date').send_keys(date)  # 输入乘车日期
        driver.find_element(By.ID,'train_date').send_keys(Keys.ENTER)
        driver.find_element(By.ID,'query_ticket').click()
        time.sleep(4)
        html_content = driver.page_source
        file0 = tmp+os.sep+str(s)+str(s2)
        with open(file0, "w", encoding='utf-8') as f:  # 保存HTML内容到临时文件
            f.write(html_content)
        with open(file0+'.tsv', 'w', encoding='utf-8') as f:  # 保存解析后的结果
            with redirect_stdout(f):
                parse_train_info(file0, check)
        print(f"[{dt()}]{date} {stationlst[s]}->{stationlst[s2]}结果保存到{file0}。")
driver.quit()
file0 = tmp+os.sep+'0'+str(s2)+'.tsv'
if os.path.isfile(out):  # 如果输出文件已存在，则删除
    os.remove(out)
filesize0 = True
for filename in os.listdir(tmp):  # 检查是否全区段都获取信息
    if filename.endswith('.tsv'):
        filepath = os.path.join(tmp, filename)
        if os.path.isfile(filepath) and os.path.getsize(filepath) <= 0:
            print(f"[{dt()}]部分区段无直达车或网站信息有误。")
            filesize0 = False
            break
if filesize0:
    print(f"[{dt()}]所有区段信息已获得。")
if os.path.exists(file0) and os.path.getsize(file0) > 0:
    get_score(file0, out, check)
for ss in subset(vianum):  # 获取所有中转站的组合
    file1 = tmp+os.sep+'0'+str(ss[0])+'.tsv'
    if not os.path.exists(file1) or os.path.getsize(file1) <= 0:
        print(f"[{dt()}] {froms}->{stationlst[ss[0]]}无直达车或网站信息有误。")
        continue
    ssall = ss+(vianum+1,)
    for sidx in range(len(ssall)-1):
        gapidx = ssall[sidx] - 1
        file2 = tmp+os.sep+str(ssall[sidx])+str(ssall[sidx+1])+'.tsv'
        if not os.path.exists(file2) or os.path.getsize(file2) <= 0:
            print(f"[{dt()}]{stationlst[ssall[sidx]]}->{stationlst[ssall[sidx+1]]}无直达车或网站信息有误。")
            del file3;break
        gap1 = gapmin[gapidx] if gapminnum > 1 else gapmin[0]
        gap2 = gapmax[gapidx] if gapmaxnum > 1 else gapmax[0]
        file3 = tmp+os.sep+str(ssall[sidx])+'.tsv2'
        transfer_plan(file1, file2, file3, gap1, gap2)
        file1 = file3
    if 'file3' in globals():
        if os.path.exists(file3) and os.path.getsize(file3) > 0:
            get_score(file3, out, check)
shutil.rmtree(tmp)  # 删除临时文件夹及其内容
if os.path.getsize(out) <= 0:
    if os.path.isfile(out):
        os.remove(out)
    print(f"[{dt()}]未找到中转方案，请稍后重试或更改设置。")
else:
    header = "总时长\t总票价\t得分" + "\t车次\t出发站\t到达站\t发时\t到时\t座位\t票价\t余票\t票览" * (vianum + 1) + "\n"  # 生成输出文件的标题行
    with open(out, 'r', encoding='utf-8') as f:
        content = f.readlines()
    data = []
    for line in content:
        parts = line.strip().split('\t')  # 分割行并去掉换行符
        duration_hour, duration_minute = map(int, parts[0].split(':'))  # 获取总时长
        dep_hour, dep_minute = map(int, parts[6].split(':'))  # 获取出发时间
        arr_minute = dep_minute + duration_minute  # 计算到达时间
        arr_hour = dep_hour + duration_hour + (arr_minute // 60)  # 超过60分钟则进位
        arr_minute %= 60  # 保持在0-59分钟内
        dep_time = parts[6]
        arr_time = str(arr_hour) + ":" + str(arr_minute)
        if len(arr_time) < 5:
            arr_time = "0" + arr_time 
        if (depstart and dep_time < depstart) or (depend and dep_time > depend):  # 判断出发时间是否在指定范围内
            continue  # 不在范围内，跳过
        if (arrstart and arr_time < arrstart) or (arrend and arr_time > arrend):  # 判断到达时间是否在指定范围内
            continue  # 不在范围内，跳过
        third_col_value = parts[2] if len(parts) > 2 else None  # 获取第三列的值，如果不存在则设为None
        try:  # 尝试将第三列的值转换为浮点数，以便排序
            third_col_value = float(third_col_value) if third_col_value is not None else float('inf')
        except ValueError:
            third_col_value = float('inf')  # 如果转换失败，则将其视为一个极大的数
        data.append((third_col_value, line))  # 将原始行与第三列的值一起存储
    if not data:
        if os.path.isfile(out):
            os.remove(out)
        print(f"[{dt()}]经过出发到达时间筛选后无结果。")
    else:
        data.sort(key=lambda x: x[0])  # 按第三列的数值排序
        content = [line for _, line in data]  # 输出排序结果
        content.insert(0, header)  # 添加标题行
        with open(out, 'w', encoding='utf-8') as f:
            f.writelines(content)
        print(f"[{dt()}]中转方案已保存到{out}。")