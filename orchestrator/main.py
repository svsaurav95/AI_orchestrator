# orchestrator/main.py
from fastapi import FastAPI, HTTPException
import docker
import requests
import json
import os
from groq import Groq
from pydantic import BaseModel

app = FastAPI()
docker_client = docker.from_env()

# Load secrets from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set")

groq_client = Groq(api_key=GROQ_API_KEY)

class UserRequest(BaseModel):
    request: str
    data: str

def get_task_sequence(user_request: str) -> list:
    prompt = f"""Determine which of these services to execute:
    Available services:
    1. data_cleaner - For dataset cleaning tasks
    2. sentiment_analyzer - For text sentiment analysis
    
    User Request: {user_request}
    
    Respond with JSON format: {{"tasks": ["service1", "service2"]}}"""
    
    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)["tasks"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

@app.post("/process")
async def handle_request(user_request: UserRequest):
    try:
        tasks = get_task_sequence(user_request.request)
        processed_data = user_request.data
        
        for task in tasks:
            container = docker_client.containers.run(
                image=f"{task}:latest",
                ports={'5000/tcp': None},
                detach=True
            )
            container.reload()
            port = container.attrs['NetworkSettings']['Ports']['5000/tcp'][0]['HostPort']
            
            try:
                response = requests.post(
                    f"http://localhost:{port}/process",
                    json={"data": processed_data},
                    timeout=30
                )
                response.raise_for_status()
                processed_data = response.json()["result"]
            finally:
                container.stop()
                container.remove()
        
        return {"result": processed_data}
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")
