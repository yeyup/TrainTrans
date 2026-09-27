import time,os,sys,datetime,re,itertools,warnings,shutil,argparse  # 导入所需的库
paths = os.path.dirname(os.path.abspath(__file__))  # 脚本所在目录（用于 chrome 默认路径）
def parse_gap(raw, vianum):  # 解析中转间隔（逗号分隔整数列表），并与中转站数校验
    var = list(map(int, raw.split(',')))  # 将输入转化为整数列表
    varnum = len(var)   # 统计中转间隔数个数
    if varnum > 1 and varnum != vianum:  # 中转间隔数应与经停站数(vianum)一致；单一值套用全部
        sys.exit(f"错误：中转间隔数({varnum})与中转站数({vianum})不匹配，请检查 --gap-min/--gap-max。")
    return var, varnum
def validate_time(val, name):  # 校验 HH:MM 时间格式，空串表示不筛选
    if not val:
        return ""
    pattern = r'^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$'  # 时间格式正则表达式
    if not re.match(pattern, val):
        sys.exit(f"错误：{name} 格式应为 HH:MM（如 06:30），收到：{val}")
    return val
# ---- 命令行参数----
parser = argparse.ArgumentParser(description="查询12306火车中转换乘方案")
parser.add_argument("-f", "--from-station", required=True, help="出发站")
parser.add_argument("-t", "--to-station", required=True, help="到达站")
parser.add_argument("-v", "--via", required=True, help="中转站，多个用逗号分开，如武汉,郑州")
parser.add_argument("-d", "--date", default=None, help="乘车日期，如20241230，不输入则为两周后")
parser.add_argument("-o", "--out", required=True, help="输出文件")
parser.add_argument("-g1", "--gap-min", default="15", help="中转间隔最少分钟数，默认15，多个用逗号分开")
parser.add_argument("-g2", "--gap-max", default="60", help="中转间隔最多分钟数，默认60，多个用逗号分开")
parser.add_argument("-ds", "--dep-start", default="", help="出发时间不早于，如06:30，不指定则不检查")
parser.add_argument("-de", "--dep-end", default="", help="出发时间不晚于，如09:00，不指定则不检查")
parser.add_argument("-as", "--arr-start", default="", help="到达时间不早于，如15:15，不指定则不检查")
parser.add_argument("-ae", "--arr-end", default="", help="到达时间不晚于，如20:59，不指定则不检查")
parser.add_argument("-c", "--check", action="store_true", help="检查可用车票")
parser.add_argument("-ld", "--limit-dep", action="store_true", help="限定出发站必须等于命令行指定的出发站")
parser.add_argument("-la", "--limit-arr", action="store_true", help="限定到达站必须等于命令行指定的到达站")
parser.add_argument("-k", "--keep-tmp", action="store_true", help="保留中间文件tmp目录")
parser.add_argument("-cc", "--chrome", default=paths+os.sep+"chrome"+os.sep+"chrome",
                    help="Chrome 可执行文件路径（默认：脚本目录/chrome/chrome）")
parser.add_argument("-cd", "--chromedriver", default=paths+os.sep+"chromedriver"+os.sep+"chromedriver",
                    help="chromedriver 可执行文件路径（默认：脚本目录/chromedriver/chromedriver）")
parser.add_argument("-w", "--wait-time", default="5", help="12306查询等待时间，默认5")
args = parser.parse_args()

froms = args.from_station
to = args.to_station
via = args.via.split(',')
vianum = len(via)
if args.date:  # 乘车日期：显式指定则校验，否则默认两周后
    try:
        date = datetime.datetime.strptime(args.date, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        sys.exit(f"错误：日期格式应为 YYYYMMDD，收到：{args.date}")
else:
    date = (datetime.datetime.now()+datetime.timedelta(days=14)).strftime("%Y%m%d")
    date = datetime.datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")
out = args.out
gapmin, gapminnum = parse_gap(args.gap_min, vianum)
gapmax, gapmaxnum = parse_gap(args.gap_max, vianum)
check = args.check
depstart = validate_time(args.dep_start, "出发时间不早于")
depend = validate_time(args.dep_end, "出发时间不晚于")
arrstart = validate_time(args.arr_start, "到达时间不早于")
arrend = validate_time(args.arr_end, "到达时间不晚于")
limit_dep = args.limit_dep
limit_arr = args.limit_arr
keep_tmp = args.keep_tmp
tmp = out + 'tmptmp'  # 临时文件路径
if not os.path.isfile(args.chrome):
    sys.exit(f"错误：Chrome 可执行文件不存在：{args.chrome}\n（可用 --chrome 指定正确路径）")
if not os.path.isfile(args.chromedriver):
    sys.exit(f"错误：chromedriver 可执行文件不存在：{args.chromedriver}\n（可用 --chromedriver 指定正确路径）")

# Starting
import pandas as pd
from selenium import webdriver  # 使用selenium进行网页交互
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from contextlib import redirect_stdout  # 重定向标准输出
def dt():  # 获取当前时间的辅助函数
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
def select_station(driver, input_id, target, max_arrow=15):
    # 多次盲选：键入站名后，按 k 次 ArrowDown 再 ENTER，读回 value 判断是否精确命中。
    # 解决 12306 前缀同名站（如 北京/北京南/北京西）直接 ENTER 会选错的问题。
    inp = driver.find_element(By.ID, input_id)
    for k in range(max_arrow):
        inp.click()
        inp.clear()
        time.sleep(0.2)
        inp.send_keys(target)
        time.sleep(1.0)  # 等下拉出现
        for _ in range(k):  # 把高亮移到第 k 项（k=0 即直接 ENTER 取默认高亮）
            inp.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.1)
        inp.send_keys(Keys.ENTER)
        time.sleep(0.3)
        val = inp.get_attribute('value')
        if val is not None and val.strip() == target.strip():
            return True
    return False
def wait_for_results(driver, timeout=20):
    # 等待 12306 结果表格返回：出现车次行（#queryLeftTable tr），或出现“无结果”提示即返回。
    # 超时也不抛异常，按原逻辑继续（下游会判空文件），避免偶发慢网络直接崩。
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "#queryLeftTable tr")
                      or any(k in d.page_source for k in ("未找到", "没有", "抱歉"))
        )
    except Exception:
        pass
def parse_train_info(input_file, check_left=False):  # 解析火车信息
    # aria_price/aria_seat/aria_left 均初始化，避免某车次无余票行时打印触发 NameError
    current_title = "";current_strong = [];aria_labels = [];aria_price = "";aria_seat = "";aria_left = "";l = 0  # 初始化
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
                current_title = "";current_strong = [];aria_labels = [];aria_price = "";aria_seat = "";aria_left = ""   # 重置
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
print(f"[{dt()}] 处理中：{froms} -> {to}，中转={via}，日期={date}。")
os.makedirs(tmp, exist_ok=True)  # 创建临时目录
stationlst = [froms, *via, to]  # 构造站点列表
os.environ['PULSE_SERVER'] = ''  # 处理音频
options = webdriver.ChromeOptions()  # 设置Chrome选项
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--mute-audio')
options.binary_location = args.chrome  # 指定chrome路径
service = Service(executable_path=args.chromedriver)  # 指定chromedriver路径
driver = webdriver.Chrome(service=service, options=options)
driver.get('https://kyfw.12306.cn/otn/leftTicket/init')
time.sleep(1)
driver.implicitly_wait(float(args.wait_time)/5)
for s in range(vianum+1):
    for s2 in range(s+1, vianum+2):
        print(f"[{dt()}]正在查询{date} {stationlst[s]}->{stationlst[s2]}。")
        # 出发站：多次盲选，确保选中的站名与键入一致（避免前缀同名站选错）
        if not select_station(driver, 'fromStationText', stationlst[s]):
            print(f"[{dt()}]警告：{stationlst[s]} 未精确匹配下拉项，使用最后候选。")
        # 到达站
        if not select_station(driver, 'toStationText', stationlst[s2]):
            print(f"[{dt()}]警告：{stationlst[s2]} 未精确匹配下拉项，使用最后候选。")
        driver.find_element(By.ID,'train_date').click()
        driver.find_element(By.ID,'train_date').clear()
        driver.find_element(By.ID,'train_date').send_keys(date)  # 输入乘车日期
        driver.find_element(By.ID,'train_date').send_keys(Keys.ENTER)
        driver.find_element(By.ID,'query_ticket').click()
        wait_for_results(driver)  # 等待结果表格返回（替代固定 sleep）
        time.sleep(float(args.wait_time))  # 留出 DOM 稳定时间
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
    file3 = None  # 本子集累积结果文件，先置空，避免沿用上一次子集的残留
    for sidx in range(len(ssall)-1):
        gapidx = ssall[sidx] - 1
        file2 = tmp+os.sep+str(ssall[sidx])+str(ssall[sidx+1])+'.tsv'
        if not os.path.exists(file2) or os.path.getsize(file2) <= 0:
            print(f"[{dt()}]{stationlst[ssall[sidx]]}->{stationlst[ssall[sidx+1]]}无直达车或网站信息有误。")
            file3 = None; break  # 置空而非 del，避免未定义变量；同时阻断本次子集
        gap1 = gapmin[gapidx] if gapminnum > 1 else gapmin[0]
        gap2 = gapmax[gapidx] if gapmaxnum > 1 else gapmax[0]
        file3 = tmp+os.sep+str(ssall[sidx])+'.tsv2'
        transfer_plan(file1, file2, file3, gap1, gap2)
        file1 = file3
    if file3 is not None and os.path.exists(file3) and os.path.getsize(file3) > 0:
        get_score(file3, out, check)
if keep_tmp:
    print(f"[{dt()}]已保留中间文件目录：{tmp}")
else:
    shutil.rmtree(tmp)  # 删除临时文件夹及其内容
# out 可能从未被写入（没有任何方案），先判断存在再取大小，避免 FileNotFoundError
if not os.path.exists(out) or os.path.getsize(out) <= 0:
    if os.path.isfile(out):
        os.remove(out)
    print(f"[{dt()}]未找到中转方案，请稍后重试或更改设置。")
else:
    header = "总时长\t总票价\t得分" + "\t车次\t出发站\t到达站\t发时\t到时\t座位\t票价\t余票\t票览" * (vianum + 1) + "\n"  # 生成输出文件的标题行
    with open(out, 'r', encoding='utf-8') as f:
        content = f.readlines()
    data = []
    def _to_min(t):
        if not t:
            return None
        h, m = map(int, t.split(':'))
        return h * 60 + m
    dep_lo, dep_hi = _to_min(depstart), _to_min(depend)
    arr_lo, arr_hi = _to_min(arrstart), _to_min(arrend)
    if limit_dep or limit_arr:  # 站名一致性筛选日志
        print(f"[{dt()}]应用站名一致性筛选：出发站={'与1一致('+froms+')' if limit_dep else '不限定'}，"
              f"到达站={'与2一致('+to+')' if limit_arr else '不限定'}。")
    for line in content:
        parts = line.strip().split('\t')  # 分割行并去掉换行符
        # 方案站名一致性筛选（输入13/14）：要求出发站/到达站与输入1/2完全一致，否则丢弃该方案
        if limit_dep and len(parts) > 4 and parts[4].strip() != froms.strip():
            continue
        if limit_arr and len(parts) > (5 + vianum * 9) and parts[5 + vianum * 9].strip() != to.strip():
            continue
        duration_hour, duration_minute = map(int, parts[0].split(':'))  # 总时长
        dep_hour, dep_minute = map(int, parts[6].split(':'))  # 出发时间
        dep_min = dep_hour * 60 + dep_minute
        arr_min = dep_min + duration_hour * 60 + duration_minute  # 到达时间（绝对分钟，正确处理跨天）
        if (dep_lo is not None and dep_min < dep_lo) or (dep_hi is not None and dep_min > dep_hi):  # 出发时间范围
            continue
        if (arr_lo is not None and arr_min < arr_lo) or (arr_hi is not None and arr_min > arr_hi):  # 到达时间范围（跨天按绝对分钟比较）
            continue
        third_col_value = parts[2] if len(parts) > 2 else None  # 获取第三列的值，如果不存在则设为None
        try:  # 尝试将第三列的值转换为浮点数，以便排序
            third_col_value = float(third_col_value) if third_col_value is not None else float('inf')
        except ValueError:
            third_col_value = float('inf')  # 如果转换失败，则将其视为一个极大的数
        data.append((third_col_value, line))  # 将原始行与第三列的值一起存储
    if not data:
        if os.path.isfile(out):
            os.remove(out)
        print(f"[{dt()}]经过出发/到达时间或站名一致性筛选后无结果。")
    else:
        data.sort(key=lambda x: x[0])  # 按第三列的数值排序
        content = [line for _, line in data]  # 输出排序结果
        content.insert(0, header)  # 添加标题行
        with open(out, 'w', encoding='utf-8') as f:
            f.writelines(content)
        print(f"[{dt()}]中转方案已保存到{out}。")

