import json

with open("./memory_store/memory.json", "r", encoding="utf-8") as f:
    data = json.load(f)

result = [list(item.values())[0] for item in data]

with open("recovery.txt", "w", encoding="utf-8") as f:
    f.write(f"list = {result}")

print("Done")
