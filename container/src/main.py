import typing
import pathlib

import uvicorn

from fastapi import FastAPI, Depends

from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pydantic import BaseModel

Base = declarative_base()

# This is our SQLAlchemy model used with the database
class Thing(Base):
    __tablename__ = "thing"
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)

pathlib.Path("/opt/data").mkdir(exist_ok=True)
engine = create_async_engine("sqlite+aiosqlite:////opt/data/db.sqlite3")
async_session_maker = async_sessionmaker(engine)

async def create_db_and_tables():
    async with engine.begin() as conn:
        # We drop all tables on startup just for demonstration purposes.
        # Don't do this in production!
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> typing.AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


app = FastAPI()

# This is our Pydantic model used with the API
class ThingModel(BaseModel):
    id: typing.Optional[int]
    text: str

# We use the "startup" event to create our database and tables
@app.on_event("startup")
async def on_startup(session: AsyncSession = Depends(get_async_session)):
    await create_db_and_tables()

@app.get("/things")
async def get_things(session: AsyncSession = Depends(get_async_session)) -> typing.List[ThingModel]:
    things = await session.execute(select(Thing))
    return [ThingModel(id=thing.id, text=thing.text) for thing in things.scalars()]

@app.get("/things/{id}")
async def get_thing(id: str, session: AsyncSession = Depends(get_async_session)):
    thing = await session.get(Thing, id)
    if thing:
        return ThingModel(id=thing.id, text=thing.text)

@app.post("/things")
async def post_thing(thing: ThingModel, session: AsyncSession = Depends(get_async_session)):
    session.add(Thing(text=thing.text))
    await session.commit()

@app.delete("/things/{id}")
async def delete_thing(id: str, session: AsyncSession = Depends(get_async_session)):
    thing = await session.get(Thing, id)
    await session.delete(thing)
    await session.commit()

@app.put("/things/{id}")
async def put_thing(id: str, new_thing: ThingModel, session: AsyncSession = Depends(get_async_session)):
    thing = await session.get(Thing, id)
    thing.text = new_thing.text
    await session.commit()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
