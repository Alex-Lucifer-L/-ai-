"""Shared quality rules for extracted policy items."""

from dataclasses import dataclass

from crawler.utils import compact_spaces


EXACT_NOISE_ITEM_NAMES = {
    "培训类型（选填）",
    "培训机构（单位）名称",
    "可开展的培训项目",
    "地址",
    "联系人",
    "联系电话",
    "备注",
    "职业培训师",
    "培训地点",
    "培训内容",
    "评审标准及规则",
    "资助等级",
    "补贴标准",
    "奖补标准",
    "受理机构：各级公共就业服务机构",
    "受理机构：各地公共就业人才服务机构",
    "享受对象：就业困难人员和离校未就业高校毕业生",
    "政策名称：用人单位社会保险补贴",
    "政策名称：企业吸纳就业税收优惠",
    "项目扶持",
    "年的社会保险补贴，不包括个人应缴纳的部分。",
}

NOISE_TITLE_KEYWORDS = (
    "培训学校",
    "培训中心",
    "人才培训中心",
    "有限公司",
    "学院",
    "名单",
    "目录",
    "申请表",
    "申报表",
    "明细表",
    "项目计划书",
    "附件：",
    "附件:",
    "联系电话",
    "联系人",
    "抖音号",
    "直播平台",
    "比赛顺序",
    "中场休息",
    "评审标准",
    "报名参赛条件",
    "参赛项目具有",
    "社会保险补贴，不包括个人应缴纳的部分",
)

WEAK_NOISE_PREFIXES = (
    "各区人社局",
    "各区、各有关单位",
    "受理机构：",
    "政策名称：",
    "附件：",
    "附件:",
)

POLICY_SIGNALS = (
    "补贴",
    "补助",
    "奖补",
    "奖励",
    "资助",
    "贷款",
    "落户",
    "住房补贴",
    "生活补贴",
    "安家补贴",
    "社保补贴",
    "创业担保贷款",
)

TALENT_KEYWORDS = (
    "人才",
    "生活补贴",
    "安家补贴",
    "师范生",
    "博士",
    "硕士",
    "本科生",
    "留学人员",
    "博士后",
    "高层次",
    "高技能领军人才",
)

ENTERPRISE_ABSORB_KEYWORDS = (
    "企业吸纳",
    "吸纳就业",
    "小微企业",
    "社会保险补贴",
    "社保补贴",
)

INTERNSHIP_KEYWORDS = ("见习", "实习")
TRAINING_KEYWORDS = ("培训", "职业技能", "技能提升", "技工院校", "学徒制")
HOUSING_KEYWORDS = ("住房", "租房", "公租房", "落户", "入厦", "保障性商品房")
ENTREPRENEUR_KEYWORDS = ("创业", "创业担保贷款", "一次性创业补贴", "创业资助")


@dataclass(frozen=True)
class QualityDecision:
    is_noise: bool
    reason: str = ""


def looks_like_noise_item(item_name: str, text: str = "") -> QualityDecision:
    item_name = compact_spaces(item_name)
    text = compact_spaces(text)
    combined = f"{item_name} {text}"

    if item_name in EXACT_NOISE_ITEM_NAMES:
        return QualityDecision(True, "精确命中表头/附件/流程噪声")

    if any(item_name.startswith(prefix) for prefix in WEAK_NOISE_PREFIXES):
        return QualityDecision(True, "命中弱政策措施前缀")

    if any(keyword in item_name for keyword in NOISE_TITLE_KEYWORDS):
        if not any(signal in combined for signal in POLICY_SIGNALS):
            return QualityDecision(True, "标题像机构/附件/活动流程且缺少政策信号")

    if any(keyword in item_name for keyword in ("培训学校", "培训中心", "有限公司")):
        return QualityDecision(True, "机构名称")

    if len(item_name) <= 4 and not any(signal in item_name for signal in POLICY_SIGNALS):
        return QualityDecision(True, "名称过短且缺少政策信号")

    if item_name.endswith("：") and not any(signal in combined for signal in POLICY_SIGNALS):
        return QualityDecision(True, "冒号标题且缺少政策信号")

    if item_name.startswith(("1.", "2.", "3.", "4.", "5.", "一、", "二、", "三、")) and len(item_name) > 45:
        if not any(signal in item_name for signal in POLICY_SIGNALS):
            return QualityDecision(True, "长编号条款且缺少政策信号")

    return QualityDecision(False, "")


def suggest_category(item_name: str, text: str, current_category: str, conservative: bool = False) -> str:
    title_text = item_name
    combined = f"{item_name}\n{text}"

    if conservative:
        if current_category == "落户/住房相关支持" and any(keyword in title_text for keyword in HOUSING_KEYWORDS):
            return current_category
        if current_category == "创业扶持" and any(keyword in title_text for keyword in ENTREPRENEUR_KEYWORDS):
            return current_category
        if current_category == "人才补贴" and any(keyword in title_text for keyword in TALENT_KEYWORDS):
            return current_category

        if current_category == "就业补贴" and any(keyword in title_text for keyword in ENTREPRENEUR_KEYWORDS):
            return "创业扶持"
        if current_category == "就业补贴" and any(keyword in title_text for keyword in HOUSING_KEYWORDS):
            return "落户/住房相关支持"
        if current_category in {"就业补贴", "落户/住房相关支持"} and any(
            keyword in title_text for keyword in TALENT_KEYWORDS
        ):
            return "人才补贴"
        if current_category == "就业补贴" and any(keyword in title_text for keyword in INTERNSHIP_KEYWORDS):
            return "实习/见习"
        if current_category == "就业补贴" and any(keyword in title_text for keyword in TRAINING_KEYWORDS):
            return "职业培训"
        if current_category == "就业补贴" and any(
            keyword in title_text for keyword in ENTERPRISE_ABSORB_KEYWORDS
        ):
            return "企业吸纳毕业生补贴"
        return current_category

    if any(keyword in combined for keyword in ENTERPRISE_ABSORB_KEYWORDS):
        return "企业吸纳毕业生补贴"
    if any(keyword in combined for keyword in INTERNSHIP_KEYWORDS):
        return "实习/见习"
    if any(keyword in combined for keyword in ENTREPRENEUR_KEYWORDS):
        return "创业扶持"
    if any(keyword in combined for keyword in TALENT_KEYWORDS):
        return "人才补贴"
    if any(keyword in combined for keyword in HOUSING_KEYWORDS):
        return "落户/住房相关支持"
    if any(keyword in combined for keyword in TRAINING_KEYWORDS):
        return "职业培训"
    return current_category
