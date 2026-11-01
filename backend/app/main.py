from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.netconf_service import (
    get_departments,
    get_policies,
    update_policy_action,
    upsert_policy
)

from app.services.policy_adapter import reconcile_policies

from app.services.monitoring_service import get_network_metrics

from app.services.activity_service import (
    log_activity,
    get_recent_activities
)

from app.services.gemini_service import interpret_intent


app = FastAPI(
    title="Intent-Based Campus Network Management",
    description="AI-powered intent-driven campus network configuration and management",
    version="4.0"
)


# Request models

class IntentRequest(BaseModel):
    intent: str = Field(min_length=5, max_length=300)


class PolicyUpdateRequest(BaseModel):
    action: str = Field(pattern="^(allow|block)$")


# Home endpoint

@app.get("/")
def home():

    return {
        "message": "Campus Network Intent Engine is running",
        "version": "4.0",
        "status": "active"
    }


# Retrieve campus departments and network devices

@app.get("/api/departments")
def list_departments():

    try:
        departments = get_departments()

        return {
            "total": len(departments),
            "departments": departments
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve departments: {str(error)}"
        )


# Retrieve network policies

@app.get("/api/policies")
def list_policies():

    try:
        policies = get_policies()

        return {
            "total": len(policies),
            "policies": policies
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve policies: {str(error)}"
        )


# Update an existing policy

@app.patch("/api/policies/{policy_name}")
def change_policy(
    policy_name: str,
    request: PolicyUpdateRequest
):

    try:
        policies = get_policies()

        existing_policy = next(
            (
                policy for policy in policies
                if policy["name"] == policy_name
            ),
            None
        )

        if existing_policy is None:
            raise HTTPException(
                status_code=404,
                detail="Policy not found"
            )

        update_policy_action(
            policy_name=policy_name,
            action=request.action
        )

        updated_policies = get_policies()

        result = reconcile_policies(updated_policies)

        log_activity(
            event_type="POLICY_UPDATE",
            source=existing_policy["source"],
            destination=existing_policy["destination"],
            action=request.action.upper(),
            status="SUCCESS",
            description=f"Policy {policy_name} updated successfully"
        )

        return {
            "message": "Policy updated successfully",
            "policy_name": policy_name,
            "source": existing_policy["source"],
            "destination": existing_policy["destination"],
            "action": request.action.upper(),
            "netconf_status": "UPDATED",
            **result
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Policy update failed: {str(error)}"
        )


# Apply AI-powered natural-language network intent

@app.post("/api/intent/apply")
def apply_intent(request: IntentRequest):

    # Step 1: Interpret user intent using Gemini

    try:
        interpreted = interpret_intent(request.intent)

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"AI intent interpretation failed: {str(error)}"
        )

    # Step 2: Validate Gemini response

    if not isinstance(interpreted, dict):
        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid response"
        )

    if "error" in interpreted:
        raise HTTPException(
            status_code=400,
            detail=interpreted["error"]
        )

    source = interpreted.get("source")
    destination = interpreted.get("destination")
    action = interpreted.get("action")

    if action not in {"allow", "block"}:
        raise HTTPException(
            status_code=400,
            detail="AI returned an invalid network action"
        )

    if source == destination:
        raise HTTPException(
            status_code=400,
            detail="Source and destination departments must be different"
        )

    try:

        # Step 3: Validate departments against NETCONF

        departments = get_departments()

        allowed_departments = {
            department["name"]
            for department in departments
        }

        if (
            source not in allowed_departments
            or destination not in allowed_departments
        ):
            raise HTTPException(
                status_code=400,
                detail="Source or destination department does not exist"
            )

        # Step 4: Generate a unique policy name for the pair

        policy_name = f"{source}-to-{destination}"

        # Step 5: Create or update the NETCONF policy

        upsert_policy(
            policy_name=policy_name,
            source=source,
            destination=destination,
            action=action,
            enabled=True
        )

        # Step 6: Retrieve updated policies

        policies = get_policies()

        # Step 7: Apply policies to Open vSwitch

        result = reconcile_policies(policies)

        # Step 8: Record activity

        log_activity(
            event_type="INTENT",
            source=source,
            destination=destination,
            action=action.upper(),
            status="SUCCESS",
            description=request.intent
        )

        return {
            "intent": request.intent,
            "policy_name": policy_name,
            "interpreted_intent": {
                "source": source.upper(),
                "destination": destination.upper(),
                "action": action.upper()
            },
            "message": "AI-powered network intent applied successfully",
            "netconf_status": "UPDATED",
            **result
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Intent execution failed: {str(error)}"
        )


# Retrieve network monitoring information

@app.get("/api/monitoring")
def network_monitoring():

    try:
        metrics = get_network_metrics()

        return {
            "status": "success",
            "network": metrics
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve network metrics: {str(error)}"
        )


# Retrieve recent activity logs

@app.get("/api/activity")
def list_activities(
    limit: int = Query(default=20, ge=1, le=100)
):

    try:
        activities = get_recent_activities(limit)

        return {
            "total": len(activities),
            "activities": activities
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve activity logs: {str(error)}"
        )
