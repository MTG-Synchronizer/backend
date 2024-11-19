from uuid import UUID
from neo4j import AsyncManagedTransaction

async def add_user(tx: AsyncManagedTransaction, uid: UUID):
    """ Adds a user to the database if they do not already exist """

    query = """
    MERGE (u:User {uid: $uid})
    ON CREATE SET u.created_at = datetime()
    RETURN u
    """
    response = await tx.run(query, uid=uid)
    return await response.data()