# 官方政策数据源清单

本文档整理适合本项目爬取的官方政策网站。第一阶段建议优先抓取政策文件和办事指南，写入 `policy_document` 表。

## 优先级 1：厦门市级核心来源

| 来源 | URL | 适合抓取内容 | 备注 |
| --- | --- | --- | --- |
| 厦门市人力资源和社会保障局 | https://hrss.xm.gov.cn/ | 就业创业、人才服务、职业培训、人社政策 | 本项目最核心来源 |
| 厦门市人社局-政策法规 | https://hrss.xm.gov.cn/xxgk/zcfg/ | 规范性文件、就业创业政策、人才政策 | 适合做列表页爬虫 |
| 厦门市人社局-通知公告 | https://hrss.xm.gov.cn/xxgk/tzgg/ | 政策汇编、项目申报通知、补贴通知 | 内容更贴近用户问题 |
| 厦门市人社局-网上公示 | https://hrss.xm.gov.cn/xxgk/shgs/ | 人才生活补贴、见习补贴、职业技能补贴公示 | 可作为政策有效性和执行情况补充 |
| 厦门市教育局 | https://edu.xm.gov.cn/ | 高校毕业生政策指南、就业创业服务 | 适合补充毕业生政策汇编 |
| 厦门市人民政府门户网站 | https://www.xm.gov.cn/ | 主题服务、人才补贴、技能补贴、政策文件 | 适合补充综合办事指南 |

### 当前爬虫已接入的厦门人社局入口

| 名称 | URL | 类型 |
| --- | --- | --- |
| 就业创业 | https://hrss.xm.gov.cn/xxgk/zfxxgkzl/zfxxgkml/qtxx/jycy/ | 列表页 |
| 人才服务 | https://hrss.xm.gov.cn/xxgk/zfxxgkzl/zfxxgkml/qtxx/rcfw/ | 列表页 |
| 规范性文件 | https://hrss.xm.gov.cn/xxgk/zfxxgkzl/zfxxgkml/zcfg/gfxwj/ | 列表页 |
| 其他政策文件 | https://hrss.xm.gov.cn/xxgk/zfxxgkzl/zfxxgkml/zcfg/qtwj/ | 列表页 |
| 通知公告 | https://hrss.xm.gov.cn/xxgk/tzgg/ | 列表页 |
| 入厦政策 | https://app.hrss.xm.gov.cn/ggfwwt-auth/zdcypt/intoyhzc | 专题页 |
| 毕业生入厦政策指南 | https://app.hrss.xm.gov.cn/ggfwwt-auth/mnhr/intograduate | 专题页 |
| 优秀毕业生入厦政策 | https://app.hrss.xm.gov.cn/ggfwwt-auth/yxbyszt/intorxzc | 专题页 |

## 优先级 2：福建省级来源

| 来源 | URL | 适合抓取内容 | 备注 |
| --- | --- | --- | --- |
| 福建省人力资源和社会保障厅 | https://rst.fujian.gov.cn/ | 省级就业创业政策、劳动就业文件 | 用于判断省级政策适用范围 |
| 福建省政府门户网站 | https://www.fj.gov.cn/ | 省级办事指南、一次性求职补贴等主题服务 | 可作为省级政策补充 |
| 福建就业网/毕业生就业专区 | https://www.fj99.org.cn/bys/ | 毕业生就业服务、补贴申报入口 | 有些页面可能更偏办事系统 |

## 优先级 3：厦门各区政府来源

| 区域 | 官方网站 | 适合抓取内容 |
| --- | --- | --- |
| 思明区 | https://www.siming.gov.cn/ | 就业创业办事指南、社保补贴、培训补贴 |
| 湖里区 | https://www.huli.gov.cn/ | 创业资金申请、人才服务、就业创业主题服务 |
| 集美区 | https://www.jimei.gov.cn/ | 创业资金申请、新引进人才生活补贴 |
| 海沧区 | https://www.haicang.gov.cn/ | 就业创业栏目、毕业生就业创业补贴信息 |
| 同安区 | https://www.xmta.gov.cn/ | 就业创业、公示公告、创业补贴奖励公示 |
| 翔安区 | https://www.xiangan.gov.cn/ | 就业创业栏目、人才补贴公示、区级通知 |

## 优先级 4：国家级来源

| 来源 | URL | 适合抓取内容 | 备注 |
| --- | --- | --- | --- |
| 中国政府网 | https://www.gov.cn/ | 国务院、部委发布的高校毕业生就业创业政策 | 可做国家政策依据 |
| 人力资源和社会保障部 | https://www.mohrss.gov.cn/ | 国家就业创业、人社政策 | 国家级政策源头 |
| 教育部 | https://www.moe.gov.cn/ | 高校毕业生就业创业工作通知 | 偏高校和就业指导 |
| 国家大学生就业服务平台 | https://www.ncss.cn/ | 就业政策、就业服务、创业服务 | 可作为毕业生服务补充 |

## 当前已接入爬虫的新增来源

除厦门人社局外，目前 `official_generic.py` 已接入：

| 分组 | 来源 | URL |
| --- | --- | --- |
| `fujian-hrss` | 福建省人社厅-高校毕业生政策法规 JSON 数据 | https://rst.fujian.gov.cn/fw/kstd/bys/zcfg/dcdata.htm |
| `fujian-hrss` | 福建省人社厅-毕业生就业创业问答 | https://rst.fujian.gov.cn/wz/cjwt/bysjycy/bysjydj/ |
| `xiamen-gov` | 厦门市政府-稳岗就业 | https://www.xm.gov.cn/zdxxgk/jycy/ |
| `xiamen-gov` | 厦门市政府-人才补贴服务 | https://www.xm.gov.cn/wsbs/ztfw/fwcj/jycy/rcbtfw/ |
| `xiamen-gov` | 厦门市政府-技能提升补贴服务 | https://www.xm.gov.cn/wsbs/ztfw/fwcj/jycy/jntsbtfw/ |
| `xiamen-gov` | 厦门市政府-灵活就业参保服务 | https://www.xm.gov.cn/wsbs/ztfw/fwcj/jycy/lhjycbfw/ |
| `district-gov` | 集美区政府-创业资金申请 | https://www.jimei.gov.cn/nrrh/202309/t20230926_937426.htm |
| `district-gov` | 海沧区政府-就业创业 | https://www.haicang.gov.cn/xx/zdxxgk/zdxxgk/jycy/ |
| `district-gov` | 海沧区政府-毕业生就业创业补贴 | https://www.haicang.gov.cn/xx/ywdt/hcyw/jrhc/202507/t20250716_1108574.htm |
| `district-gov` | 思明区政府-重点群体项目制培训 | https://www.siming.gov.cn/xxgk/zwgkzdgz/wgjy/jyzc/202303/t20230306_901057.htm |
| `district-gov` | 湖里区政府-人才及重点群体住房保障 | https://www.huli.gov.cn/nrrh/202312/t20231202_1027800.htm |

## 建议的爬取顺序

1. 厦门市人社局-政策法规
2. 厦门市人社局-通知公告
3. 厦门市教育局-高校毕业生政策指南
4. 厦门市人民政府门户网站-就业创业主题服务
5. 福建省人社厅-劳动就业政策
6. 六个区政府网站的就业创业栏目
7. 中国政府网、人社部、教育部等国家级来源

## 入库建议

优先写入 `policy_document`：

```text
title
policy_number
issuing_department
publish_level
publish_date
status
source_url
full_text
summary
```

政策来源层级建议：

```text
国家级：publish_level = country
福建省级：publish_level = province
厦门市级：publish_level = city
厦门区级：publish_level = district
```

后续再从 `policy_document.full_text` 中拆解 `policy_item`。
