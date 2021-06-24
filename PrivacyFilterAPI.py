import uvicorn
from fastapi import FastAPI
from PrivacyFilter import PrivacyFilter
from pydantic import BaseModel

privacyFilterApp = FastAPI()

pfilter = PrivacyFilter()
pfilter.initialize()


class Item(BaseModel):
    text: str


@privacyFilterApp.get("/")
async def root():
    return {"message": "Hello World"}


@privacyFilterApp.post("/filter")
async def filtertext(item: Item):
    item_dict = item.dict()
    filtered_text = pfilter.filter(item.text)
    item_dict.update({"filtered": filtered_text})
    return item_dict

if __name__ == '__main__':
    uvicorn.run("PrivacyFilterAPI:privacyFilterApp",
                host="0.0.0.0",
                port=8000,
                reload=True,
                ssl_keyfile="./key.pem",
                ssl_certfile="./cert.pem"
                )