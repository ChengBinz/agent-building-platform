"""Chat conversations API."""
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationOut,
    ConversationListItem,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationListItem])
async def list_conversations(
    agent_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    return await service.list_conversations(current_user.id, agent_id=agent_id)


@router.post("/conversations", response_model=ConversationOut, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    return await service.create_conversation(current_user.id, data)


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    return await service.get_conversation(current_user.id, conversation_id)


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    return await service.update_conversation(current_user.id, conversation_id, data)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    await service.delete_conversation(current_user.id, conversation_id)


@router.post("/conversations/{conversation_id}/send", response_model=SendMessageResponse)
async def send_message(
    conversation_id: uuid.UUID,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    return await service.send_message(current_user.id, conversation_id, data)


@router.post("/conversations/{conversation_id}/send-stream")
async def send_message_stream(
    conversation_id: uuid.UUID,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
):
    # 必须在 StreamingResponse 内部创建 session，否则生成器执行时 session 已关闭
    from app.db.session import async_session_factory

    async def stream_with_session():
        async with async_session_factory() as db:
            try:
                service = ChatService(db)
                async for chunk in service.send_message_stream(current_user.id, conversation_id, data):
                    if chunk == "data: [DONE]\n\n":
                        # 关键：先 commit，再把 [DONE] 推给前端。
                        # 否则前端收到 [DONE] 后立刻发 GET /conversations/{id}，
                        # 此时本事务还没提交，前端会拿到「空 messages」而看不到刚发的消息。
                        await db.commit()
                        yield chunk
                    else:
                        yield chunk
            except Exception as e:
                # 在 SSE 流中抛异常会让前端只看到 "network error"，
                # 这里捕获并以 data 事件传出错误，再正常结束流。
                await db.rollback()
                msg = str(e).replace("\n", " ")
                yield f"data: ❌ 服务器内部错误：{msg}\n\n"
                yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_with_session(),
        media_type="text/event-stream",
    )
