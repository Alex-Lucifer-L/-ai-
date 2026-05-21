项目名称：
厦门大学生/高校毕业生就业创业政策 AI 解读系统

核心定位：
帮助大学生/毕业生查询、理解、匹配在厦门就业创业时可适用的相关政策。

服务对象：
1. 在校大学生
2. 应届毕业生
3. 离校未就业毕业生
4. 准备来厦门就业的毕业生
5. 准备在厦门创业的毕业生

政策范围：
不再只限于“厦门本地发布的政策”，而是：

1. 国家级政策
2. 福建省级政策
3. 厦门市级政策
4. 厦门各区政策

地区层级：
中国
└── 福建省
    └── 厦门市
        ├── 思明区
        ├── 湖里区
        ├── 集美区
        ├── 海沧区
        ├── 同安区
        └── 翔安区

主要政策方向：
1. 就业补贴
2. 创业扶持
3. 人才补贴
4. 实习 / 见习
5. 职业培训
6. 落户 / 住房相关支持
7. 企业吸纳毕业生补贴

系统核心能力：
1. 政策查询
2. 政策分类查看
3. AI 通俗解读
4. 根据用户情况匹配政策
5. 展示政策来源
6. 判断政策适用层级



政策结构化信息：
政策标题
发布部门
发布层级
适用地区
政策类别
适用对象
政策状态
发布日期
来源链接
政策正文




工作流：
厦门大学生/高校毕业生就业创业政策 AI 解读系统
│
├── 1. 政策数据层
│   ├── 政策文件 Policy_Document
│   │   ├── 原始政策标题
│   │   ├── 发布部门
│   │   ├── 发布时间
│   │   ├── 来源链接
│   │   └── 政策全文
│   │
│   └── 政策措施 Policy_Item
│       ├── 具体补贴/扶持措施
│       ├── 适用对象
│       ├── 适用地区
│       ├── 申请条件
│       ├── 补贴标准
│       └── 办理方式
│
├── 2. 检索层
│   ├── 用户提出问题
│   ├── 系统从数据库查相关政策
│   └── 取出相关政策原文/摘要/措施
│
├── 3. AI 解读层
│   ├── 把用户问题 + 政策内容发给大模型 API
│   ├── 大模型生成通俗解释
│   └── 返回申请条件、补贴内容、注意事项
│
└── 4. 结果展示层
    ├── AI 解读结果
    ├── 相关政策列表
    ├── 原文来源链接
    └── 引用依据


数据库结构：
数据库设计核心
│
├── Policy_Document：保存官方政策文件
│   ├── 文件标题
│   ├── 发布部门
│   ├── 发布层级
│   ├── 发布时间
│   ├── 原文链接
│   └── 政策全文
│
└── Policy_Item：保存用户真正关心的具体措施
    ├── 措施名称
    ├── 所属政策文件
    ├── 政策类别
    ├── 适用地区
    ├── 适用对象
    ├── 申请条件
    ├── 扶持内容
    ├── 办理流程
    └── 注意事项








一、实体列表

1. Policy_Document   政策文件
2. Policy_Item       政策措施
3. Document_Item     政策文件-政策措施依据关系
4. Region            地区
5. Item_Region       政策措施-地区适用关系
6. Category          政策分类
7. User              用户
8. Login_Record      登录记录
9. QA_Record         问答记录
10. QA_Reference     问答引用关系


二、实体类型

强实体：
1. Policy_Document
2. Policy_Item
3. Region
4. Category
5. User
6. QA_Record

弱实体：
1. Login_Record

联系实体 / 中间实体：
1. Document_Item
2. Item_Region
3. QA_Reference

支持联系 / 识别联系：
User 1 ─── 产生 ─── N Login_Record

三、联系列表

1. Policy_Document N ─── 依据 ─── M Policy_Item
   通过 Document_Item / 政策文件-政策措施依据关系实现

2. Policy_Item N ─── 归类于 ─── 1 Category

3. Policy_Item N ─── 适用于 ─── M Region
   通过 Item_Region / 政策措施-地区适用关系实现

4. Region N ─── 隶属于 ─── 1 Region

5. User 1 ─── 产生 ─── N Login_Record
   Login_Record 是弱实体，“产生”是支持联系 / 识别联系

6. User 1 ─── 发起 ─── N QA_Record

7. QA_Record N ─── 引用 ─── M Policy_Item
   通过 QA_Reference / 问答引用关系实现






          

四、实体——属性

1. Policy_Document 政策文件
├── document_id 主键
├── title
├── policy_number
├── issuing_department
├── publish_level
├── publish_date
├── effective_date
├── expire_date
├── status
├── source_url
├── full_text
├── summary
└── created_at


2. Policy_Item 政策措施
├── item_id 主键
├── category_id 外键 → Category.category_id
├── item_name
├── target_group_text
├── conditions_text
├── support_content
├── subsidy_standard
├── application_materials
├── application_process
├── application_channel
├── keywords
├── status
└── created_at


3. Document_Item 政策文件-政策措施依据关系
├── document_id 外键 → Policy_Document.document_id
├── item_id 外键 → Policy_Item.item_id
├── relation_type
├── original_excerpt
├── note
└── 主键：document_id + item_id


4. Region 地区
├── region_id 主键
├── region_name
├── region_level
└── parent_region_id 外键 → Region.region_id


5. Item_Region 政策措施-地区适用关系
├── item_id 外键 → Policy_Item.item_id
├── region_id 外键 → Region.region_id
├── applicability_note
├── applicability_type
└── 主键：item_id + region_id


6. Category 政策分类
├── category_id 主键
├── category_name
└── description


7. User 用户
├── user_id 主键
├── username
├── password_hash
├── role
├── status
├── created_at
└── updated_at


8. Login_Record 登录记录
├── user_id 外键 → User.user_id
├── login_no 局部主键
├── login_time
├── login_ip
├── login_status
└── 主键：user_id + login_no


9. QA_Record 问答记录
├── qa_id 主键
├── user_id 外键 → User.user_id
├── user_question
├── ai_answer
├── question_time
├── answer_time
└── model_name


10. QA_Reference 问答引用关系
├── qa_id 外键 → QA_Record.qa_id
├── item_id 外键 → Policy_Item.item_id
├── relevance_score
├── reference_note
├── used_excerpt
├── rank_order
└── 主键：qa_id + item_id