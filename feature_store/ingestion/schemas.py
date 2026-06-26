from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

class RawEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: Literal["click", "purchase", "view", "search", "add_to_cart"]
    user_id: str
    item_id: str
    category: str
    price: Optional[float] = None
    quantity: Optional[int] = None
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    platform: Literal["web", "mobile", "tablet"]
    region: Literal["us-east", "us-west", "eu-west", "ap-south"]

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "category": self.category,
            "price": self.price,
            "quantity": self.quantity,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "platform": self.platform,
            "region": self.region,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RawEvent":
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
