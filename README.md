## TrainTransfer：12306火车中转方案生成器
#### This project does not have an English version, as it is exclusively designed for China's 12306 railway ticketing system. 
### 项目简介
TrainTrans是一个基于Python开发的智能工具，能够根据用户输入的出发地、目的地和日期，实时查询12306官方数据，自动生成所有可行的火车中转方案。项目通过智能算法分析列车时刻数据，为用户提供最优换乘建议，特别适合解决直达车次不足或时间不合适时的出行规划问题。
### 依赖 
`python` `pandas` `selenium` `chrome,chromedriver`
### 安装步骤
#### 前提条件： Windows 10/11 操作系统，已安装 Miniconda 或 Anaconda
1. 下载本项目仓库并下载chrome, chromedriver
##### 关于chrome, chromedriver，请访问https://googlechromelabs.github.io/chrome-for-testing/ 或 https://developer.chrome.com/docs/chromedriver
2. 创建conda虚拟环境
```
# 1. 创建虚拟环境
conda create -n train_env -c conda-forge python pandas selenium
# 2. 激活环境 
conda activate train_env
```
3. 在项目目录执行
```
python .\train_input.py
```
或使用绝对路径，例如
```
D:\programFile\miniconda3\envs\train_env\python D:\download\TrainTrans\train_input.py
```
并根据提示输入相应信息
### 注意事项
#### ⚠️ 重要法律声明
本项目仅限个人学习研究用途，禁止商业使用。频繁查询可能导致12306无法访问。严禁使用本项目从事票务代抢等违规行为。因使用本项目产生的任何问题，开发者不承担责任
#### 技术限制
目前对跨天车次信息整合存在错误，本项目暂时无法正确计算超过24小时情形时统计数据，且车次信息可能有误
#### 贡献指南
欢迎通过Issue提交建议，将尽可能实现更多功能

