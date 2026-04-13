import ollama
import time

def generate_message(prompt:str):
    start_time=time.time()
    response=ollama.chat(
        model='llama3',
        messages=[{"role": "user", "content": prompt}]
    )
    end_time=time.time()
    print("LLM Resaponse Time : ",end_time-start_time)
    return response['message']['content']