import aiosqlite

from .repositories import (
    ConversationParticipantsRepository,
    ConversationParticipantsRepositoryImpl,
    ConversationsRepository,
    ConversationsRepositoryImpl,
)


def provide_conversations_repository(
    db_connection: aiosqlite.Connection,
) -> ConversationsRepository:
    return ConversationsRepositoryImpl(db_connection)


def provide_conversation_participants_repository(
    db_connection: aiosqlite.Connection,
) -> ConversationParticipantsRepository:
    return ConversationParticipantsRepositoryImpl(db_connection)
