GET_OWN_CONVERSATIONS = "/api/v1/users/me/conversations"

CREATE_CONVERSATION = "/api/v1/conversations"
GET_CONVERSATION = "/api/v1/conversations/{conversation_id:int}"
UPDATE_CONVERSATION = "/api/v1/conversations/{conversation_id:int}"
DELETE_CONVERSATION = "/api/v1/conversations/{conversation_id:int}"

CREATE_MESSAGE = "/api/v1/conversations/{conversation_id:int}/messages"
GET_MESSAGES = "/api/v1/conversations/{conversation_id:int}/messages"
UPDATE_MESSAGE = "/api/v1/conversations/{conversation_id:int}/messages/{message_id:int}"
DELETE_MESSAGE = "/api/v1/conversations/{conversation_id:int}/messages/{message_id:int}"

ADD_MEMBER_TO_CONVERSATION = (
    "/api/v1/conversations/{conversation_id:int}/participants/{user_id:int}"
)
REMOVE_SELF_FROM_CONVERSATION = (
    "/api/v1/conversations/{conversation_id:int}/participants/me"
)
REMOVE_MEMBER_FROM_CONVERSATION = (
    "/api/v1/conversations/{conversation_id:int}/participants/{user_id:int}"
)

GET_ATTACHMENT_CONTENT = "/api/v1/conversations/{conversation_id:int}/messages/{message_id:int}/attachments/{attachment_id:int}"
