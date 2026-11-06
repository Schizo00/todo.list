from sqlalchemy import select
from sqlalchemy.orm import Session

from app.model import Todo
from app.tables import TodoRow


def list_todos(db: Session) -> dict[str, list[Todo]]:
    rows = db.scalars(select(TodoRow).order_by(TodoRow.created_at)).all()
    return {"todos": [Todo.model_validate(row) for row in rows]}