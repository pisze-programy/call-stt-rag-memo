from pymongo import AsyncMongoClient

class Database:
    client: AsyncMongoClient = None
    db = None

    async def connect(self, uri: str, db_name: str):
        self.client = AsyncMongoClient(uri)
        self.db = self.client[db_name]
        await self.client.admin.command('ping')

    async def close(self):
        await self.client.close()

db = Database()