from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Iterable


STOPWORDS = {
    "an",
    "ban",
    "biet",
    "cho",
    "co",
    "cua",
    "do",
    "gan",
    "hay",
    "hong",
    "khong",
    "khi",
    "la",
    "lam",
    "luon",
    "mot",
    "muon",
    "nao",
    "nha",
    "nha_hang",
    "nhahang",
    "o",
    "quan",
    "quan_an",
    "quanh",
    "tai",
    "thich",
    "toi",
    "va",
    "voi",
    "nhung",
    "nay",
    "phai",
    "gi",
}

CUISINE_PATTERNS = {
    "món việt": ["viet", "com nha", "quan com", "com tam", "bun", "pho", "hu tieu", "banh cuon", "banh xeo"],
    "món nhật": ["nhat", "sushi", "sashimi", "ramen", "udon", "izakaya", "omakase"],
    "món hàn": ["han", "han quoc", "tokbokki", "tteok", "tteokbokki", "kimchi", "korean", "soju", "bbq han"],
    "món thái": ["thai", "tom yum", "pad thai", "thai lan"],
    "món trung hoa": ["trung hoa", "dim sum", "sieu cay trung", "lau trung", "chinese"],
    "bbq / nướng": ["nuong", "bbq", "grill", "thit nuong", "yakitori"],
    "lẩu": ["lau", "hotpot", "hot pot"],
    "hải sản": ["hai san", "seafood", "quan oc", "oc", "cua bien", "tom hum", "tom", "muc"],
    "chay / healthy": ["chay", "healthy", "salad", "eat clean", "vegetarian"],
    "cà phê / brunch": ["ca phe", "coffee", "cafe", "brunch", "tra sua", "bakery"],
    "pizza / Âu": ["pizza", "pasta", "steak", "italy", "italian", "western"],
    "buffet": ["buffet"],
}

AMBIENCE_PATTERNS = {
    "yen_tinh": ["yen tinh", "thu gian", "nhe nhang", "it on", "doc sach", "lam viec"],
    "am_cung": ["am cung", "cozy", "nho xinh", "de thuong", "ap ap"],
    "lang_man": ["hen ho", "lang man", "romantic", "anniversary", "dating"],
    "view_dep": ["view dep", "song ao", "rooftop", "skyline", "ngam canh"],
    "sang_trong": ["sang trong", "fine dining", "cao cap", "luxury"],
    "dong_vui": ["dong vui", "nhon nhip", "vui ve", "party"],
}

AMENITY_PATTERNS = {
    "do_xe": ["do xe", "giu xe", "bai xe", "parking"],
    "o_cam": ["o cam", "cam sac", "sac laptop", "work friendly"],
    "wifi": ["wifi", "internet", "mang manh"],
    "phong_rieng": ["phong rieng", "vip", "private room"],
    "ngoai_troi": ["ngoai troi", "san vuon", "ban cong", "terrace"],
    "may_lanh": ["may lanh", "lanh", "indoor"],
    "tre_em": ["tre em", "ghe tre em", "kids", "kid friendly"],
}

OCCASION_PATTERNS = {
    "hen_ho": ["hen ho", "dating", "lang man", "couple"],
    "gia_dinh": ["gia dinh", "tre em", "kids", "bo me"],
    "ban_be": ["ban be", "tu tap", "hop mat", "gap go"],
    "lam_viec": ["lam viec", "meeting", "hoc bai", "workspace"],
    "an_dem": ["an dem", "khuya", "late night"],
    "nhom_dong": ["nhom", "dong nguoi", "team", "party", "sinh nhat"],
    "sinh_nhat": ["sinh nhat", "birthday"],
}

WEATHER_PATTERNS = {
    "troi_mua": ["troi mua", "mua", "tranh mua", "tranh lanh"],
    "troi_nong": ["nong", "mat me", "giai nhiet"],
}

BUDGET_PATTERNS = {
    "binh_dan": ["gia re", "binh dan", "sinh vien", "hssv", "tiet kiem"],
    "trung_binh": ["vua tui tien", "gia hop ly", "tam trung"],
    "cao_cap": ["sang trong", "cao cap", "fine dining", "xin xo"],
}

PREFERENCE_PATTERNS = {
    "easy_to_eat": ["de an", "ngon ngon", "on khong", "chan an", "khong biet an gi", "co gi an"],
    "light_meal": ["an nhe", "mon nhe", "nhe bung", "vua an com", "an com roi", "chan an"],
    "healthy": ["healthy", "eat clean", "it calo", "low calorie", "tot cho suc khoe"],
    "filling": ["no bung", "that no", "an no"],
    "less_popular": ["it pho bien", "la la", "quan moi", "doi vi"],
    "quick_service": ["an nhanh", "phuc vu nhanh", "len mon nhanh", "mang di"],
    "comfort_food": ["comfort food", "am bung", "de chiu"],
    "cooling_food": ["lam mat", "giai nhiet", "mat co the"],
    "vegetarian_option": ["nguoi an chay", "co an chay", "mon chay"],
    "kid_friendly": ["tre em", "kids", "ghe tre em"],
    "group_work": ["lam viec nhom", "hoc nhom", "meeting nhom"],
    "outdoor_seating": ["ngoai troi", "san vuon", "ban cong"],
    "parking": ["xe may", "do xe", "giu xe", "bai xe"],
    "soupy_food": ["do nuoc", "mon nuoc", "co nuoc"],
}

DISH_PATTERNS = {
    "mì trộn": ["mi tron"],
    "mì cay": ["mi cay"],
    "cơm tấm": ["com tam"],
    "bún bò Huế": ["bun bo hue", "bun bo"],
}

DISTRICT_PATTERNS = [
    (re.compile(r"\b(q\.?|quan)\s*(\d{1,2})\b"), lambda match: f"quan-{match.group(2)}"),
    (re.compile(r"\bthu duc\b"), lambda match: "tp-thu-duc"),
    (re.compile(r"\bbinh thanh\b"), lambda match: "quan-binh-thanh"),
    (re.compile(r"\bbinh tan\b"), lambda match: "quan-binh-tan"),
    (re.compile(r"\bphu nhuan\b"), lambda match: "quan-phu-nhuan"),
    (re.compile(r"\btan binh\b"), lambda match: "quan-tan-binh"),
    (re.compile(r"\btan phu\b"), lambda match: "quan-tan-phu"),
    (re.compile(r"\bgovap\b"), lambda match: "quan-go-vap"),
    (re.compile(r"\bgo vap\b"), lambda match: "quan-go-vap"),
    (re.compile(r"\bbinh chanh\b"), lambda match: "huyen-binh-chanh"),
    (re.compile(r"\bnha be\b"), lambda match: "huyen-nha-be"),
    (re.compile(r"\bhoc mon\b"), lambda match: "huyen-hoc-mon"),
    (re.compile(r"\bcu chi\b"), lambda match: "huyen-cu-chi"),
    (re.compile(r"\bcan gio\b"), lambda match: "huyen-can-gio"),
]

NUMBER_WORDS = {
    "mot": 1,
    "hai": 2,
    "ba": 3,
    "bon": 4,
    "tu": 4,
    "nam": 5,
    "sau": 6,
    "bay": 7,
    "tam": 8,
    "chin": 9,
    "muoi": 10,
}


@dataclass
class QueryIntent:
    original_query: str
    normalized_query: str
    keywords: list[str] = field(default_factory=list)
    cuisines: list[str] = field(default_factory=list)
    districts: list[str] = field(default_factory=list)
    ambience_tags: list[str] = field(default_factory=list)
    amenity_tags: list[str] = field(default_factory=list)
    occasion_tags: list[str] = field(default_factory=list)
    weather_tags: list[str] = field(default_factory=list)
    price_min: int | None = None
    price_max: int | None = None
    budget_label: str | None = None
    group_size: int | None = None
    open_now: bool | None = None
    excluded_cuisines: list[str] = field(default_factory=list)
    excluded_keywords: list[str] = field(default_factory=list)
    preference_tags: list[str] = field(default_factory=list)
    dish_terms: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    walking_only: bool = False
    parser_mode: str = "heuristic"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def merged_with(self, previous: "QueryIntent | None") -> "QueryIntent":
        if previous is None:
            return self
        return QueryIntent(
            original_query=self.original_query,
            normalized_query=self.normalized_query,
            keywords=_merge_lists(previous.keywords, self.keywords),
            cuisines=_merge_lists(previous.cuisines, self.cuisines),
            districts=_merge_lists(previous.districts, self.districts),
            ambience_tags=_merge_lists(previous.ambience_tags, self.ambience_tags),
            amenity_tags=_merge_lists(previous.amenity_tags, self.amenity_tags),
            occasion_tags=_merge_lists(previous.occasion_tags, self.occasion_tags),
            weather_tags=_merge_lists(previous.weather_tags, self.weather_tags),
            price_min=self.price_min if self.price_min is not None else previous.price_min,
            price_max=self.price_max if self.price_max is not None else previous.price_max,
            budget_label=self.budget_label or previous.budget_label,
            group_size=self.group_size if self.group_size is not None else previous.group_size,
            open_now=self.open_now if self.open_now is not None else previous.open_now,
            excluded_cuisines=_merge_lists(previous.excluded_cuisines, self.excluded_cuisines),
            excluded_keywords=_merge_lists(previous.excluded_keywords, self.excluded_keywords),
            preference_tags=_merge_lists(previous.preference_tags, self.preference_tags),
            dish_terms=_merge_lists(previous.dish_terms, self.dish_terms),
            conflicts=_merge_lists(previous.conflicts, self.conflicts),
            walking_only=self.walking_only or previous.walking_only,
            parser_mode=self.parser_mode,
            notes=_merge_lists(previous.notes, self.notes),
        )


def normalize_text(text: object) -> str:
    if text is None:
        text = ""
    elif isinstance(text, float) and math.isnan(text):
        text = ""
    else:
        text = str(text)
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.replace("đ", "d")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    text = re.sub(r"\bmy\b", "mi", text)
    text = re.sub(r"\bhssv\b", "sinh vien", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return [token for token in normalize_text(text).split() if len(token) > 1 and token not in STOPWORDS]


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output


def extract_district_slug_from_text(text: object) -> str | None:
    normalized = normalize_text(text)
    if not normalized:
        return None
    for pattern, mapper in DISTRICT_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return mapper(match)
    return None


def haversine_km(
    latitude_a: float | None,
    longitude_a: float | None,
    latitude_b: float | None,
    longitude_b: float | None,
) -> float | None:
    if None in {latitude_a, longitude_a, latitude_b, longitude_b}:
        return None
    radius_km = 6371.0
    lat1 = math.radians(float(latitude_a))
    lon1 = math.radians(float(longitude_a))
    lat2 = math.radians(float(latitude_b))
    lon2 = math.radians(float(longitude_b))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def infer_cuisines(*texts: str) -> list[str]:
    normalized = " ".join(normalize_text(text) for text in texts if text)
    matches: list[str] = []
    for label, patterns in CUISINE_PATTERNS.items():
        if any(_contains_pattern(normalized, pattern) for pattern in patterns):
            matches.append(label)
    return unique_preserve_order(matches)


def infer_semantic_tags(*texts: str) -> list[str]:
    normalized = " ".join(normalize_text(text) for text in texts if text)
    return unique_preserve_order(
        [
            *_match_patterns(normalized, AMBIENCE_PATTERNS),
            *_match_patterns(normalized, AMENITY_PATTERNS),
            *_match_patterns(normalized, OCCASION_PATTERNS),
            *_match_patterns(normalized, WEATHER_PATTERNS),
        ]
    )


def parse_query_heuristically(query: str) -> QueryIntent:
    normalized = normalize_text(query)
    keywords = tokenize(query)
    cuisines = infer_cuisines(query)
    if "healthy" in normalized and "chay" not in normalized:
        cuisines = [cuisine for cuisine in cuisines if cuisine != "chay / healthy"]
    if "nguoi an chay" in normalized:
        cuisines = [cuisine for cuisine in cuisines if cuisine != "chay / healthy"]
    districts: list[str] = []
    for pattern, mapper in DISTRICT_PATTERNS:
        for match in pattern.finditer(normalized):
            districts.append(mapper(match))

    ambience_tags = _match_patterns(normalized, AMBIENCE_PATTERNS)
    amenity_tags = _match_patterns(normalized, AMENITY_PATTERNS)
    occasion_tags = _match_patterns(normalized, OCCASION_PATTERNS)
    weather_tags = _match_patterns(normalized, WEATHER_PATTERNS)
    price_min, price_max, budget = _parse_price(normalized)
    group_size = _parse_group_size(normalized)
    open_now = (
        True
        if any(phrase in normalized for phrase in ["dang mo", "mo ngay", "mo khuya", "gio nay", "dem khuya", "con quan nao mo"])
        else None
    )
    excluded_cuisines = _extract_excluded_cuisines(normalized)
    excluded_keywords = _extract_excluded_keywords(normalized)
    preference_tags = _match_patterns(normalized, PREFERENCE_PATTERNS)
    dish_terms = _match_patterns(normalized, DISH_PATTERNS)
    if "troi_nong" in weather_tags:
        preference_tags = unique_preserve_order([*preference_tags, "cooling_food"])
    if "troi_mua" in weather_tags:
        preference_tags = unique_preserve_order([*preference_tags, "comfort_food"])
    walking_only = any(phrase in normalized for phrase in ["di bo", "pham vi di bo", "walking"])
    conflicts = _detect_conflicts(normalized, price_max, budget, preference_tags, walking_only)

    notes: list[str] = []
    if len(keywords) < 2 and not cuisines and not districts:
        notes.append("Truy vấn khá ngắn, nên gợi ý người dùng mô tả chi tiết hơn.")
    if not any([cuisines, districts, ambience_tags, amenity_tags, occasion_tags, weather_tags, price_min, price_max]):
        notes.append("Không trích xuất được nhiều thực thể mạnh, nên ưu tiên lexical fallback.")

    return QueryIntent(
        original_query=query,
        normalized_query=normalized,
        keywords=keywords,
        cuisines=cuisines,
        districts=unique_preserve_order(districts),
        ambience_tags=ambience_tags,
        amenity_tags=amenity_tags,
        occasion_tags=occasion_tags,
        weather_tags=weather_tags,
        price_min=price_min,
        price_max=price_max,
        budget_label=budget,
        group_size=group_size,
        open_now=open_now,
        excluded_cuisines=excluded_cuisines,
        excluded_keywords=excluded_keywords,
        preference_tags=preference_tags,
        dish_terms=dish_terms,
        conflicts=conflicts,
        walking_only=walking_only,
        parser_mode="heuristic",
        notes=notes,
    )


def _match_patterns(normalized_text: str, patterns_map: dict[str, list[str]]) -> list[str]:
    return unique_preserve_order(
        label
        for label, patterns in patterns_map.items()
        if any(_contains_pattern(normalized_text, pattern) for pattern in patterns)
    )


def _contains_pattern(normalized_text: str, pattern: str) -> bool:
    return re.search(rf"\b{re.escape(normalize_text(pattern))}\b", normalized_text) is not None


def _parse_price(normalized_text: str) -> tuple[int | None, int | None, str | None]:
    between_match = re.search(r"(\d{2,3})\s*(k|000)?\s*(?:-|den|toi|~)\s*(\d{2,3})\s*(k|000)?", normalized_text)
    if between_match:
        low = _normalize_price_number(between_match.group(1), between_match.group(2))
        high = _normalize_price_number(between_match.group(3), between_match.group(4))
        return low, high, None

    under_match = re.search(r"(duoi|toi da|max)\s*(\d{2,3})\s*(k|000)?", normalized_text)
    if under_match:
        high = _normalize_price_number(under_match.group(2), under_match.group(3))
        return None, high, None

    remaining_budget_match = re.search(r"(chi con|con|ngan sach)\s*(\d{2,3})\s*(k|000)?", normalized_text)
    if remaining_budget_match:
        high = _normalize_price_number(remaining_budget_match.group(2), remaining_budget_match.group(3))
        return None, high, None

    over_match = re.search(r"(tren|tu)\s*(\d{2,3})\s*(k|000)?", normalized_text)
    if over_match:
        low = _normalize_price_number(over_match.group(2), over_match.group(3))
        return low, None, None

    for label, patterns in BUDGET_PATTERNS.items():
        if any(_contains_pattern(normalized_text, pattern) for pattern in patterns):
            return None, None, label
    return None, None, None


def _normalize_price_number(number_text: str, suffix: str | None) -> int:
    base = int(number_text)
    if suffix == "k" or (suffix is None and base < 1000):
        return base * 1000
    return base


def _parse_group_size(normalized_text: str) -> int | None:
    for digit_match in re.finditer(r"(\d{1,2})\s*(nguoi|ban)", normalized_text):
        suffix = normalized_text[digit_match.end():].lstrip()
        if suffix.startswith("an chay"):
            continue
        return int(digit_match.group(1))

    for word, value in NUMBER_WORDS.items():
        match = re.search(rf"\b{word}\s*(nguoi|ban)\b", normalized_text)
        if match and not normalized_text[match.end():].lstrip().startswith("an chay"):
            return value
    return None


def _extract_excluded_cuisines(normalized_text: str) -> list[str]:
    excluded: list[str] = []
    negative_cues = ["khong an", "khong phai", "dung goi y", "bo qua", "ghet", "tranh"]
    for cuisine, patterns in CUISINE_PATTERNS.items():
        for pattern in patterns:
            if any(f"{cue} {pattern}" in normalized_text for cue in negative_cues):
                excluded.append(cuisine)
                break
    if any(phrase in normalized_text for phrase in ["dung goi y do han", "dung goi y mon han", "khong an do han"]):
        excluded.append("món hàn")
    return unique_preserve_order(excluded)


def _extract_excluded_keywords(normalized_text: str) -> list[str]:
    excluded: list[str] = []
    if any(
        phrase in normalized_text
        for phrase in ["ghet an cay", "khong an cay", "khong cay", "it cay", "khong phai mi cay", "dung goi y mi cay"]
    ):
        excluded.extend(["cay", "mi cay"])
    if any(phrase in normalized_text for phrase in ["vua an com", "an com roi", "khong an com"]):
        excluded.append("com")
    return unique_preserve_order(excluded)


def _detect_conflicts(
    normalized_text: str,
    price_max: int | None,
    budget_label: str | None,
    preference_tags: list[str],
    walking_only: bool,
) -> list[str]:
    conflicts: list[str] = []
    if "buffet" in normalized_text and price_max is not None and price_max <= 30_000:
        conflicts.append("Buffet dưới 30k khá khó đáp ứng; hệ thống sẽ ưu tiên lựa chọn gần ngân sách nhất.")
    if any(word in normalized_text for word in ["sang trong", "cao cap", "fine dining"]) and budget_label == "binh_dan":
        conflicts.append("Yêu cầu sang trọng và giá sinh viên khá mâu thuẫn; hệ thống sẽ ưu tiên quán có không gian tốt nhưng giá mềm.")
    if "filling" in preference_tags and "healthy" in preference_tags and any(
        phrase in normalized_text for phrase in ["it calo", "low calorie"]
    ):
        conflicts.append("No bụng nhưng ít calo cần đánh đổi; hệ thống sẽ ưu tiên món nhiều rau, đạm hoặc phần ăn vừa phải.")
    radius_match = re.search(r"(\d+(?:\.\d+)?)\s*km\b", normalized_text)
    if walking_only and radius_match and float(radius_match.group(1)) > 1.5:
        conflicts.append(
            f"Phạm vi đi bộ {radius_match.group(1)}km là khá xa; hệ thống giới hạn khoảng đi bộ thực tế ở 1.5km."
        )
    return conflicts


def _merge_lists(first: list[str], second: list[str]) -> list[str]:
    return unique_preserve_order([*first, *second])
