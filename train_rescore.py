import os, sys, re, argparse, itertools, warnings
import pandas as pd

def subset(n):
    s = []; e = list(range(1, n + 1))
    for i in range(1, n + 1):
        s.extend(itertools.combinations(e, i))
    return s
def transfer_plan(t1, t2, out, gmin, gmax):
    warnings.simplefilter('ignore')
    df1 = pd.read_csv(t1, sep='\t', header=None)
    df2 = pd.read_csv(t2, sep='\t', header=None)
    cn = len(df1.columns) // 9 - 1
    stations = set(df1[df1[0] != '-----'][df1.columns[2 + 9 * cn]])
    res = []
    for st in stations:
        a = df1[(df1.apply(lambda x: all(y != '-----' for y in x), axis=1)) & (df1[df1.columns[2 + 9 * cn]] == st)]
        b = df2[(df2.apply(lambda x: all(y != '-----' for y in x), axis=1)) & (df2[1] == st)]
        a['M'] = a[a.columns[4 + 9 * cn]].apply(lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
        b['M'] = b[3].apply(lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
        for _, r1 in a.iterrows():
            for _, r2 in b.iterrows():
                if r1['M'] + gmin <= r2['M'] <= r1['M'] + gmax:
                    res.append(list(r1.drop('M')) + list(r2.drop('M')))
    with open(out, 'w', encoding='utf-8') as f:
        for r in res:
            f.write('\t'.join(map(str, r)) + '\n')
def get_score(inf, outf, check):
    df = pd.read_csv(inf, sep='\t', header=None)
    ci = df.shape[1] // 9
    if check:
        df = df[~df[[i * 9 + 7 for i in range(ci)]].isin(['无', '候补']).any(axis=1)]
    st = df[3].apply(lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
    et = df[ci * 9 - 5].apply(lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
    el = [(j - i + 1440) if j <= i else j - i for i, j in zip(st, et)]
    sp = df[[i * 9 + 6 for i in range(ci)]].sum(axis=1)
    df.insert(0, 'score', el * sp); df.insert(0, 'price', sp)
    df.insert(0, 'time', [f"{i // 60:02}:{i % 60:02}" for i in el])
    df.sort_values(['score', 'price']).to_csv(outf, sep='\t', header=False, index=False, mode='a')
def read_stations(path):
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                p = line.rstrip('\n').split('\t')
                if len(p) > 2 and p[1].strip() and p[2].strip():
                    return p[1].strip(), p[2].strip()
    except FileNotFoundError:
        return None, None
    return None, None
def parse_gap(raw, vianum):
    var = list(map(int, raw.split(',')))
    if len(var) > 1 and len(var) != vianum:
        sys.exit(f"错误：中转间隔数({len(var)})与经停段数({vianum})不匹配，请检查 --gap-min/--gap-max。")
    return var, len(var)
def validate_time(val, name):
    if not val:
        return ""
    if not re.match(r'^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$', val):
        sys.exit(f"错误：{name} 格式应为 HH:MM，收到：{val}")
    return val
# ---------- 命令行参数 ----------
ap = argparse.ArgumentParser(description="复用已保存的 tmp 目录，重跑不同 gap/时间/站名筛选")
ap.add_argument("-t", "--from-tmp", required=True, help="之前运行保留的 tmp 目录（含 .tsv 查询结果）")
ap.add_argument("-o", "--out", required=True, help="输出文件")
ap.add_argument("-g1", "--gap-min", default="15", help="中转间隔最少分钟数，默认15，多个用逗号分开")
ap.add_argument("-g2", "--gap-max", default="60", help="中转间隔最多分钟数，默认60，多个用逗号分开")
ap.add_argument("-c", "--check", action="store_true", help="检查可用车票（不指定则不检查）")
ap.add_argument("-ds", "--dep-start", default="", help="出发时间不早于，如06:30")
ap.add_argument("-de", "--dep-end", default="", help="出发时间不晚于，如09:00")
ap.add_argument("-as", "--arr-start", default="", help="到达时间不早于，如15:15")
ap.add_argument("-ae", "--arr-end", default="", help="到达时间不晚于，如20:59")
ap.add_argument("-ld", "--limit-dep", default=None, help="限定出发站")
ap.add_argument("-la", "--limit-arr", default=None, help="限定到达站")
args = ap.parse_args()
# ---------- 从 tmp 自动推断 出发站/到达站/经停段数 ----------
if not os.path.isdir(args.from_tmp):
    sys.exit(f"错误：tmp 目录不存在：{args.from_tmp}")
tsv_files = [f for f in os.listdir(args.from_tmp) if f.endswith('.tsv')]
if not tsv_files:
    sys.exit(f"错误：{args.from_tmp} 中无 .tsv 文件。")
digits = set()
for f in tsv_files:
    for c in f[:-4]:
        if c.isdigit():
            digits.add(int(c))
V = max(digits)
vianum = V - 1
froms, _ = read_stations(os.path.join(args.from_tmp, "01.tsv"))
if froms is None:
    for f in sorted(tsv_files):
        if f.startswith('0') and len(f) > 5:
            s, _ = read_stations(os.path.join(args.from_tmp, f))
            if s:
                froms = s; break
_, to = read_stations(os.path.join(args.from_tmp, f"{V - 1}{V}.tsv"))
if to is None:
    _, to = read_stations(os.path.join(args.from_tmp, f"0{V}.tsv"))
if froms is None or to is None:
    sys.exit("错误：无法从 tmp 推断出发站/到达站，请检查 .tsv 内容。")
print(f"从 tmp 推断：出发站={froms}  到达站={to}  经停段数={vianum}")
if args.limit_dep and args.limit_dep.strip() != froms:
    print(f"警告：--limit-dep={args.limit_dep} 与 tmp 推断的出发站({froms})不一致。")
if args.limit_arr and args.limit_arr.strip() != to:
    print(f"警告：--limit-arr={args.limit_arr} 与 tmp 推断的到达站({to})不一致。")
gapmin, gapminn = parse_gap(args.gap_min, vianum)
gapmax, gapmaxn = parse_gap(args.gap_max, vianum)
check = args.check
depstart = validate_time(args.dep_start, "出发时间不早于")
depend = validate_time(args.dep_end, "出发时间不晚于")
arrstart = validate_time(args.arr_start, "到达时间不早于")
arrend = validate_time(args.arr_end, "到达时间不晚于")
tmp = args.from_tmp
out = args.out
# ---------- 重跑组合 + 打分（复用 .tsv）----------
if os.path.isfile(out):
    os.remove(out)
file0 = os.path.join(tmp, f"0{V}.tsv")
if os.path.exists(file0) and os.path.getsize(file0) > 0:
    get_score(file0, out, check)
for ss in subset(vianum):
    file1 = os.path.join(tmp, f"0{ss[0]}.tsv")
    if not os.path.exists(file1) or os.path.getsize(file1) <= 0:
        continue
    ssall = ss + (V,)
    file3 = None
    for sidx in range(len(ssall) - 1):
        gapidx = ssall[sidx] - 1
        file2 = os.path.join(tmp, f"{ssall[sidx]}{ssall[sidx + 1]}.tsv")
        if not os.path.exists(file2) or os.path.getsize(file2) <= 0:
            file3 = None; break
        g1 = gapmin[gapidx] if gapminn > 1 else gapmin[0]
        g2 = gapmax[gapidx] if gapmaxn > 1 else gapmax[0]
        file3 = os.path.join(tmp, f"{ssall[sidx]}.tsv2")
        transfer_plan(file1, file2, file3, g1, g2)
        file1 = file3
    if file3 is not None and os.path.exists(file3) and os.path.getsize(file3) > 0:
        get_score(file3, out, check)
# ---------- 时间 + 站名筛选，生成最终文件 ----------
if not os.path.exists(out) or os.path.getsize(out) <= 0:
    if os.path.isfile(out):
        os.remove(out)
    print("未找到中转方案，请调整 gap/时间设置。")
else:
    header = "总时长\t总票价\t得分" + "\t车次\t出发站\t到达站\t发时\t到时\t座位\t票价\t余票\t票览" * (vianum + 1) + "\n"
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
    for line in content:
        parts = line.strip().split('\t')
        if args.limit_dep and len(parts) > 4 and parts[4].strip() != args.limit_dep.strip():
            continue
        if args.limit_arr and len(parts) > (5 + 9 * vianum) and parts[5 + 9 * vianum].strip() != args.limit_arr.strip():
            continue
        dur_h, dur_m = map(int, parts[0].split(':'))
        dep_h, dep_m = map(int, parts[6].split(':'))
        dep_min = dep_h * 60 + dep_m
        arr_min = dep_min + dur_h * 60 + dur_m
        if (dep_lo is not None and dep_min < dep_lo) or (dep_hi is not None and dep_min > dep_hi):
            continue
        if (arr_lo is not None and arr_min < arr_lo) or (arr_hi is not None and arr_min > arr_hi):
            continue
        try:
            tc = float(parts[2]) if len(parts) > 2 and parts[2] else float('inf')
        except ValueError:
            tc = float('inf')
        data.append((tc, line))
    if not data:
        if os.path.isfile(out):
            os.remove(out)
        print("经过时间或站名筛选后无结果。")
    else:
        data.sort(key=lambda x: x[0])
        content = [line for _, line in data]
        content.insert(0, header)
        with open(out, 'w', encoding='utf-8') as f:
            f.writelines(content)
        print(f"中转方案已保存到{out}。")

