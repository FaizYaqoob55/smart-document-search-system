from fastapi import FastAPI

app = FastAPI(title="Smart Document Search System")




@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Document Search System!"}