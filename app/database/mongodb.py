from motor.motor_asyncio import AsyncIOMotorClient

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        await self.db.command("ping")

    async def close(self):
        if self.client:
            self.client.close()

    @property
    def calls(self):
        return self.db["calls"]

    @property
    def callers(self):
        return self.db["callers"]

db = Database()