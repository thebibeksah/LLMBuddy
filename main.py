import os
import json
import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
import time
import re
from datetime import datetime

dt = datetime.now()
app_id = ""

OLLAMA_MODEL = "deepseek-r1:8b"
OLLAMA_URL = "http://localhost:11434/api/generate"

EMBED_MODEL_NAME = "./bge_model_local"

os.environ['TRANSFORMERS_OFFLINE'] = "1"
os.environ['HF_DATASETS_OFFLINE'] = "1"

MEMORY_DIR = "./memory_store"
FAISS_PATH = f"{MEMORY_DIR}/memory.index"
META_PATH = f"{MEMORY_DIR}/memory.json"

EMBED_DIM = 768
TOP_K = 24
SIM_THRESHOLD = 0.45

SELF_QUERIES = ["what do you know about me", "who am i", "tell me about me"]
MEMORY_KEYWORDS = ["remember this", "note it", "keep it in mind"]
SEARCH_KEYWORDS = ["search online", "search this", "search this online"]
TERMINATION_KEYWORDS = ["quit the program", "/bye"]

os.makedirs(MEMORY_DIR, exist_ok=True)
conversation_history = []

try:
    embed_model = SentenceTransformer(EMBED_MODEL_NAME, local_files_only=True)
    print("Model loaded successfully in offline mode.")
except Exception as e:
    print(f"Error: Ensure the model is downloaded to {EMBED_MODEL_NAME}. Details: {e}")

if os.path.exists(FAISS_PATH):
    index = faiss.read_index(FAISS_PATH)
else:
    index = faiss.IndexFlatIP(EMBED_DIM)

if os.path.exists(META_PATH):
    with open(META_PATH, "r") as f:
        memory_texts = json.load(f)
else:
    memory_texts = []

def load_core_memory():
    return """Core Memory:
    - Assistant name is LLMBuddy
    - Give a greeting and begin the conversation
    """

def search_online(query):
    url = "http://api.wolframalpha.com/v1/result"
    params = {
        "i": query,
        "appid": app_id
    }

    res = requests.get(url, params=params)
    if res.status_code == 200:
        return res.text
    else:
        return False

def get_current_datetime_formatted():
    dt = datetime.now()
    def day_suffix(day):
        if 4 <= day <= 20 or 24 <= day <= 30:
            return "th"
        else:
            return ["st", "nd", "rd"][day % 10 - 1]
    return f"{dt.day}{day_suffix(dt.day)} {dt.strftime('%b')}, {dt.year} and time is {dt.strftime('%I:%M %p')}"


def save_memory():
    faiss.write_index(index, FAISS_PATH)
    with open(META_PATH, "w") as f:
        json.dump(memory_texts, f, indent=2)

def add_memory(text, importance=1.0):
    vec = embed_model.encode([text], normalize_embeddings=True)
    index.add(np.array(vec).astype("float32"))
    memory_texts.append({"text": text, "importance": importance})
    save_memory()

def retrieve_memory(query):
    if index.ntotal == 0:
        return []
    
    q = query.lower()
    if any(s in q for s in SELF_QUERIES):
        return [m["text"] for m in memory_texts[-10:]]
    
    q_vec = embed_model.encode([query]).astype("float32")
    q_vec = q_vec / np.linalg.norm(q_vec, axis=1, keepdims=True)
    D, I = index.search(q_vec, TOP_K)

    results = []
    for score, idx in zip(D[0], I[0]):
        if score > SIM_THRESHOLD:
            results.append(memory_texts[idx]["text"])
    
    return results

def build_prompt(user_input):
    memories = retrieve_memory(user_input)
    memory_block = ""
    
    if memories:
        memory_block = "\n".join(f"- {m}" for m in memories)
        memory_block = f"Context from past conversation:\n{memory_block}\n\n"
    
    conv_block = ""
    for entry in conversation_history:
        role = entry["role"]
        content = entry["content"]
        conv_block += f"{role}: {content}\n"
    
    return f"{memory_block}{conv_block}User: {user_input}\nAssistant:"

def ollama_chat(prompt):
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        r = requests.post(OLLAMA_URL, json=payload)
        return r.json()["response"]
    except Exception as e:
        return f"Error connecting to Ollama: {e}"
    
def chat(user_input):
    prompt = build_prompt(user_input)
    response = ollama_chat(prompt)
    conversation_history.append({"role": "User", "content": user_input})
    conversation_history.append({"role": "Assistant", "content": response})
    return response

def clean_llm_response(text):
    clean_text = re.sub(r"[^a-zA-Z0-9\s.,]", "", text)
    clean_text = " ".join(clean_text.split())
    return clean_text


if __name__ == "__main__":
    
    chat_history = []
    print(chat(load_core_memory()))

    while True:
        formatted_date = get_current_datetime_formatted()
        system_instruction = f"System note: the current date and time is {formatted_date}. Respond accordingly if relevant."

        print("\n\n\n")
        user = input("> ")

        if user in TERMINATION_KEYWORDS:
            break

        found_search = None
        for keyword in SEARCH_KEYWORDS:
            if keyword in user.lower():
                found_search = keyword
                break
        
        instruction = user
        if found_search:
            index_num_search = user.lower().find(found_search)
            search_phrase = user[index_num_search + len(found_search):].strip()
            if search_phrase:
                result = search_online(search_phrase)
                print("\nSearching...\n")
                if result:
                    print(f"\nResults from Online: {result}\n")
                    instruction = f"{search_phrase}\nFrom System: Result from online: {result}"
                else:
                    print(f"\nCouldn't find the Answer online.\n")
                    instruction = f"{search_phrase}\nFrom System: Couldn't find a results online."

        start_time = time.perf_counter()
        response = chat(system_instruction + "\nUser: " + instruction)
        print("\n\n\n")

        found_keyword = None
        for keyword in MEMORY_KEYWORDS:
            if keyword in user.lower(): 
                found_keyword = keyword
                break

        if found_keyword:
            index_num = user.lower().find(found_keyword)
            memory_phrase = user[index_num + len(found_keyword):].strip()
            if memory_phrase:
                add_memory(memory_phrase)
                print(f"Memory updated: '{memory_phrase}'\n\n")
            else:
                print("No memory text found after the keyword.\n\n")
        
        print(response)
        end_time = time.perf_counter()

        print(f"\nResponse Generated in {end_time - start_time:.3f} seconds")
        
        systematic_layout_for_list = "User: " + str(user)
        chat_history.append(systematic_layout_for_list)

    formatted_string = "[" + ", ".join(f'"{item}' for item in chat_history) + "]"
    with open("chat_history.txt", "w", encoding="utf-8") as file:
        file.write(formatted_string)
