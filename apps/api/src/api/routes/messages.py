from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.repositories.message_repository import MessageRepository
from src.schemas.message import MessageResponse

router = APIRouter(prefix='/conversations', tags=['messages'])


@router.get('/{conversation_id}/messages', response_model=list[MessageResponse])
def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    return MessageRepository(db).list_for_conversation(conversation_id)
