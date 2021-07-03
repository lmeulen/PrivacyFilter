import uvicorn
from fastapi import FastAPI
from PrivacyFilter import PrivacyFilter
from pydantic import BaseModel

privacyFilterApp = FastAPI()

pfilter = PrivacyFilter()
pfilter.initialize(clean_accents=True, nlp_filter=False)


class Parameter(BaseModel):
    text: str
    use_nlp: bool


@privacyFilterApp.get("/")
async def root():
    return {"message": "Welcome, please navigate to /filter"}


@privacyFilterApp.post("/filter")
async def filtertext(item: Parameter):
    if item:
        item_dict = item.dict()
        filtered_text = pfilter.filter(item.text, nlp_filter=item.use_nlp)
        item_dict.update({"filtered": filtered_text})
        return item_dict
    else:
        return {"message": "No text specified"}

if __name__ == '__main__':
    uvicorn.run("PrivacyFilterAPI:privacyFilterApp",
                host="0.0.0.0",
                port=8000,
                reload=True)
