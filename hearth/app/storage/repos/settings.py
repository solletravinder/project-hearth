from app.storage.database import get_db
from app.storage.repos._shared import _now


async def get_settings() -> dict[str, str]:
    conn = await get_db()
    try:
        cursor = await conn.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}
    finally:
        await conn.close()


async def update_setting(key: str, value: str) -> dict[str, str]:
    conn = await get_db()
    try:
        await conn.execute(
            "INSERT INTO settings (key, value, updated_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE "
            "SET value = excluded.value, updated_at = excluded.updated_at",
            (key, value, _now()),
        )
        await conn.commit()
        return {"key": key, "value": value}
    finally:
        await conn.close()
