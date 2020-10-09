## API 文档

### /update

输入：无需参数

输出：
如果更新完成等

result: 是否响应更新请求

status: 0，开始；1，更新中，2 更新冷却中

message: 更新信息

lastupdate: 上次更新的各项信息

其中：message：上次更新信息 last_update:上次更新时间 error:上次更新的错误

```json

{
  "result": true,
  "status": 0,
  "message": "Started!",
  "last_update": {
    "message": "Done!",
    "last_update": 1602208918.4503858
  }
}

```

如果在更新进程中

```json

{
  "result": true,
  "status": 1,
  "message":"INITIATING",
  "percent": 0.0
}
```

若上次更新出现错误

```json

{"result": true,
  "status": 0,
  "message": "Started!",
  "last_update":
  {
    "message": "Server Error",
    "last_update": 1602208918.4503858,
    "error": "ERROR..."
  }
}
```

### /query

输入：json get方式
例如：

```json
{
  "key": "id",
  "query": "2010",
  "strict": false
}
```

key: 要查询的键值，key的值只能从下面输出的键中选取

query: 查询字符串

strict：置为false时进行模糊搜索

输出一个json形式的列表，例如

```json
[
    {
        "id": "arxiv:2010.02178v1",
        "title": "Mind the Pad -- CNNs can Develop Blind Spots",
        "authors": [
            "Bilal Alsallakh",
            "Narine Kokhlikyan",
            "Vivek Miglani",
            "Jun Yuan",
            "Orion Reblitz-Richardson"
        ],
        "summary": "We show how feature maps in convolutional networks are susceptible to spatialbias. Due to a combination of architectural choices, the activation at certainlocations is systematically elevated or weakened. The major source of this biasis the padding mechanism. Depending on several aspects of convolutionarithmetic, this mechanism can apply the padding unevenly, leading toasymmetries in the learned weights. We demonstrate how such bias can bedetrimental to certain tasks such as small object detection: the activation issuppressed if the stimulus lies in the impacted area, leading to blind spotsand misdetection. We propose solutions to mitigate spatial bias and demonstratehow they can improve model accuracy.",
        "category": [
            "cs.CV",
            "cs.AI",
            "stat.ML"
        ],
        "pdf": "http://arxiv.org/pdf/2010.02178v1",
        "essay_details": "http://arxiv.org/abs/2010.02178v1",
        "updated": 1601889888,
        "published": 1601889888,
        "primary_category": "cs.CV",
        "comment": "Appendix E available at  https://drive.google.com/file/d/1bIvRQJIBwJbKTfpg0hNaFX2ThuuDO8PU/view?usp=sharing",
        "journal_ref": null,
        "doi": null
    }
]
```

id: arxiv_id, title: 论文标题

authors: 作者 summary: 摘要

category: 论文标签 pdf: pdf文件下载地址

essay_details: 论文详细信息网址

updated: 更新的时间戳 published: 首次上传的时间戳

primary_category: 主要方向标签

comment：论文的comment

journal_ref: 论文的journal_ref

doi: 论文的doi

### /process

输入：无需参数
输出：当前update任务的进行情况
例如：

```json
{
  "status": 0,
  "message": "Not Updating"
}
```

```json
{
  "status": 1,
  "message":"INITIATING",
  "percent": 0.0
}
```

```json
{
  "status": 2,
  "message": "Done"
}
```

status: 0 未进行更新，1 正在更新，2 上次更新已完成

### /pdf/<arxiv_id>

输入：<arxiv_id> 需要下载的论文的arxiv_id
输出： pdf文件或者404

如果没有该文件且数据库中含有该id记录，则会当场下载。
