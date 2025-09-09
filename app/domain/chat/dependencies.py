import aiosqlite

from .repositories import (
    ConversationParticipantsRepository,
    ConversationParticipantsRepositoryImpl,
    ConversationsRepository,
    ConversationsRepositoryImpl,
    MessageAttachmentsRepository,
    MessageAttachmentsRepositoryImpl,
    MessagesRepository,
    MessagesRepositoryImpl,
)


def provide_conversations_repository(
    db_connection: aiosqlite.Connection,
) -> ConversationsRepository:
    return ConversationsRepositoryImpl(db_connection)


def provide_conversation_participants_repository(
    db_connection: aiosqlite.Connection,
) -> ConversationParticipantsRepository:
    return ConversationParticipantsRepositoryImpl(db_connection)


def provide_messages_repository(
    db_connection: aiosqlite.Connection,
) -> MessagesRepository:
    return MessagesRepositoryImpl(db_connection)


def provide_message_attachments_repository(
    db_connection: aiosqlite.Connection,
) -> MessageAttachmentsRepository:
    return MessageAttachmentsRepositoryImpl(db_connection)
