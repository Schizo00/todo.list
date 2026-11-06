import logging
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.model import Todo, TodoCreate, TodoListParams, TodoPage, TodoUpdate
from app.tables import TodoRow

logger = logging.getLogger(__name__)

SORT_COLUMNS = {
    "created_at": TodoRow.created_at,
    "updated_at": TodoRow.updated_at,
    "title": TodoRow.title,
}


def _get_row(db: Session, todo_id: UUID) -> TodoRow:
    row = db.get(TodoRow, todo_id)
    if row is None:
        logger.info("Todo %s not found", todo_id)
        raise HTTPException(status_code=404, detail="Todo not found")
    return row


def list_todos(db: Session, params: TodoListParams) -> TodoPage:
    query = select(TodoRow)
    if params.done is not None:
        query = query.where(TodoRow.done == params.done)

    # Count the filtered rows before limit/offset, so clients know how many pages there are.
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    column = SORT_COLUMNS[params.sort]
    ordering = column.asc() if params.order == "asc" else column.desc()
    # id breaks ties, so rows with equal sort values keep a stable order across pages.
    query = query.order_by(ordering, TodoRow.id).limit(params.limit).offset(params.offset)
    rows = db.scalars(query).all()

    logger.debug("Listed %d of %d todos", len(rows), total)
    return TodoPage(
        todos=[Todo.model_validate(row) for row in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


def create_todo(db: Session, todo_create: TodoCreate) -> Todo:
    row = TodoRow(id=uuid4(), **todo_create.model_dump())
    db.add(row)
    db.commit()
    logger.info("Created todo %s", row.id)
    return Todo.model_validate(row)


def get_todo(db: Session, todo_id: UUID) -> Todo:
    row = _get_row(db, todo_id)

    return Todo.model_validate(row)


def update_todo(db: Session, todo_id: UUID, todo_update: TodoUpdate) -> Todo:
    row = _get_row(db, todo_id)

    for key, value in todo_update.model_dump(exclude_unset=True).items():
        setattr(row, key, value)

    db.commit()
    logger.info("Updated todo %s", todo_id)
    return Todo.model_validate(row)


def toggle_todo_status(db: Session, todo_id: UUID) -> Todo:
    row = _get_row(db, todo_id)

    row.done = not row.done
    db.commit()
    logger.info("Toggled todo %s done=%s", todo_id, row.done)
    return Todo.model_validate(row)


def delete_todo(db: Session, todo_id: UUID) -> None:
    row = _get_row(db, todo_id)

    db.delete(row)
    db.commit()
    logger.info("Deleted todo %s", todo_id)
