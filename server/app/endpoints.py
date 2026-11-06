from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.model import Todo, TodoCreate
from app.tables import TodoRow


def list_todos(db: Session) -> dict[str, list[Todo]]:
    rows = db.scalars(select(TodoRow).order_by(TodoRow.created_at)).all()
    return {"todos": [Todo.model_validate(row) for row in rows]}

def create_todo(db: Session, todo_create: TodoCreate) -> Todo:
    row = TodoRow(id=uuid4(), **todo_create.model_dump())
    db.add(row)
    db.commit()
    return Todo.model_validate(row)