from app.model import Todo
from datetime import datetime
from uuid import uuid4


def list_todos():
    return {"todos": Todo(
        id=uuid4(),
        title="Sample Todo",
        description="This is a sample todo item.",
        done=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )}
