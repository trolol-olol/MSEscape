import time

def update_globals(globs):
    globals().update(globs)

def _sleep_print(text):
    strs=text.split('\n')
    for s in strs:
        print(s)
        time.sleep(2)

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
