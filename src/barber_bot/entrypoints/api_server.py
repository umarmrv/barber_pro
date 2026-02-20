from __future__ import annotations

import uvicorn


if __name__ == "__main__":
    uvicorn.run("barber_bot.api.app:create_app", factory=True, host="0.0.0.0", port=8000)
