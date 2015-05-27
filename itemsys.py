import item
 
import random
 
###Item System by Mitsunari-san###
 
#rarity chart
rarechart = ["E","D","C","B","A","S"]
 
def generate_item(): #limit 10 random items per floor unless special events occur.
        getlist = 0
        rID = random.randrange(150) # 65 common, 30 uncommon, 25 rare, 15 super rare, 10 ultra rare, 5 mythical rare
        if 0 <= rID and rID <= 64:
                getlist = 0     
        if 65 <= rID and rID <= 94:
                getlist = 1
        elif 95 <= rID and rID <= 119:
                getlist = 2
        elif 120 <= rID and rID <= 134:
                getlist = 3
        elif 135 <= rID and rID <= 144:
                getlist = 4
        elif rID >= 145:
                getlist = 5
        ID = random.randrange(len(item.catalog[getlist]))
        return item.catalog[getlist][ID]


#aka godmod, but we'll use this to make a Vulnerary.
def make_item(nameofitem):
        for i in range(len(item.catalog)):
            for j in range(len(item.catalog[i])):
                if item.catalog[i][j].name == nameofitem:
                    return item.catalog[i][j]
        print("Warning! No such item exists.")
        return
