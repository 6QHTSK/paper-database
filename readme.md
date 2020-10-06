## DAY 1-REPO

### 24：00 更新

学习beatifulsoup4库

了解arxiv网站架构，决定爬虫的拉取的网页和分析方式

主要是在上课写作业，就没啥机会码代码

### 26：20更新

开始进行拉取部分的代码搭建

更改了拉取网页的策略

搭建了基础的爬虫，现在基本上可以达到层次一的内容

对此爬虫进行了基础的测试，基本满足当前的拉取要求

## DAY 2-REPO

### 24:30 更新

搭建数据库部分

找了一个arxiv的官方api，不再从搜索列表里拉东西

搭建main雏形

## DAY 3-REPO

解决了拉取列表时更新造成提前停止拉取的bug

搭建基础的下载pdf的程序（但是网太慢了）

## DAY 4-REPO

又是一天工程实训

搭建了基础的flask框架，并于数据库进行了适配

完善pdf下载功能

增加一个文件用于定时任务，定时拉取文件

对update功能进行测试，20k+数据完全成功拉取。但是下载功能由于太多正在优化，校园网还行远程服务器难以下载，考虑反代服务器

计划明后日进行flask框架运行中debug，学习搭建机器人mirai框架等，搭建简单的前端演示框架

## DAY 5-REPO

flask 框架完全测试完成，准备写api文档

优化了update函数的多线程处理，实时返回处理情况

优化了项目结构，现在它看起来更清晰了？

开始进行机器人编写，学习mirai框架下的python-mirai

决定忽略可能产生的论文更新问题。
