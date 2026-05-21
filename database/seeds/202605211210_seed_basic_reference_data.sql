-- Basic seed data for categories and Xiamen region hierarchy.
-- Target database: MySQL 8.x

SET NAMES utf8mb4;

INSERT INTO category (category_id, category_name, description) VALUES
  (1, '就业补贴', '面向毕业生就业、求职、基层就业等场景的补贴政策'),
  (2, '创业扶持', '面向创业启动、创业场地、创业担保贷款等场景的扶持政策'),
  (3, '人才补贴', '面向高校毕业生、青年人才、重点产业人才的奖励和补贴政策'),
  (4, '实习/见习', '面向实习、就业见习、见习基地等场景的政策'),
  (5, '职业培训', '面向技能培训、职业资格、培训补贴等场景的政策'),
  (6, '落户/住房相关支持', '面向落户、租房、购房、人才住房等场景的支持政策'),
  (7, '企业吸纳毕业生补贴', '面向企业吸纳高校毕业生就业、社保补贴等场景的政策')
ON DUPLICATE KEY UPDATE
  category_name = VALUES(category_name),
  description = VALUES(description);

INSERT INTO region (region_id, region_name, region_level, region_code, parent_region_id) VALUES
  (1, '中国', 'country', 'CN', NULL),
  (2, '福建省', 'province', '350000', 1),
  (3, '厦门市', 'city', '350200', 2),
  (4, '思明区', 'district', '350203', 3),
  (5, '湖里区', 'district', '350206', 3),
  (6, '集美区', 'district', '350211', 3),
  (7, '海沧区', 'district', '350205', 3),
  (8, '同安区', 'district', '350212', 3),
  (9, '翔安区', 'district', '350213', 3)
ON DUPLICATE KEY UPDATE
  region_name = VALUES(region_name),
  region_level = VALUES(region_level),
  region_code = VALUES(region_code),
  parent_region_id = VALUES(parent_region_id);
