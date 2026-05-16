from sqlalchemy.orm import Session
from typing import Any, Dict

def create(db: Session, obj: Any):
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update(db: Session, obj: Any, data: Dict):
    for field, value in data.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, obj: Any):
    db.delete(obj)
    db.commit()
    