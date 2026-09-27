# TrainTrans：12306 火车中转方案生成器

TrainTrans 是一个基于 Python 的工具，可根据用户指定的出发地、目的地与日期，实时查询 12306 官方数据，自动枚举所有可行的火车中转方案。项目通过启发式打分（总时长 × 总票价）对方案排序，在直达车次不足或时刻不合适时，帮助快速规划更优的换乘路线。

- Gitee：https://gitee.com/yeyup/TrainTrans
- GitHub：https://github.com/yeyup/TrainTrans

### 依赖

`python` · `pandas` · `selenium` · `chrome` + `chromedriver`

## 安装步骤

**前提条件**：Windows 10/11 或 Linux，并已安装 [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install#windows-powershell) 或 [Anaconda](https://www.anaconda.com/download)。

### 1. 下载项目与 Chrome / chromedriver

可从 [百度网盘](https://pan.baidu.com/s/1nQCsqxGDIUiyh4Md2-KU0g?pwd=jvus) 下载配套 Chrome 与 chromedriver，解压至本项目目录；如需最新版，请访问 [chrome-for-testing](https://googlechromelabs.github.io/chrome-for-testing) 或 [chromedriver](https://developer.chrome.com/docs/chromedriver)。

### 2. 创建 conda 虚拟环境

```
conda create -n train_env -c conda-forge python pandas selenium
conda activate train_env
```

### 3. 运行脚本（交互模式）

按提示逐项输入出发站、到达站、中转站、日期等信息：

```
# Windows
python .\train_input.py
# Linux
python train_input.py
```

也可使用绝对路径，例如：

```
# Windows
D:\programFile\miniconda3\envs\train_env\python D:\download\TrainTrans\train_input.py
# Linux
/home/user_name/miniconda3/envs/train_env/python /home/user_name/download/TrainTrans/train_input.py
```

### 4. 运行脚本（命令行模式）

通过命令行参数一次性指定所有条件，适合批量与脚本化调用：

```
# Windows
python .\train_input_cmd.py --from-station 北京 --to-station 上海 --via 南京 --date 20260202 --out bjsz.txt
# Linux
python train_input_cmd.py --from-station 北京 --to-station 上海 --via 南京 --date 20260202 --out bjsz.txt
```

完整选项说明：

```text
> python train_input_cmd.py -h
usage: train_input_cmd.py [-h] -f FROM_STATION -t TO_STATION -v VIA [-d DATE] -o OUT
                          [-g1 GAP_MIN] [-g2 GAP_MAX] [-ds DEP_START] [-de DEP_END]
                          [-as ARR_START] [-ae ARR_END] [-c] [-ld] [-la] [-k]
                          [-cc CHROME] [-cd CHROMEDRIVER] [-w WAIT_TIME]

查询 12306 火车中转换乘方案

options:
  -h, --help            show this help message and exit
  -f FROM_STATION, --from-station FROM_STATION
                        出发站
  -t TO_STATION, --to-station TO_STATION
                        到达站
  -v VIA, --via VIA     中转站，多个用逗号分开，如 武汉,郑州
  -d DATE, --date DATE  乘车日期，如 20241230，不输入则为两周后
  -o OUT, --out OUT     输出文件
  -g1 GAP_MIN, --gap-min GAP_MIN
                        中转间隔最少分钟数，默认 15，多个用逗号分开
  -g2 GAP_MAX, --gap-max GAP_MAX
                        中转间隔最多分钟数，默认 60，多个用逗号分开
  -ds DEP_START, --dep-start DEP_START
                        出发时间不早于，如 06:30，不指定则不检查
  -de DEP_END, --dep-end DEP_END
                        出发时间不晚于，如 09:00，不指定则不检查
  -as ARR_START, --arr-start ARR_START
                        到达时间不早于，如 15:15，不指定则不检查
  -ae ARR_END, --arr-end ARR_END
                        到达时间不晚于，如 20:59，不指定则不检查
  -c, --check           检查可用车票
  -ld, --limit-dep      限定出发站必须等于命令行指定的出发站
  -la, --limit-arr      限定到达站必须等于命令行指定的到达站
  -k, --keep-tmp        保留中间文件 tmp 目录
  -cc CHROME, --chrome CHROME
                        Chrome 可执行文件路径（默认：脚本目录/chrome/chrome）
  -cd CHROMEDRIVER, --chromedriver CHROMEDRIVER
                        chromedriver 可执行文件路径（默认：脚本目录/chromedriver/chromedriver）
  -w WAIT_TIME, --wait-time WAIT_TIME
                        12306 查询等待时间，默认 5
```

## 复用中间文件，二次筛选

运行 `train_input_cmd.py` 时加上 `--keep-tmp` 即可保留中间查询结果（`输出文件名 + tmptmp` 目录）。之后无需再访问 12306，直接调整 gap、时间或站名条件即可获得更精准的筛选结果：

```
# Windows
python .\train_rescore.py --from-tmp bjsz.txttmptmp --out bjsz2.txt
# Linux
python train_rescore.py --from-tmp bjsz.txttmptmp --out bjsz2.txt
```

完整选项说明：

```text
> python train_rescore.py -h
usage: train_rescore.py [-h] -t FROM_TMP -o OUT [-g1 GAP_MIN] [-g2 GAP_MAX] [-c]
                        [-ds DEP_START] [-de DEP_END] [-as ARR_START] [-ae ARR_END]
                        [-ld LIMIT_DEP] [-la LIMIT_ARR]

复用已保存的 tmp 目录，重跑不同 gap/时间/站名筛选

options:
  -h, --help            show this help message and exit
  -t FROM_TMP, --from-tmp FROM_TMP
                        之前运行保留的 tmp 目录（含 .tsv 查询结果）
  -o OUT, --out OUT     输出文件
  -g1 GAP_MIN, --gap-min GAP_MIN
                        中转间隔最少分钟数，默认 15，多个用逗号分开
  -g2 GAP_MAX, --gap-max GAP_MAX
                        中转间隔最多分钟数，默认 60，多个用逗号分开
  -c, --check           检查可用车票（不指定则不检查）
  -ds DEP_START, --dep-start DEP_START
                        出发时间不早于，如 06:30
  -de DEP_END, --dep-end DEP_END
                        出发时间不晚于，如 09:00
  -as ARR_START, --arr-start ARR_START
                        到达时间不早于，如 15:15
  -ae ARR_END, --arr-end ARR_END
                        到达时间不晚于，如 20:59
  -ld LIMIT_DEP, --limit-dep LIMIT_DEP
                        限定出发站（等于命令行指定的出发站）
  -la LIMIT_ARR, --limit-arr LIMIT_ARR
                        限定到达站（等于命令行指定的到达站）
```

## 注意事项

- 本项目仅供个人学习与研究使用，禁止任何商业用途。
- 频繁查询可能导致 12306 临时限制访问；严禁用于票务代抢等违规行为。
- 因使用本项目产生的任何问题，开发者不承担任何责任。
- 个人 PC 上较不易触发 12306 的访问限制；若使用服务器或集群，请选用 `train_input_cmd.py` 并适当调高 `--wait-time`（例如 `--wait-time 15`），以确保稳定获取数据。

## 已知限制

- 跨天车次的整合可能存在错误，相关时刻信息或不准确。
- 对于超过 24 小时的旅程，统计数据的计算可能有误。

## 更新日志

- 修复因站名前缀重名导致无法查询特定线路车次的问题。
- 重构代码以提升运行稳定性。

## 贡献指南

欢迎通过 Issue 提交建议与反馈，我们将尽可能采纳并实现更多功能。
