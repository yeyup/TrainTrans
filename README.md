# TrainTransfer12306：12306火车中转方案生成器
TrainTrans是一个基于Python开发的智能工具，能够根据用户输入的出发地、目的地和日期等，实时查询12306官方数据，自动生成所有可行的火车中转方案。项目通过智能算法分析列车时刻数据，为用户提供最优换乘建议，特别适合解决直达车次不足或时间不合适时的出行规划问题。

gitee地址：https://gitee.com/yeyup/TrainTrans

github地址：https://github.com/yeyup/TrainTrans
## 依赖 
`python` `pandas` `selenium` `chrome,chromedriver`
## 安装步骤
前提条件：Windows 10/11，安装 [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install#windows-powershell) 或 [Anaconda](https://www.anaconda.com/download)
#### 1. 下载本项目仓库并下载chrome, chromedriver
可从 [百度网盘](https://pan.baidu.com/s/1nQCsqxGDIUiyh4Md2-KU0g?pwd=jvus) 下载chrome,chromedriver并解压至本项目目录，最新版请访问 [chrome](https://googlechromelabs.github.io/chrome-for-testing) 或 [chromedriver](https://developer.chrome.com/docs/chromedriver)
#### 2. 创建conda虚拟环境
```
conda create -n train_env -c conda-forge python pandas selenium
# 激活环境 
conda activate train_env
```
#### 3. 在项目目录执行
```
python .\train_input.py
```
或使用绝对路径，例如
```
D:\programFile\miniconda3\envs\train_env\python D:\download\TrainTrans\train_input.py
```
并根据提示输入相应信息
## 注意事项
本项目仅限个人学习研究用途，禁止商业使用。频繁查询可能导致12306无法访问。严禁使用本项目从事票务代抢等违规行为。因使用本项目产生的任何问题，开发者不承担责任
#### 技术限制
跨天车次整合存在错误且信息可能有误；对超过24小时的旅程，计算统计数据可能有错
#### 贡献指南
欢迎通过Issue提交建议，将尽可能实现更多功能
