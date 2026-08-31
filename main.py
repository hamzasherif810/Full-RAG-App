from fastapi import FastAPI
app = FastAPI()

@app.get("/welcome")
def greeting():
    return {
        "message": "hello guyssssssss! I am mozaaaaaaaaaa"
    }

