import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from ._version import __version__
from .core import PrivacyFilter


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        pfilter = PrivacyFilter()
        pfilter.initialize(
            clean_accents=True,
            nlp_filter=True,
            wordlist_filter=False,
            regular_expressions=True,
        )
        app.state.pfilter = pfilter
    except Exception as error:
        app.state.startup_error = str(error)
    yield


privacyFilterApp = FastAPI(title="PrivacyFilter API", version=__version__, lifespan=lifespan)


class Parameter(BaseModel):
    text: str
    use_nlp: bool = True


@privacyFilterApp.get("/")
async def root():
    return {"message": "Welcome, please navigate to /filter", "version": __version__}


@privacyFilterApp.get("/health")
async def health(request: Request):
    if hasattr(request.app.state, "startup_error"):
        raise HTTPException(status_code=503, detail=request.app.state.startup_error)
    return {"status": "ok", "version": __version__}


@privacyFilterApp.post("/filter")
def filtertext(item: Parameter, request: Request):
    if hasattr(request.app.state, "startup_error"):
        raise HTTPException(status_code=503, detail=request.app.state.startup_error)

    starttime = time.time()
    filtered_text = request.app.state.pfilter.filter(item.text, nlp_filter=item.use_nlp)
    return {"text": filtered_text, "time": time.time() - starttime}


if __name__ == "__main__":
    uvicorn.run("privacyfilter.api:privacyFilterApp", host="0.0.0.0", port=8000, reload=True)
