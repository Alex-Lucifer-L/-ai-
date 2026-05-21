-- Initial schema for 厦门大学生/高校毕业生就业创业政策 AI 解读系统
-- Target database: MySQL 8.x

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS category (
  category_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '政策分类主键',
  category_name VARCHAR(100) NOT NULL COMMENT '政策分类名称',
  description TEXT NULL COMMENT '分类说明',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (category_id),
  UNIQUE KEY uk_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='政策分类';

CREATE TABLE IF NOT EXISTS region (
  region_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '地区主键',
  region_name VARCHAR(100) NOT NULL COMMENT '地区名称',
  region_level VARCHAR(30) NOT NULL COMMENT '地区层级：country/province/city/district',
  region_code VARCHAR(20) NULL COMMENT '行政区划代码，可为空',
  parent_region_id BIGINT UNSIGNED NULL COMMENT '上级地区',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (region_id),
  UNIQUE KEY uk_region_parent_name (parent_region_id, region_name),
  UNIQUE KEY uk_region_code (region_code),
  KEY idx_region_level (region_level),
  CONSTRAINT fk_region_parent
    FOREIGN KEY (parent_region_id) REFERENCES region (region_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地区';

CREATE TABLE IF NOT EXISTS policy_document (
  document_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '政策文件主键',
  title VARCHAR(500) NOT NULL COMMENT '政策标题',
  policy_number VARCHAR(100) NULL COMMENT '政策文号',
  issuing_department VARCHAR(255) NOT NULL COMMENT '发布部门',
  publish_level VARCHAR(30) NOT NULL COMMENT '发布层级：country/province/city/district',
  publish_date DATE NULL COMMENT '发布日期',
  effective_date DATE NULL COMMENT '生效日期',
  expire_date DATE NULL COMMENT '失效日期',
  status VARCHAR(30) NOT NULL DEFAULT 'effective' COMMENT '政策状态：effective/expired/repealed/draft/unknown',
  source_url VARCHAR(1000) NULL COMMENT '原文链接',
  full_text LONGTEXT NULL COMMENT '政策全文',
  summary TEXT NULL COMMENT '政策摘要',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (document_id),
  KEY idx_policy_document_publish_level (publish_level),
  KEY idx_policy_document_publish_date (publish_date),
  KEY idx_policy_document_status (status),
  FULLTEXT KEY ft_policy_document_text (title, issuing_department, full_text, summary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='官方政策文件';

CREATE TABLE IF NOT EXISTS policy_item (
  item_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '政策措施主键',
  category_id BIGINT UNSIGNED NOT NULL COMMENT '政策分类',
  item_name VARCHAR(300) NOT NULL COMMENT '措施名称',
  target_group_text TEXT NULL COMMENT '适用对象',
  conditions_text TEXT NULL COMMENT '申请条件',
  support_content TEXT NULL COMMENT '扶持内容',
  subsidy_standard TEXT NULL COMMENT '补贴标准',
  application_materials TEXT NULL COMMENT '申请材料',
  application_process TEXT NULL COMMENT '办理流程',
  application_channel VARCHAR(500) NULL COMMENT '办理渠道',
  keywords TEXT NULL COMMENT '检索关键词',
  status VARCHAR(30) NOT NULL DEFAULT 'effective' COMMENT '措施状态：effective/expired/repealed/suspended/unknown',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (item_id),
  KEY idx_policy_item_category (category_id),
  KEY idx_policy_item_status (status),
  FULLTEXT KEY ft_policy_item_text (
    item_name,
    target_group_text,
    conditions_text,
    support_content,
    subsidy_standard,
    keywords
  ),
  CONSTRAINT fk_policy_item_category
    FOREIGN KEY (category_id) REFERENCES category (category_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='具体政策措施';

CREATE TABLE IF NOT EXISTS document_item (
  document_id BIGINT UNSIGNED NOT NULL COMMENT '政策文件',
  item_id BIGINT UNSIGNED NOT NULL COMMENT '政策措施',
  relation_type VARCHAR(50) NOT NULL DEFAULT 'basis' COMMENT '关系类型：basis/amendment/repeal/implementation',
  original_excerpt TEXT NULL COMMENT '原文依据摘录',
  note TEXT NULL COMMENT '备注',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (document_id, item_id),
  KEY idx_document_item_item (item_id),
  KEY idx_document_item_relation_type (relation_type),
  CONSTRAINT fk_document_item_document
    FOREIGN KEY (document_id) REFERENCES policy_document (document_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_document_item_item
    FOREIGN KEY (item_id) REFERENCES policy_item (item_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='政策文件-政策措施依据关系';

CREATE TABLE IF NOT EXISTS item_region (
  item_id BIGINT UNSIGNED NOT NULL COMMENT '政策措施',
  region_id BIGINT UNSIGNED NOT NULL COMMENT '适用地区',
  applicability_note TEXT NULL COMMENT '适用说明',
  applicability_type VARCHAR(50) NOT NULL DEFAULT 'direct' COMMENT '适用类型：direct/inherited/excluded/reference',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (item_id, region_id),
  KEY idx_item_region_region (region_id),
  KEY idx_item_region_type (applicability_type),
  CONSTRAINT fk_item_region_item
    FOREIGN KEY (item_id) REFERENCES policy_item (item_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_item_region_region
    FOREIGN KEY (region_id) REFERENCES region (region_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='政策措施-地区适用关系';

CREATE TABLE IF NOT EXISTS app_user (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户主键',
  username VARCHAR(100) NOT NULL COMMENT '用户名',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
  role VARCHAR(30) NOT NULL DEFAULT 'user' COMMENT '角色：admin/user',
  status VARCHAR(30) NOT NULL DEFAULT 'active' COMMENT '用户状态：active/disabled/deleted',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (user_id),
  UNIQUE KEY uk_app_user_username (username),
  KEY idx_app_user_role (role),
  KEY idx_app_user_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户';

CREATE TABLE IF NOT EXISTS login_record (
  user_id BIGINT UNSIGNED NOT NULL COMMENT '用户',
  login_no INT UNSIGNED NOT NULL COMMENT '用户内登录序号',
  login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  login_ip VARCHAR(45) NULL COMMENT '登录 IP，兼容 IPv4/IPv6',
  login_status VARCHAR(30) NOT NULL DEFAULT 'success' COMMENT '登录状态：success/failed',
  PRIMARY KEY (user_id, login_no),
  KEY idx_login_record_time (login_time),
  KEY idx_login_record_status (login_status),
  CONSTRAINT fk_login_record_user
    FOREIGN KEY (user_id) REFERENCES app_user (user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录记录';

CREATE TABLE IF NOT EXISTS qa_record (
  qa_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '问答记录主键',
  user_id BIGINT UNSIGNED NOT NULL COMMENT '提问用户',
  user_question TEXT NOT NULL COMMENT '用户问题',
  ai_answer LONGTEXT NULL COMMENT 'AI 回答',
  question_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提问时间',
  answer_time DATETIME NULL COMMENT '回答时间',
  model_name VARCHAR(100) NULL COMMENT '模型名称',
  PRIMARY KEY (qa_id),
  KEY idx_qa_record_user (user_id),
  KEY idx_qa_record_question_time (question_time),
  FULLTEXT KEY ft_qa_record_question_answer (user_question, ai_answer),
  CONSTRAINT fk_qa_record_user
    FOREIGN KEY (user_id) REFERENCES app_user (user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答记录';

CREATE TABLE IF NOT EXISTS qa_reference (
  qa_id BIGINT UNSIGNED NOT NULL COMMENT '问答记录',
  item_id BIGINT UNSIGNED NOT NULL COMMENT '引用的政策措施',
  relevance_score DECIMAL(6,5) NULL COMMENT '相关度得分，范围建议 0-1',
  reference_note TEXT NULL COMMENT '引用说明',
  used_excerpt TEXT NULL COMMENT '实际使用的政策摘录',
  rank_order INT UNSIGNED NULL COMMENT '引用排序',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (qa_id, item_id),
  KEY idx_qa_reference_item (item_id),
  KEY idx_qa_reference_rank (qa_id, rank_order),
  CONSTRAINT fk_qa_reference_qa
    FOREIGN KEY (qa_id) REFERENCES qa_record (qa_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_qa_reference_item
    FOREIGN KEY (item_id) REFERENCES policy_item (item_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答引用关系';

SET FOREIGN_KEY_CHECKS = 1;
