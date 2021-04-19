import json

grouped_file = "D:\Desktop\dissertation\dimev\lydgate\DIMEV-Edges.json"

with open(grouped_file, 'r') as f:
    data = json.load(f)

with open("dimev-fall-edges.csv", "w") as f:
    f.write("Source, Target\n")
    for w in data:
        texts = data[w]
        for i in range(len(texts)):
            for t in texts[i+1:]:
                f.write(f"{texts[i]}, {t}\n")
