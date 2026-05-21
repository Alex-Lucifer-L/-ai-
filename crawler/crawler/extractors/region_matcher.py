"""Rule-based region matcher for policy items."""

from dataclasses import dataclass


XIAMEN_DISTRICTS = (
    "思明区",
    "湖里区",
    "集美区",
    "海沧区",
    "同安区",
    "翔安区",
)


@dataclass(frozen=True)
class RegionMatch:
    region_name: str
    applicability_type: str
    applicability_note: str


class RegionMatcher:
    def match(self, text: str, publish_level: str | None = None) -> list[RegionMatch]:
        text = text or ""
        first_line = text.splitlines()[0] if text.splitlines() else ""
        title_matches = self._district_matches(first_line)
        if title_matches:
            return title_matches

        matches = self._district_matches(text)
        if len(matches) == len(XIAMEN_DISTRICTS):
            return [
                RegionMatch(
                    region_name="厦门市",
                    applicability_type="direct",
                    applicability_note="文本覆盖厦门各区，按厦门市级适用处理",
                )
            ]

        if matches:
            return matches

        if "各区" in first_line:
            return [
                RegionMatch(
                    region_name="厦门市",
                    applicability_type="direct",
                    applicability_note="措施名称出现“各区”，按厦门市级适用处理",
                )
            ]

        if "市级" in first_line:
            return [
                RegionMatch(
                    region_name="厦门市",
                    applicability_type="direct",
                    applicability_note="措施名称出现“市级”，按厦门市级适用处理",
                )
            ]

        if "省级" in first_line:
            return [
                RegionMatch(
                    region_name="福建省",
                    applicability_type="direct",
                    applicability_note="措施名称出现“省级”，按福建省级适用处理",
                )
            ]

        if "国家级" in first_line:
            return [
                RegionMatch(
                    region_name="中国",
                    applicability_type="direct",
                    applicability_note="措施名称出现“国家级”，按国家级适用处理",
                )
            ]

        if publish_level == "province" or "福建省" in text:
            return [
                RegionMatch(
                    region_name="福建省",
                    applicability_type="direct",
                    applicability_note="根据政策发布层级或文本内容识别为福建省级适用",
                )
            ]

        if publish_level == "country" or "中国" in text or "全国" in text:
            return [
                RegionMatch(
                    region_name="中国",
                    applicability_type="direct",
                    applicability_note="根据政策发布层级或文本内容识别为国家级适用",
                )
            ]

        if any(keyword in text for keyword in ("厦门", "在厦", "来厦", "入厦", "我市")) or publish_level == "city":
            return [
                RegionMatch(
                    region_name="厦门市",
                    applicability_type="direct",
                    applicability_note="根据政策发布层级或文本内容识别为厦门市级适用",
                )
            ]

        return []

    def _district_matches(self, text: str) -> list[RegionMatch]:
        matches: list[RegionMatch] = []
        for district_name in XIAMEN_DISTRICTS:
            if district_name in text:
                matches.append(
                    RegionMatch(
                        region_name=district_name,
                        applicability_type="direct",
                        applicability_note=f"文本中出现“{district_name}”",
                    )
                )
        return self._deduplicate(matches)

    def _deduplicate(self, matches: list[RegionMatch]) -> list[RegionMatch]:
        result: list[RegionMatch] = []
        seen: set[str] = set()
        for match in matches:
            if match.region_name in seen:
                continue
            seen.add(match.region_name)
            result.append(match)
        return result
