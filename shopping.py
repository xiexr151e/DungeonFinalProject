import sys
import time
from item import catalog, itemwrapper

def shop(hero, npc, level):       
    i = 0
    while i != '3':
        sys.stdout.write("\x1b[2J\x1b[H")
        print("{}: {}\n".format(npc.i.name,npc.i.welcome)) 
        print(" 1. Buy\n 2. Sell\n 3. Leave")
        print(shopquotes[npc.i.level][0])
        i = input()
        if i == '1':
            buy(hero,npc,level)
        elif i == '2':
            sell(hero,npc)
        elif i == '3':
            print(shopquotes[npc.i.level][len(shopquotes[npc.i.level]) - 1])
            time.sleep(1)

def buy(hero,npc,level):
    canbuy = []
    if len(hero.bag) >= 5:
        print("Bag is too full.")
        time.sleep(1)
        return   
    for i in range(len(catalog[npc.i.level])):
        if catalog[npc.i.level][i].shop:
            canbuy.append(catalog[npc.i.level][i])
    print("Pick an item from 0-{}.".format(len(canbuy) - 1))
    for j in range(len(canbuy)):
        print('{} {} Cost: {}G'.format(j, canbuy[j].name, canbuy[j].cost))
    reasonable = False
    while reasonable == False:
        try:
            select = int(input())
            if select >= 0 and select < len(canbuy):
                reasonable = True
        except ValueError:
            print("What?")
            time.sleep(1)
            continue
    cost = str(canbuy[select].cost)
    print('{} [Y/N]'.format(buildquote(shopquotes[npc.i.level][1], [canbuy[select].name, cost])))
    choose = 'Bleh'
    while choose != 'y' and choose != 'n':
        choose = input()
        choose.lower()
        if choose != 'y' and choose != 'n':
            print("Well?")
            time.sleep(1)
    if choose == 'n':
        return
    elif choose == 'y':
        if canbuy[select].cost > hero.money:
            print(shopquotes[npc.i.level][6])
        else:
            print(shopquotes[npc.i.level][4])
            hero.money -= canbuy[select].cost
            hero.bag.append(itemwrapper(canbuy[select], level, hero.position.x, hero.position.y))
    time.sleep(1)
    return

def sell(hero,npc):
    print(shopquotes[npc.i.level][2])

def buildquote(quote, words):
    current = 0
    final = ""
    for i in range(len(quote)):
        if quote[i] == '*':
            final += words[current]
            current += 1
        else:
            final += quote[i]
    return final
shopquotes = [
["なにを差し上げる?","*の値段は...*Gぐらいだね。買う？","なにを売る？","これ、*Gを上げられる。","じゃあ、どうぞ！","残念。Gが足りないよ。","じゃあ、またどうぞ！"],
[],
[]]
