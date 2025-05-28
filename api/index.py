import uvicorn

from main import app

handler = app

uvicorn.run(app)