print("questeng.py (c) trolol inc. 2026")

class GameOver(Exception):
    pass

locale={
    "quest_launch": "Запуск квеста QUEST!",
    "choice": "Ваш выбор: ",
    "got_item": "Вы получили 'ITEM' xAMOUNT",
    "lost_item": "Вы потеряли 'ITEM' xAMOUNT",
    "invalid_choice": "Введите число от MIN до MAX!",
    "open_inventory": "Просмотреть инвентарь",
    "inventory_msg": "Ваш инвентарь: ",
    "item_msg": "AMOUNTx 'ITEM' - 'DESC'"
    }

def templ_print(template,data=[]):
    s=locale[template]
    if template=="quest_launch":
        s=s.replace("QUEST",data)
    elif template=="got_item" or template=="lost_item":
        s=s.replace("ITEM",data[0])
        s=s.replace("AMOUNT",str(data[1]))
    elif template=="invalid_choice":
        s=s.replace("MIN",str(data[0]))
        s=s.replace("MAX",str(data[1]))
    elif template=="item_msg":
        s=s.replace("AMOUNT",str(data[0]))
        s=s.replace("ITEM",data[1])
        s=s.replace("DESC",data[2])
    print(s)

def form_templ_str(s,params):
    pattern=r'\$\(([^)]+)\)'
    
    def replace_match(match):
        key=match.group(1).strip()
        return str(params[key])

    result=__import__('re').sub(pattern, replace_match, s)
    
    return result

def form_templ_location(template,params):
    location={}
    location["name"]=form_templ_str(template["name"],params)
    location["text"]=form_templ_str(template["text"],params)
    location["choices"]=[]
    for choice_cat in template["choices"]:
        if choice_cat["type"]=='single':
            choice={}
            choice["text"]=form_templ_str(choice_cat["text"],params)
            choice["result"]={}
            for k,v in choice_cat["result"].items():
                choice["result"][k]=form_templ_str(v,params)
            if choice_cat.get("condition"):
                choice["condition"]={}
                for k,v in choice_cat["condition"].items():
                    choice["condition"][k]=form_templ_str(v,params)
            location["choices"].append(choice)
        elif choice_cat["type"]=='multi':
            cat=choice_cat["category"]
            cat_params=params[cat].copy()
            for param_set in cat_params:
                for param in param_set:
                    params[cat+'.'+param]=param_set[param]
                choice={}
                choice["text"]=form_templ_str(choice_cat["text"],params)
                choice["result"]={}
                for k,v in choice_cat["result"].items():
                    choice["result"][k]=form_templ_str(v,params)
                if choice_cat.get("condition"):
                    choice["condition"]={}
                    for k,v in choice_cat["condition"].items():
                        choice["condition"][k]=form_templ_str(v,params)
                location["choices"].append(choice)
    return location

def watch_inventory():
    templ_print("inventory_msg")
    for item,amount in inventory.items():
        if amount==0:
            continue
        desc=items.get(item,{}).get("desc",'')
        templ_print("item_msg",[amount,item,desc])
    print()

with open("quest2.json", encoding="utf-8") as o:
    quest=__import__('json').load(o)

quest_name=quest.get("name","Quest")
locale.update(quest.get("locale",{}))

cur_location=quest.get("start_location","start")
locations=quest["locations"]
items=quest.get("items",{})

templates=quest["templates"]
templated=quest["templated_locations"]

for name,loc in templated.items():
    locations[name]=form_templ_location(templates[loc["template"]],loc["params"])

inventory=__import__('collections').defaultdict(int)
choiced=set()
flags=set()

builtin_keys={
    'I': ('open_inventory', watch_inventory)
    }

def check_condition(condition):
    cond_type=condition.get("type",'')
    if cond_type is None or cond_type=='':
        return True
    if cond_type=="not-choiced":
        return condition["choice"] not in choiced
    if cond_type=="choiced":
        return condition["choice"] in choiced
    if cond_type=="has-item":
        return inventory[condition["item"]]>=int(condition.get("amount",1))
    if cond_type=="has-item-from":
        return any(inventory[item["item"]]>=int(item.get("amount",1)) for item in condition["items"])
    if cond_type=="no-item":
        return inventory[condition["item"]]==0
    if cond_type=="flag-set":
        return condition["flag"] in flags
    if cond_type=="flag-cleared":
        return condition["flag"] not in flags
    
    return True

def execute_result(result):
    global cur_location
    res_type=result.get("type",'none')
    if result["text"]:
        print()
        print(result["text"])
        print()
    if res_type=='goto':
        return result["goto"]
    elif res_type=='get-item':
        inventory[result["item"]]+=int(result.get("amount",1))
        if inventory[result["item"]]<0:
            inventory[result["item"]]=0
        templ_print("got_item",[result['item'],result.get('amount',1)])
    elif res_type=='get-items':
        for i in range(min(len(result["items"]),len(result["amounts"]))):
            item=result["items"][i]
            amount=result["amounts"][i]
            inventory[item]+=amount
            if inventory[item]<0:
                inventory[item]=0
            templ_print("got_item",[item,amount])
    elif res_type=='remove-item':
        inventory[result["item"]]-=int(result.get("amount",1))
        if inventory[result["item"]]<0:
            inventory[result["item"]]=0
        templ_print("lost_item",[result['item'],result.get('amount',1)])
    elif res_type=='clear-inventory':
        for item,amount in inventory.items():
            if amount==0:
                continue
            inventory[item]=0
            templ_print("lost_item",[item,amount])
    elif res_type=='get-remove-item':
        inventory[result["get_item"]]+=int(result.get("get_amount",1))
        if inventory[result["get_item"]]<0:
            inventory[result["get_item"]]=0
        templ_print("got_item",[result['get_item'],result.get('get_amount',1)])
        inventory[result["remove_item"]]-=int(result.get("remove_amount",1))
        if inventory[result["remove_item"]]<0:
            inventory[result["remove_item"]]=0
        templ_print("lost_item",[result['remove_item'],result.get('remove_amount',1)])
    elif res_type=='set-flag':
        flags.add(result["flag"])
    elif res_type=='clear-flag':
        try:
            flags.remove(result["flag"])
        except KeyError:
            pass
    elif res_type=='sublocation':
        new=run_location({
            "text": '',
            "choices": result["choices"],
            },sublocation=True)
        if new:
            return new
    elif res_type=='end':
        raise GameOver
    elif res_type=='none':
        pass

def run_location(location,sublocation=False):
    if location.get("text") is not None:
        text=location["text"]
        if text:
            print(text)
    else:
        texts=location["texts"]
        conds=location["text_conditions"]
        for cond,text in zip(conds,texts):
            if check_condition(cond):
                print(text)
                break
    while True:
        i=1
        available=[]
        for j,choice in enumerate(location["choices"]):
            conds=choice.get("conditions")
            if conds is None:
                conds=[choice.get("condition",{"type":''})]
            ok=True
            for cond in conds:
                if not check_condition(cond):
                    ok=False
            if ok:
                print(str(i)+'. '+choice['text'])
                i+=1
                available.append(j)
        for k,v in builtin_keys.items():
            print(k+'. ',end='')
            templ_print(v[0])

        while True:
            inp=input(locale["choice"])
            if inp.upper() in builtin_keys:
                builtin_keys[inp.upper()][1]()
                break
            if not inp.isnumeric():
                templ_print("invalid_choice",[1,len(available)])
                continue
            num=int(inp)
            if num<1 or len(available)<num:
                templ_print("invalid_choice",[1,len(available)])
                continue
            choice=location["choices"][available[num-1]]
            if not sublocation:
                choiced.add(location['name']+'.'+str(available[num-1]+1))
            if (inp:=choice.get("input")) is not None:
                inp=choice["input"]
                user_inp=input(inp["text"])
                if user_inp==inp["correct"]:
                    print(inp["text_correct"])
                else:
                    print(inp["text_fail"])
                    break
            if (results:=choice.get("results")) is not None:
                chanced=[asd for asd in results if asd.get("chance") is not None]
                unchanced=[asd for asd in results if asd.get("chance") is None]
                res=[]
                if len(chanced)>0:
                    res+=__import__('random').choices(chanced,weights=[chanc["chance"] for chanc in chanced])
                res+=unchanced
            else:
                res=[choice["result"]]

            for result in res:
                if new_location:=execute_result(result):
                    return new_location

            if sublocation:
                return
                
            break

def main():
    global cur_location
    templ_print("quest_launch",quest_name)
    while True:
        try:
            cur_location=run_location(locations[cur_location])
        except GameOver:
            break
    input("Нажмите enter для выхода...")

main()
