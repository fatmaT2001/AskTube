from .base_model import BaseModel
from ..db_scheme import message_scheme
from sqlalchemy import text as sql_text
from ..enums import TablesEnum

class MessageModel(BaseModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.table_name = TablesEnum.MESSAGES.value
        
    
    async def add_message(self,message_data:message_scheme):
        async with self.db_clint() as session:
            async with session.begin():
                session.add(message_data)
            await session.commit()
            await session.refresh(message_data)
        return message_data
    

    async def get_chat_history(self,chat_id)->list[message_scheme]:
        async with self.db_Clint() as session:
            result = await session.execute(sql_text(f"SELECT * FROM {self.table_name} where chat_id=:chat_id").bindparams(chat_id=chat_id))
            chats = result.fetchall()

        return [message_scheme(**row) for row in chats]
    