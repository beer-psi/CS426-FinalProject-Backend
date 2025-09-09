# Gateway

The Gateway API is the entrypoint for receiving real-time events (usually revolving chat).

It can be accessed by opening a WebSocket connection at `{BASE_URL}/api/v1/gateway` with the
correct authorization (using the `Authorization` header or cookies).

## Gateway events

Gateway events are payloads sent over a Gateway connection. Clients receive events after they
take place on the server.

All Gateway events are encapsulated in a Gateway event payload:

```json
{
    "t": "EVENT_NAME",
    "d": {}
}
```

The `t` field denotes the event type, and determines the data in the `d` field.

The data types can mostly be referenced from the REST API documentation [here](https://studymate.beerpsi.cc/schema).

### Conversation Create

Sent when a conversation is created, or when the current user is added to a conversation.
The data is a conversation object.
- When a conversation is created, includes an additional `newly_created` boolean field.
- When the user gets added to a conversation, includes a conversation participant object under
the `participant` key.

```json
{
    "t": "CONVERSATION_CREATE",
    "d": {
        "id": 0,
        "type": "direct",
        "name": "string",
        "description": "string",
        "created_at": "2019-08-24T14:15:22Z",
        "updated_at": "2019-08-24T14:15:22Z",
        "require_member_approval": false,
        "participants": [

        ]
    }
}
```

### Conversation Update

Sent when a conversation is updated (name or description changed). The data is the updated conversation object.

```json
{
    "t": "CONVERSATION_UPDATE",
    "d": {
        "id": 0,
        "type": "direct",
        "name": "string",
        "description": "string",
        "created_at": "2019-08-24T14:15:22Z",
        "updated_at": "2019-08-24T14:15:22Z",
        "require_member_approval": false,
        "participants": [

        ]
    }
}
```

### Conversation Delete

Sent when a conversation is deleted, or the current user was removed from the conversation. The data is the conversation ID.

```json
{
    "t": "CONVERSATION_DELETE",
    "d": {
        "id": 0
    }
}
```

### Conversation Participants Update

Sent when anyone is added or removed from a conversation. Added participants are full conversation participant objects,
while only the IDs of removed participants are sent.

```json
{
    "t": "CONVERSATION_PARTICIPANTS_UPDATE",
    "d": {
        "id": 0,
        "participant_count": 0,
        "added_participants": [],
        "removed_participant_ids": []
    }
}
```

### Message Create

Sent when a message is created. The data is the newly created message object.

```json
{
    "t": "MESSAGE_CREATE",
    "d": {
        "id": 0,
        "conversation_id": 0,
        "reply_to_id": 0,
        "user_id": 0,
        "content": "string",
        "created_at": "2019-08-24T14:15:22Z",
        "updated_at": "2019-08-24T14:15:22Z",
        "edited_at": "2019-08-24T14:15:22Z",
        "attachments": []
    }
}
```

### Message Delete

Sent when a message is deleted. The data is the deleted message ID.

```json
{
    "t": "MESSAGE_DELETE",
    "d": {
        "id": 0
    }
}
```
