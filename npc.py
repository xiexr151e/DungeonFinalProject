import collections
import shopping

npc = collections.namedtuple('npc', 'name job welcome floor level')

npcindex = []

class npcwrapper:
    def __init__(self, i, x, y):
        self.i = i
        self.level = i.floor
        self.x = x
        self.y = y

npcbase = [
npc("誠","Shopkeeper","あ、いらっしゃい！ここは初心者のショップだよ！",0,0),
npc("Jin","Shopkeeper","'Sup! Welcome to my shop! You can find decent goods here.",9,1),
npc("Aku","Shopkeeper","Oh, welcome. I have some slightly better goods.",22,2)
]

def loadnpc():
    for i in range(len(npcbase)):
        npcindex.append(npcbase[i].floor)

def checknpc(floor):
    for i in range(len(npcbase)):
        if floor == npcbase[i].floor:
            return npcbase[i]

def dothings(hero, npc, level):
    if npc.i.job == "Shopkeeper":
        shopping.shop(hero, npc, level)