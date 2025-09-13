from .base_model import BaseModel
from ..db_scheme import Chat
from sqlalchemy import text as sql_text
from ..enums import TablesEnum

class ChatModel(BaseModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.table_name = TablesEnum.CHATS.value
        
    
    async def create_chat(self,chat_data:Chat):
        async with self.db_clint() as session:
            async with session.begin():
                session.add(chat_data)
            await session.commit()
            await session.refresh(chat_data)
        return chat_data
    

    async def get_all_chats(self)->list[Chat]:
        async with self.db_Clint() as session:
            result = await session.execute(sql_text(f"SELECT * FROM {self.table_name}"))
            chats = result.fetchall()

        return [Chat(**row) for row in chats]
    
    async def get_chat_by_id(self,chat_id:int)->Chat|None:
        async with self.db_clint() as session:
            result = await session.execute(
                sql_text(f"SELECT * FROM {self.table_name} WHERE id = :chat_id")
                .bindparams(chat_id=chat_id)
            )
            row = result.fetchone()
            if row:
                return Chat(**row)
            return None