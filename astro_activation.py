from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter()

ASTRO_COMPUTATION_VERSION = "h2_2026_degree_based_v1"


SIGN_RANGES = {
    "Aries": (0.0, 30.0),
    "Taurus": (30.0, 60.0),
    "Gemini": (60.0, 90.0),
    "Cancer": (90.0, 120.0),
    "Leo": (120.0, 150.0),
    "Virgo": (150.0, 180.0),
    "Libra": (180.0, 210.0),
    "Scorpio": (210.0, 240.0),
    "Sagittarius": (240.0, 270.0),
    "Capricorn": (270.0, 300.0),
    "Aquarius": (300.0, 330.0),
    "Pisces": (330.0, 360.0),
}


CORE_TRANSITS = {
    "jupiter_cancer": {
        "transit": "Jupiter in Cancer",
        "planet": "Jupiter",
        "sign": "Cancer",
        "period": "June 9, 2025 — June 30, 2026",
        "role": "active May–June 2026 layer",
    },
    "jupiter_leo": {
        "transit": "Jupiter in Leo",
        "planet": "Jupiter",
        "sign": "Leo",
        "period": "June 30, 2026 — July 26, 2027",
        "role": "main July–December 2026 amplification axis",
    },
    "pluto_aquarius": {
        "transit": "Pluto in Aquarius",
        "planet": "Pluto",
        "sign": "Aquarius",
        "period": "November 19, 2024 — January 19, 2044",
        "role": "deep social / systemic / technological / power-structure layer",
    },
    "saturn_aries": {
        "transit": "Saturn in Aries",
        "planet": "Saturn",
        "sign": "Aries",
        "period": "February 13, 2026 — April 12, 2028",
        "role": "structure / discipline / maturity / self-command layer",
    },
    "neptune_aries": {
        "transit": "Neptune in Aries",
        "planet": "Neptune",
        "sign": "Aries",
        "period": "January 26, 2026 — March 23, 2039",
        "role": "vision / illusion / dissolution / unclear-action layer",
    },
    "uranus_gemini": {
        "transit": "Uranus in Gemini",
        "planet": "Uranus",
        "sign": "Gemini",
        "period": "April 26, 2026 — May 22, 2033",
        "role": "speed / communication / information / learning / technology layer",
    },
}


class AstroActivationMapRequest(BaseModel):
    order_id: Optional[str] = None
    house_system: Optional[str] = "Placidus"
    reading_period: Optional[Dict[str, str]] = Field(default_factory=dict)
    western_chart_data: Dict[str, Any]


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def extract_houses(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    western = payload.get("western_chart_data", payload)

    if isinstance(western, dict) and "houses" in western:
        houses = western["houses"]
    elif isinstance(western, dict) and "data" in western and "houses" in western["data"]:
        houses = western["data"]["houses"]
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not find houses in western_chart_data. "
                "Expected western_chart_data.houses or western_chart_data.data.houses."
            ),
        )

    if not isinstance(houses, list) or len(houses) != 12:
        raise HTTPException(
            status_code=400,
            detail=f"Expected exactly 12 houses, received {len(houses) if isinstance(houses, list) else 'invalid value'}.",
        )

    normalized = []

    for house in houses:
        try:
            house_id = int(house["house_id"])
            start_degree = float(house["start_degree"]) % 360
            end_degree = float(house["end_degree"]) % 360
        except (KeyError, TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid house object. Each house must include house_id, start_degree, end_degree. Received: {house}",
            )

        normalized.append(
            {
                "house_id": house_id,
                "start_degree": start_degree,
                "end_degree": end_degree,
                "sign": house.get("sign"),
            }
        )

    return sorted(normalized, key=lambda h: h["house_id"])


def expand_house_interval(house: Dict[str, Any]) -> List[Dict[str, Any]]:
    start = house["start_degree"]
    end = house["end_degree"]

    if start < end:
        return [
            {
                "house_id": house["house_id"],
                "from": start,
                "to": end,
            }
        ]

    if start > end:
        return [
            {
                "house_id": house["house_id"],
                "from": start,
                "to": 360.0,
            },
            {
                "house_id": house["house_id"],
                "from": 0.0,
                "to": end,
            },
        ]

    raise HTTPException(
        status_code=400,
        detail=f"Invalid house interval with identical start and end degrees for house {house['house_id']}.",
    )


def format_sign_degree(sign: str, absolute_degree: float) -> str:
    sign_start, sign_end = SIGN_RANGES[sign]

    degree = absolute_degree

    if degree < sign_start:
        degree = sign_start

    if degree > sign_end:
        degree = sign_end

    within_sign = degree - sign_start

    deg_int = int(within_sign)
    minutes = int(round((within_sign - deg_int) * 60))

    if minutes == 60:
        deg_int += 1
        minutes = 0

    return f"{sign} {deg_int}°{minutes:02d}′"


def split_sign_range_by_houses(sign: str, houses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if sign not in SIGN_RANGES:
        raise HTTPException(status_code=400, detail=f"Unknown sign: {sign}")

    sign_start, sign_end = SIGN_RANGES[sign]

    expanded_houses = []
    for house in houses:
        expanded_houses.extend(expand_house_interval(house))

    segments = []

    for interval in expanded_houses:
        overlap_start = max(sign_start, interval["from"])
        overlap_end = min(sign_end, interval["to"])

        if overlap_start < overlap_end:
            length = overlap_end - overlap_start

            segments.append(
                {
                    "house": int(interval["house_id"]),
                    "absolute_range": {
                        "from": round(overlap_start, 5),
                        "to": round(overlap_end, 5),
                    },
                    "sign_degree_range": (
                        f"{format_sign_degree(sign, overlap_start)}–"
                        f"{format_sign_degree(sign, overlap_end)}"
                    ),
                    "length_degrees": round(length, 5),
                }
            )

    if not segments:
        raise HTTPException(
            status_code=400,
            detail=f"No house segments found for sign {sign}. Check house cusp data.",
        )

    return sorted(segments, key=lambda s: s["absolute_range"]["from"])


def choose_primary_house(segments: List[Dict[str, Any]]) -> int:
    largest = max(segments, key=lambda s: s["length_degrees"])
    return int(largest["house"])


def ordinal(number: int) -> str:
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def build_transition_note(sign: str, segments: List[Dict[str, Any]]) -> Optional[str]:
    if len(segments) <= 1:
        return None

    first_house = segments[0]["house"]
    last_house = segments[-1]["house"]

    if first_house == last_house:
        return None

    return (
        f"The {sign} activation begins in the {ordinal(first_house)} house "
        f"and later moves into the {ordinal(last_house)} house."
    )


def build_activation_map(houses: List[Dict[str, Any]]) -> Dict[str, Any]:
    activation_map = {}

    for transit_key, config in CORE_TRANSITS.items():
        sign = config["sign"]
        sign_start, sign_end = SIGN_RANGES[sign]

        segments = split_sign_range_by_houses(sign, houses)
        primary_house = choose_primary_house(segments)

        activation_map[transit_key] = {
            "transit": config["transit"],
            "planet": config["planet"],
            "sign": sign,
            "period": config["period"],
            "role": config["role"],
            "sign_range_absolute": {
                "from": sign_start,
                "to": sign_end,
            },
            "activated_house_segments": segments,
            "primary_house": primary_house,
            "transition_note": build_transition_note(sign, segments),
        }

    summary_fields = {
        "cancer_house": activation_map["jupiter_cancer"]["primary_house"],
        "leo_house": activation_map["jupiter_leo"]["primary_house"],
        "aquarius_house": activation_map["pluto_aquarius"]["primary_house"],
        "aries_house": activation_map["saturn_aries"]["primary_house"],
        "gemini_house": activation_map["uranus_gemini"]["primary_house"],
    }

    return {
        "activation_map": activation_map,
        "summary_fields": summary_fields,
    }


@router.post("/compute-astro-activation-map")
async def compute_astro_activation_map(request: AstroActivationMapRequest):
    payload = model_to_dict(request)

    houses = extract_houses(payload)

    house_cusps = {
        str(house["house_id"]): {
            "start_degree": house["start_degree"],
            "end_degree": house["end_degree"],
            "sign": house.get("sign"),
        }
        for house in houses
    }

    activation_result = build_activation_map(houses)

    return {
        "order_id": request.order_id,
        "house_system": request.house_system,
        "reading_period": request.reading_period,
        "astro_computation_version": ASTRO_COMPUTATION_VERSION,
        "house_cusps": house_cusps,
        "activation_map": activation_result["activation_map"],
        "summary_fields": activation_result["summary_fields"],
    }
