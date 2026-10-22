import json
import datacls

def load_masters_to_json(obj: datacls.Master):
    
    obj_tp = tuple(m.to_dict() for m in obj_tp.masters)
    with open("output.json", "w", encoding="UTF-8") as file:
        json.dump(obj_tp, file, indent=4, ensure_ascii=False)

def load_master_out_json(json_obj: str):

    with open(json_obj, "r", encoding="UTF-8") as file:
        data = json.load(file)
    return data

# print(load_master_out_json("output.json"))
