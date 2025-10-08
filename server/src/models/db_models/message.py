from .base_model import BaseModel
from ..db_scheme import message_scheme,chat_scheme
from sqlalchemy import text as sql_text
from ..enums import TablesEnum

class MessageModel(BaseModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.table_name = TablesEnum.MESSAGES.value
        
    
    async def add_message(self,message_data:message_scheme,chat_id:int):
        async with self.db_clint() as session:
            async with session.begin():
                await session.execute(
                sql_text(f"UPDATE {TablesEnum.CHATS.value} "
                         "SET updated_at = CURRENT_TIMESTAMP "
                         "WHERE id = :chat_id"),
                {"chat_id": chat_id}
            )
                session.add(message_data)
            await session.commit()
            await session.refresh(message_data)
        return message_data
    

    async def get_chat_history(self,chat_id)->list[message_scheme]:
        async with self.db_clint() as session:
            result = await session.execute(sql_text(f"SELECT * FROM {self.table_name} WHERE chat_id=:chat_id ORDER BY created_at ASC").bindparams(chat_id=chat_id))
            chats = result.mappings().fetchall()

        return [message_scheme(**row) for row in chats]
    

    async def delete_messages_by_chat_id(self,chat_id:int):
        async with self.db_clint() as session:
            async with session.begin():
                await session.execute(
                    sql_text(f"DELETE FROM {self.table_name} WHERE chat_id = :chat_id"),
                    {"chat_id": chat_id}
                )
            await session.commit()
        return True