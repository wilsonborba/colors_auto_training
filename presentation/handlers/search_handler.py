from __future__ import annotations

from presentation.handlers.response_dto import PresentationResponseDTO

_PLANS: dict[str, dict] = {}


def create_plan(payload: dict) -> PresentationResponseDTO:
    plan_id = f"plan-{len(_PLANS) + 1}"
    plan = {
        "id": plan_id,
        "query": payload["query"],
        "status": "draft",
        "results": [],
    }
    _PLANS[plan_id] = plan
    return PresentationResponseDTO(status_code=201, message="Search plan created.", data=plan)


def generate_plan(plan_id: str) -> PresentationResponseDTO:
    plan = _PLANS.get(plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)

    plan["status"] = "generated"
    plan["results"] = [{"id": "result-1", "score": 0.95}]
    return PresentationResponseDTO(status_code=200, message="Search plan generated.", data=plan)


def run_plan(plan_id: str) -> PresentationResponseDTO:
    plan = _PLANS.get(plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)

    plan["status"] = "running"
    return PresentationResponseDTO(status_code=202, message="Search plan execution started.", data=plan)


def list_plans() -> PresentationResponseDTO:
    return PresentationResponseDTO(
        status_code=200,
        message="Search plans fetched successfully.",
        data=list(_PLANS.values()),
    )


def get_plan(plan_id: str) -> PresentationResponseDTO:
    plan = _PLANS.get(plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)

    return PresentationResponseDTO(status_code=200, message="Search plan fetched successfully.", data=plan)


def get_plan_results(plan_id: str) -> PresentationResponseDTO:
    plan = _PLANS.get(plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)

    return PresentationResponseDTO(
        status_code=200,
        message="Search plan results fetched successfully.",
        data=plan.get("results", []),
    )


def approve_plan(plan_id: str) -> PresentationResponseDTO:
    plan = _PLANS.get(plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)

    plan["status"] = "approved"
    return PresentationResponseDTO(status_code=200, message="Search plan approved.", data=plan)


def reject_plan(plan_id: str, reason: str | None) -> PresentationResponseDTO:
    plan = _PLANS.get(plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)

    plan["status"] = "rejected"
    plan["rejection_reason"] = reason
    return PresentationResponseDTO(status_code=200, message="Search plan rejected.", data=plan)


def bulk_action(plan_ids: list[str], action: str) -> PresentationResponseDTO:
    updated = []
    for plan_id in plan_ids:
        plan = _PLANS.get(plan_id)
        if not plan:
            continue
        plan["status"] = action
        updated.append(plan)

    return PresentationResponseDTO(
        status_code=200,
        message="Bulk action applied to search plans.",
        data={"updated_count": len(updated), "plans": updated},
    )
