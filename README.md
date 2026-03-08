
# LLMBuddy

LLMBuddy is a way to use ollama local models with some additional features like session chat history, long-term memory, online search (via wolframAlpha), time tracking, and many more using python.

For online search and query you must have a WolframAlpha App ID which you can get from their website for free.

After getting the App ID you can simply add your ID to the main.py file on app_id (which initially is an empty variable already in the code) variable.






## Installation

You must be using python 3.13.3 or above. I have used this specific version on development.

You should also have ollama models pre-installed in your device. I have used gpt-oss:20b and deepseek-r1:8b models on tesing and both of them worked pretty well. Smaller models can make mistakes on memory so I personally recommend the models I have used. You can use other powerful models as well.

## Run Locally

Clone the project

```bash
  git clone https://github.com/thebibeksah/LLMBuddy.git
```

Go to the project directory

```bash
  cd llmbuddy
```
Create a virtual environment

```bash
  python -m venv .venv
```

Install dependencies

```bash
  pip install -r requirements.txt
```
Inside of python terminal run this code for the first time to download the embedding model (You can also use other models of your wish)

```bash
from huggingface_hub import snapshot_download

# Download the specific model to a local folder
snapshot_download(
    repo_id="BAAI/bge-base-en-v1.5", 
    local_dir="./bge_model_local",
    local_dir_use_symlinks=False
)

```
Run the program

```bash
  python .\main.py
```


## Features

- Have a long-term memory
- Can do online searches
- Can have defined personalities
- LLM independent


## Additional Informations

There are some other python files called manual_memory_integration.py which already has some attributes. Upon running this file, those properties will be added to the llmbuddy's long term memory. You can manually add memory using this file.

On the other hand you can also add long-term memroy inside the main.py program by using some pre-defined queries example: note it, remember this, etc. All the queries are pre-defined in the code and you can add additional queries if you wish.

The memory_recovery.py is used to recover memory if the memory file gets corrupted for any reason. This file will return a python list with all the memories. Then you can simply run the manual_memory_integration.py with this list to recover the memory.