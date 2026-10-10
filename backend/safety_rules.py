from __future__ import annotations

from foodkeeper import FOODKEEPER_DATA

DANGER_ZONE_MIN_C = 4.4
DANGER_ZONE_MAX_C = 60
HOT_DAY_C = 32.2

UNIT_TO_DAYS = {
    "hour": 1 / 24,
    "hours": 1 / 24,
    "day": 1,
    "days": 1,
    "week": 7,
    "weeks": 7,
    "month": 30,
    "months": 30,
    "year": 365,
    "years": 365,
}


def _limit(product: dict, condition: str) -> tuple[float | None, str | None]:
    for prefix in (f"DOP_{condition}", condition):
        metric = product.get(f"{prefix}_Metric")
        maximum = product.get(f"{prefix}_Max")
        if isinstance(maximum, (int, float)) and metric:
            normalized_metric = metric.strip().casefold()
            days_per_unit = UNIT_TO_DAYS.get(normalized_metric)
            if days_per_unit is not None:
                return maximum * days_per_unit, f"{maximum:g} {metric}"
            return None, f"Follow the package label ({metric})"
    return None, None


def _out_of_range(temperature: float, days_stored: float) -> bool:
    return temperature < -30 or temperature > 60 or days_stored > 365


def _base_result(temperature: float, days_stored: float) -> dict:
    out_of_range = _out_of_range(temperature, days_stored)
    return {
        "risk": "Low",
        "basis": "",
        "recommendation": "",
        "confidence": "Moderate",
        "confidence_note": (
            "This is a rule-based result, not a statistical probability. "
            "FoodKeeper durations may depend on whether food is opened and how it was prepared."
        ),
        "out_of_range": out_of_range,
        "range_warning": (
            "Conditions are outside the assessment range. Treat this result as limited "
            "guidance and consult an authoritative food-safety source."
            if out_of_range
            else None
        ),
        "source": FOODKEEPER_DATA["url"],
        "storage_guidance": None,
    }


def assess_food(product: dict, temperature: float, days_stored: float) -> dict:
    """Combine USDA danger-zone limits with the selected FoodKeeper product entry."""
    hours_stored = days_stored * 24
    result = _base_result(temperature, days_stored)
    refrigerator_days, refrigerator_label = _limit(product, "Refrigerate")
    pantry_days, pantry_label = _limit(product, "Pantry")
    freezer_days, freezer_label = _limit(product, "Freeze")
    is_shelf_stable = (
        refrigerator_days is None
        and refrigerator_label is None
        and (pantry_days is not None or pantry_label is not None)
    )

    if temperature <= -18:
        result.update(
            basis="The food is at or below 0°F (-18°C), the recommended freezer temperature.",
            recommendation=(
                "Keep it continuously frozen. FoodKeeper's freezer duration is a quality "
                "guide, not a safety deadline."
            ),
            confidence="High",
            storage_guidance=(
                f"FoodKeeper quality guide: {freezer_label}."
                if freezer_label
                else "FoodKeeper does not list a freezer duration for this item."
            ),
        )
        return result

    if DANGER_ZONE_MIN_C <= temperature < DANGER_ZONE_MAX_C:
        if is_shelf_stable:
            exceeded = pantry_days is not None and days_stored > pantry_days
            result.update(
                risk=(
                    "Critical" if pantry_days is not None and days_stored > pantry_days * 2 else "High"
                )
                if exceeded
                else "Low",
                basis=(
                    f"The selected FoodKeeper item has no refrigerated storage limit and "
                    f"has pantry guidance ({pantry_label})."
                ),
                recommendation=(
                    "Discard the item if it is beyond its storage guidance; follow the "
                    "product label and do not use food with damaged packaging."
                    if exceeded
                    else "Follow the package label. This result applies only while the item "
                    "is unopened and stored as directed."
                ),
                confidence="Limited",
                confidence_note=(
                    "The check cannot tell whether the package is opened, damaged, or past "
                    "its printed date."
                ),
                storage_guidance=f"FoodKeeper pantry guide: {pantry_label}.",
            )
            return result

        allowed_hours = 1 if temperature > HOT_DAY_C else 2
        exceeded = hours_stored > allowed_hours
        result.update(
            risk="Critical" if exceeded else "High",
            basis=(
                f"{temperature:g}°C is in the USDA danger zone (40–140°F / "
                f"{DANGER_ZONE_MIN_C:g}–{DANGER_ZONE_MAX_C:g}°C). The unrefrigerated "
                f"limit is {allowed_hours} hour{'s' if allowed_hours != 1 else ''} at this "
                f"temperature; the reported duration is {hours_stored:g} hour"
                f"{'s' if hours_stored != 1 else ''}."
            ),
            recommendation=(
                "Discard perishable food that exceeded the time limit. Do not taste it to "
                "determine whether it is safe."
                if exceeded
                else "Return perishable food to refrigeration immediately; do not exceed "
                "the USDA time limit."
            ),
            confidence="High",
        )
        return result

    if temperature >= DANGER_ZONE_MAX_C:
        result.update(
            risk="Medium",
            basis="The temperature is at or above 140°F (60°C), the USDA hot-holding threshold.",
            recommendation=(
                "Keep hot food continuously at or above 60°C (140°F). This check does not "
                "verify cooking temperature or how the food was handled earlier."
            ),
            confidence="Limited",
            confidence_note="Hot-holding guidance does not assess cooking or earlier handling.",
        )
        return result

    if temperature < DANGER_ZONE_MIN_C:
        if refrigerator_days is not None:
            exceeded = days_stored > refrigerator_days
            result.update(
                risk=(
                    "Critical"
                    if days_stored > refrigerator_days * 2
                    else "High"
                )
                if exceeded
                else "Low",
                basis=(
                    f"At refrigerator temperature, the selected FoodKeeper item has a "
                    f"{refrigerator_label} storage guide. The reported duration is "
                    f"{days_stored:g} day{'s' if days_stored != 1 else ''}."
                ),
                recommendation=(
                    "Discard food beyond this item's FoodKeeper refrigerator guide."
                    if exceeded
                    else "Keep the refrigerator at or below 4°C (40°F) and follow the "
                    "product label."
                ),
                confidence="Moderate",
                storage_guidance=f"FoodKeeper refrigerator guide: {refrigerator_label}.",
            )
            return result

        result.update(
            basis=(
                "The selected FoodKeeper item does not provide a numeric refrigerator "
                "duration; use the product's printed date and storage directions."
            ),
            recommendation="Keep the refrigerator at or below 4°C (40°F) and follow the label.",
            confidence="Limited",
            confidence_note="No numeric refrigerator storage time is available for this item.",
        )
        return result

    if is_shelf_stable:
        exceeded = pantry_days is not None and days_stored > pantry_days
        result.update(
            risk=(
                "Critical" if pantry_days is not None and days_stored > pantry_days * 2 else "High"
            )
            if exceeded
            else "Low",
            basis=(
                f"The selected FoodKeeper item has no refrigerated storage limit and "
                f"has pantry guidance ({pantry_label})."
            ),
            recommendation=(
                "Discard the item if it is beyond its storage guidance; follow the "
                "product label and do not use food with damaged packaging."
                if exceeded
                else "Follow the package label. This result applies only while the item "
                "is unopened and stored as directed."
            ),
            confidence="Limited",
            confidence_note=(
                "The check cannot tell whether the package is opened, damaged, or past "
                "its printed date."
            ),
            storage_guidance=f"FoodKeeper pantry guide: {pantry_label}.",
        )
        return result

    result.update(
        basis="No specific FoodKeeper storage duration is listed for these conditions.",
        recommendation="Follow the product label and keep perishable food at or below 4°C (40°F).",
        confidence="Limited",
        confidence_note="The selected item's storage data does not cover these conditions.",
    )
    return result
