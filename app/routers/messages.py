from fastapi import WebSocket, APIRouter, Depends
from fastapi import status
from typing import List, Optional
from fastapi.param_functions import Query
from starlette.websockets import WebSocketDisconnect
from ..resources import models, schemas, crud
from ..database import Database
from ..routers.auth import decode_token
from sqlalchemy.orm.session import Session

router = APIRouter()

class Connection:
    def __init__(self, profile_id: int, socket: WebSocket):
        self.profile_id = profile_id
        self.socket = socket

class WebsocketManager:
    def __init__(self):
        self.active_connections: List[Connection] = []

    async def connect(self, connection: Connection):
        await connection.socket.accept()
        self.active_connections.append(connection)

    def disconnect(self, connection: Connection):
        self.active_connections.remove(connection)

    async def send_message(self, db: Session, message: schemas.MessageIn):
        created_message = crud.create_message(db, message)

        sender_socket: WebSocket = list(filter(self.active_connections, lambda x: x.profile_id == created_message.sender_id))[0]
        receiver_socket: WebSocket = list(filter(self.active_connections, lambda x: x.profile_id == created_message.receiver_id))[0]

        message_json = {
            'type': 'new',
            'message':{
                'id': created_message.id,
                'from': created_message.sender_id,
                'to': created_message.receiver_id,
                'content': created_message.content,
                'datetime_sent': created_message.datetime_sent
            }
        }

        await sender_socket.send_json(message_json) 
        await receiver_socket.send_json(message_json) 
        

    async def delete_message(self, db: Session, message_id: int):
        message = crud.read_comment_by_id(db, message_id)

        sender_socket: WebSocket = list(filter(self.active_connections, lambda x: x.profile_id == message.sender_id))[0]
        receiver_socket: WebSocket = list(filter(self.active_connections, lambda x: x.profile_id == message.receiver_id))[0]

        message_json = {
            'type': 'delete',
            'id': message.id
        }

        await sender_socket.send_json(message_json) 
        await receiver_socket.send_json(message_json) 

        crud.delete_message(db, message_id)

manager = WebsocketManager()

async def WebSocketAuth(websocket: WebSocket, token: str = Query(...), db: Session = Depends(Database)):
    try:
        profile = decode_token(token, db)
    except:
        profile = None

    return profile


@router.websocket('/messages')
async def message_endpoint(websocket: WebSocket, db: Session = Depends(Database), profile: models.Profile = Depends(WebSocketAuth)):
    if profile is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    else:
        await manager.connect(Connection(profile.id, websocket))

        try:

            while True:
                data = await websocket.receive_json()
                
                if data['type'] == 'send':
                    manager.send_message(db, schemas.MessageIn(data=data['message']))
                elif data['type'] == 'delete':
                    manager.delete_message(db, data['message_id'])
        except WebSocketDisconnect:
            manager.disconnect(Connection(profile.id, websocket))