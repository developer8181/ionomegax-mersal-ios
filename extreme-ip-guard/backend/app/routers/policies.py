from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
from app.routers.auth import get_current_user

router = APIRouter(prefix="/policies", tags=["Security Policies"])

# In-memory policy store (in production, use database)
POLICIES_DB = [
    {
        "id": "pol-001",
        "name": "Block High-Risk Countries",
        "description": "Automatically block traffic from high-risk countries",
        "is_active": True,
        "priority": 10,
        "action": "block",
        "countries": ["KP", "IR"],
        "source_ip_range": None,
        "destination_ports": [],
        "protocols": [],
        "times_triggered": 245,
        "created_by": "admin",
        "created_at": "2026-05-01T00:00:00",
    },
    {
        "id": "pol-002",
        "name": "Rate Limit Suspicious IPs",
        "description": "Apply rate limiting to IPs with medium risk score",
        "is_active": True,
        "priority": 20,
        "action": "rate_limit",
        "risk_score_min": 40.0,
        "source_ip_range": None,
        "destination_ports": [],
        "protocols": [],
        "countries": [],
        "times_triggered": 89,
        "created_by": "admin",
        "created_at": "2026-05-01T00:00:00",
    },
    {
        "id": "pol-003",
        "name": "Monitor SSH/RDP Access",
        "description": "Alert on all SSH and RDP connection attempts",
        "is_active": True,
        "priority": 30,
        "action": "alert",
        "destination_ports": [22, 3389],
        "protocols": ["TCP"],
        "countries": [],
        "source_ip_range": None,
        "times_triggered": 512,
        "created_by": "analyst",
        "created_at": "2026-05-05T00:00:00",
    },
    {
        "id": "pol-004",
        "name": "Whitelist Internal Network",
        "description": "Allow all traffic from internal 192.168.x.x range",
        "is_active": True,
        "priority": 5,
        "action": "allow",
        "source_ip_range": "192.168.0.0/16",
        "destination_ports": [],
        "protocols": [],
        "countries": [],
        "times_triggered": 15432,
        "created_by": "admin",
        "created_at": "2026-04-01T00:00:00",
    },
    {
        "id": "pol-005",
        "name": "Block Tor Exit Nodes",
        "description": "Block all known Tor exit node IP addresses",
        "is_active": True,
        "priority": 15,
        "action": "block",
        "source_ip_range": None,
        "destination_ports": [],
        "protocols": [],
        "countries": [],
        "times_triggered": 67,
        "created_by": "admin",
        "created_at": "2026-05-10T00:00:00",
    },
]


class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    priority: int = 100
    action: str
    source_ip_range: Optional[str] = None
    destination_ip_range: Optional[str] = None
    destination_ports: List[int] = []
    protocols: List[str] = []
    countries: List[str] = []
    risk_score_min: Optional[float] = None


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    action: Optional[str] = None
    source_ip_range: Optional[str] = None
    destination_ports: Optional[List[int]] = None
    protocols: Optional[List[str]] = None
    countries: Optional[List[str]] = None


@router.get("")
async def list_policies(current_user: dict = Depends(get_current_user)):
    return {
        "policies": sorted(POLICIES_DB, key=lambda x: x["priority"]),
        "total": len(POLICIES_DB),
    }


@router.post("")
async def create_policy(
    policy: PolicyCreate,
    current_user: dict = Depends(get_current_user)
):
    new_policy = {
        "id": f"pol-{uuid.uuid4().hex[:8]}",
        "times_triggered": 0,
        "created_by": current_user["username"],
        "created_at": datetime.utcnow().isoformat(),
        **policy.dict(),
    }
    POLICIES_DB.append(new_policy)
    return {"policy": new_policy, "message": "Policy created successfully"}


@router.get("/{policy_id}")
async def get_policy(policy_id: str, current_user: dict = Depends(get_current_user)):
    policy = next((p for p in POLICIES_DB if p["id"] == policy_id), None)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policy": policy}


@router.put("/{policy_id}")
async def update_policy(
    policy_id: str,
    update: PolicyUpdate,
    current_user: dict = Depends(get_current_user)
):
    policy = next((p for p in POLICIES_DB if p["id"] == policy_id), None)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    policy.update(update_data)
    
    return {"policy": policy, "message": "Policy updated successfully"}


@router.delete("/{policy_id}")
async def delete_policy(policy_id: str, current_user: dict = Depends(get_current_user)):
    global POLICIES_DB
    policy = next((p for p in POLICIES_DB if p["id"] == policy_id), None)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    POLICIES_DB = [p for p in POLICIES_DB if p["id"] != policy_id]
    return {"message": "Policy deleted successfully"}


@router.post("/{policy_id}/toggle")
async def toggle_policy(policy_id: str, current_user: dict = Depends(get_current_user)):
    policy = next((p for p in POLICIES_DB if p["id"] == policy_id), None)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy["is_active"] = not policy["is_active"]
    return {
        "policy": policy,
        "message": f"Policy {'activated' if policy['is_active'] else 'deactivated'}"
    }
