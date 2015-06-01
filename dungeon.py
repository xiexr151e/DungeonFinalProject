#! /usr/bin/env python3
 
import itemsys
import help
from inventory import bag, printinv, update
import collections
import copy
import random
import sys
import termios
import tty
import time
import item
import math
from units import data, setclass, ispromote, getbase, getmax, paramcheck
from npc import npcbase, loadnpc, checknpc, npcindex, npcwrapper, dothings

################################################################
#                   TODO:
# Implement a skill system.
# Implement ranged attacks. (COMPLETE)
# Implement a convoy system with 5 extra spaces?
# Somehow edit the attack system to accomodate Astra, or drop Astra altogether. Or, make a separate Astra attack method.
# Add more NPCs. This includes a blacksmith and an alchemist. (BLACKSMITH COMPLETE)
# Make shops more frequent and change the shop boolean into an array of ints. (COMPLETE)
# Make a set direction key should be easy, but how should I do it? (COMPLETE)
# Put in the rest of the weapons... Axes and bows, I think. (COMPLETE)
# Put in locations of merchant items(aka more simple but mundane work).
################################################################

 
#control variables
current = 0
capacity = 5 #standard for weapons as well as skills
MOVEABLE = ['.', '+', '#', '>','<','?','0'] #For a "ghost", add the following to the array: '-','|',None
NPC_ICONS = ['!','п','*','г']
statread = ["HP","Strength","Magic","Skill","Speed","Luck","Defense","Resist"]
direction = None
herodamage = 0
 
# Dimensions of the dungeon
X_DIM = 80
Y_DIM = 20
 
# Min and Max number of rooms per floor
NUM_ROOMS = (3, 5)
 
# Min and Max height and width of a room
ROOM_HEIGHT = (5, 8)
ROOM_WIDTH = (5, 20)
 
# Minimum separation between rooms
MIN_SEP = 2

# 10% an enemy will spawn for every move.
MONSTER_PROB = 0.1
 
Room = collections.namedtuple('Room', 'x y width height')
Point = collections.namedtuple('Point', 'x y')
 
items = [] 
monsters = []
npcs = []
 
MONSTERS = [
#Bases are taken from Awakening while growths are taken from Shadow Dragon to balance out the poor bases
[
    ['Archer', 'a', [80, 20, 0, 30, 30, 0, 20, 10]],
    ['Fighter', 'f', [90, 50, 0, 30, 20, 0, 50, 5]],
    ['Mercenary', 'm', [80, 30, 0, 20, 20, 0, 30, 10]],
    ['Cavalier', 'c', [80,35,0,30,20,0,30,10]],
    ['Myrmidon', 't', [80,20,0,30,30,0,20,10]]
],
[
    
]
]
 
####################
 
class Monster:
    def __init__(self, pos, name, what, base, growths):
        self.pos = pos
        self.name = name
        self.what = what
        self.stats = base
        self.max = getmax(self.name)
        self.lvl = current + 1
        self.growth = growths
        self.equip = None
        self.old = '.' # monsters always spawn on a '.'
        self.setstats()
        self.bonuses()

    def setstats(self):
        self.maxHP = self.stats[0]
        self.HP = self.stats[0]
        self.strength = self.stats[1]
        self.magic = self.stats[2]
        self.skill = self.stats[3]
        self.speed = self.stats[4]
        self.luck = self.stats[5]
        self.defense = self.stats[6]
        self.resist = self.stats[7]

    def bonuses(self):
        difficulty = int((current + 1) / 4)
        for i in range(len(self.stats)):
            self.stats[i] += 2 * difficulty
        self.setstats() 
 
    def move(self, level, newpos):
        level[self.pos.x][self.pos.y] = self.old
        self.old = level[newpos.x][newpos.y]
        level[newpos.x][newpos.y] = 'm'
        self.pos = newpos
    
    def lvlchange(self): # 1 level higher or lower than base   
        r = random.randrange(3)
        if r == 1 and self.lvl > 1:
            self.lvl -= 1
        elif r == 2 and self.lvl < 20:
            self.lvl += 1

    def die(self, level):
        level[self.pos.x][self.pos.y] = self.old
            
    def grow(self, lvl): #These growth rates are automated.
        for c in range(lvl):
            for i in range(len(self.stats)):
                g = random.randrange(100)
                if g <= self.growth[i] and self.stats[i] < self.max[i]:
                    self.stats[i] += 1
            self.setstats()
    
    def howtoattack(self,target):
        if self.equip == None:
            return self.struggle(target)
        else:
            return self.attacking(self.equip, target, 0)

    def struggle(self,target):
        damage = 0
        critical = (random.randrange(100) <= self.skill / 2)
        accuracy = 100 + (self.skill * 3 + self.luck) / 2
        if accuracy < random.randrange(100):
            sys.stdout.write("Missed! ")
            return 0
        damage = self.strength - target.defense
        if damage <= 0:
                damage = 1
        if critical:
                damage *= 3
                sys.stdout.write("CRITICAL! ")
        target.HP -= damage
        return damage

    def attacking(self, weapon, target, damage):
        miss = False
        critical = (random.randrange(100) <= weapon.critical + self.skill / 2)
        accuracy = weapon.accuracy + (self.skill * 3 + self.luck) / 2
        ############ These are all skill checks
            

        ############
        if accuracy < random.randrange(100):
            sys.stdout.write("Missed! ")
            miss = True
        if miss == False:
            if weapon.obj.type == "W":
                damage += self.strength + weapon.attack - target.defense
                if damage <= 0:
                    damage = 1
                if critical:
                    sys.stdout.write("CRITICAL! " )
                    damage *= 3
                target.HP -= damage
                if weapon.obj.effect == "Drain": 
                    self.heal(int(damage * .5))                    
            elif weapon.obj.type == "M":
                damage += self.magic + weapon.attack - target.resist
                if damage <= 0:
                    damage = 1
                if critical:
                    sys.stdout.write("CRITICAL! " )
                    damage *= 3
                target.HP -= damage
                if weapon.obj.effect == "Drain":
                    self.heal(int(damage * .5))
        weapon.dur -= 1
        return damage

    def heal(self,amount):
        self.HP += amount
        if self.HP >= self.maxHP:
            self.HP = self.maxHP
        sys.stdout.write("Recovered {} HP. ".format(amount))
 
#########################################################################################################################################################################

                                                                 #*YOU ARE NOW ENTERING HERO TERRITORY*#

#########################################################################################################################################################################
 
class hero:
    def __init__(self, name, a, f):
        self.money = 1000
        self.type = setclass("Tactician")
        self.weapons = setclass("Tactician").weapons
        self.stats = [19,6,5,5,6,4,6,4]
        self.base = [40,40,35,35,35,55,30,20] #This is personal to the player. I will use this a lot for changing class.
        self.default = [0,0,0,0,0,0,0,0] #HP, Str, Mag, Skl, Spd, Lck, Def, Res
        self.modify = [0,0,0,0,0,0,0,0] #This will be static once assets and flaws are determined
        self.max = self.type.maximum
        self.name = name
        self.coins = 0
        self.exp = 0
        self.culmlvl = 0
        self.promoted = 0
        self.actuallvl = 1
        self.displvl = 1
        self.bag = bag
        self.equip = None
        self.skillset = []
        self.inactiveskills = []
 
    def expgain(self,exp):
        self.exp += exp
        sys.stdout.write("Gained {} EXP. ".format(exp))
        while self.exp >= 100:
            self.exp -= 100
            self.displvl += 1
            self.actuallvl = self.displvl + self.culmlvl + self.promoted
            sys.stdout.write("Level up! ")
            self.grow()

    def maxmod(self, promo):
        for i in range(len(self.max)):
            self.max[i] = promo.maximum[i] + self.modify[i]

    def statmod(self, promo):
        for i in range(len(self.stats)):
            word = 'increased'
            amount = promo.basestats[i] - self.type.basestats[i]
            if amount < 0:
                word = 'decreased'
            self.stats[i] += amount #Calculating promo bonuses...            
            if self.stats[i] > self.max[i]:
                amount -= self.stats[i] - self.max[i]
                self.stats[i] = self.max[i]
            print("Your {} has {} by {}.".format(statread[i], word, abs(amount)))
        self.setstats()

    def growmod(self, promo):
        for i in range(len(self.base)):
            chance = self.base[i] + promo.base[i]
            self.default[i] = chance
#           print("You now have a {}% chance to gain {} every time you level up.".format(chance, statread[i])) #Only uncomment if debug

    def grow(self):
        gain = False
        for i in range(len(self.default)):
            g = random.randrange(100)
            if g <= self.default[i] and self.stats[i] < self.max[i]:
                self.stats[i] += 1
                sys.stdout.write("Gained 1 {}.\n".format(statread[i]))
                gain = True
        if gain == False:
            sys.stdout.write("Sadly, no stats were gained this time.\n")
        self.setstats()

    def autogrow(self):        
        if self.culmlvl == 0:
            return
        sys.stdout.write("More promotion bonuses~")
        for i in range(len(self.default)): #Used for large promotion bonuses for those who already reclassed for who knows what.
            gains = 0
            for c in range(self.culmlvl): 
                g = random.randrange(100)
                if g <= self.default[i] and self.stats[i] < self.max[i]:
                    self.stats[i] += 1
                    gains += 1
            sys.stdout.write("Gained {} {}.\n".format(gains, statread[i]))
        time.sleep(1)
 
    def assetmod(self,a):
        if a == 0:
            self.base[a] += 15
            self.base[6] += 5
            self.base[7] += 5
            self.modify[1] += 1
            self.modify[2] += 1
            self.modify[5] += 2
            self.modify[6] += 2
            self.modify[7] += 2
        elif a == 1:
            self.base[a] += 10
            self.base[3] += 5
            self.base[6] += 5
            self.modify[1] += 4
            self.modify[3] += 2
            self.modify[6] += 2
        elif a == 2:
            self.base[a] += 10
            self.base[4] += 5
            self.base[7] += 5
            self.modify[2] += 4
            self.modify[4] += 2
            self.modify[7] += 2
        elif a == 3:
            self.base[a] += 10
            self.base[1] += 5
            self.base[6] += 5
            self.modify[1] += 2
            self.modify[3] += 4
            self.modify[6] += 2
        elif a == 4:
            self.base[a] += 10
            self.base[3] += 5
            self.base[5] += 5
            self.modify[3] += 2
            self.modify[4] += 4
            self.modify[5] += 2
        elif a == 5:
            self.base[a] += 10
            self.base[1] += 5
            self.base[2] += 5
            self.modify[1] += 2
            self.modify[2] += 2
            self.modify[5] += 4
        elif a == 6:
            self.base[a] += 10
            self.base[5] += 5
            self.base[7] += 5
            self.modify[5] += 2
            self.modify[6] += 4
            self.modify[7] += 2
        elif a == 7:
            self.base[a] += 10
            self.base[2] += 5
            self.base[4] += 5
            self.modify[2] += 2
            self.modify[4] += 2
            self.modify[7] += 4
 
    def flawmod(self,a):
        if a == 0:
            self.base[a] -= 15
            self.base[6] -= 5
            self.base[7] -= 5
            self.modify[1] -= 1
            self.modify[2] -= 1
            self.modify[5] -= 1
            self.modify[6] -= 1
            self.modify[7] -= 1
        elif a == 1:
            self.base[a] -= 10
            self.base[3] -= 5
            self.base[6] -= 5
            self.modify[1] -= 3
            self.modify[3] -= 1
            self.modify[6] -= 1
        elif a == 2:
            self.base[a] -= 10
            self.base[4] -= 5
            self.base[7] -= 5
            self.modify[2] -= 3
            self.modify[4] -= 1
            self.modify[7] -= 1
        elif a == 3:
            self.base[a] -= 10
            self.base[1] -= 5
            self.base[6] -= 5
            self.modify[1] -= 1
            self.modify[3] -= 3
            self.modify[6] -= 1
        elif a == 4:
            self.base[a] -= 10
            self.base[3] -= 5
            self.base[5] -= 5
            self.modify[3] -= 1
            self.modify[4] -= 3
            self.modify[5] -= 1
        elif a == 5:
            self.base[a] -= 10
            self.base[1] -= 5
            self.base[2] -= 5
            self.modify[1] -= 1
            self.modify[2] -= 1
            self.modify[5] -= 3
        elif a == 6:
            self.base[a] -= 10
            self.base[5] -= 5
            self.base[7] -= 5
            self.modify[5] -= 1
            self.modify[6] -= 3
            self.modify[7] -= 1
        elif a == 7:
            self.base[a] -= 10
            self.base[2] -= 5
            self.base[4] -= 5
            self.modify[2] -= 1
            self.modify[4] -= 1
            self.modify[7] -= 3
 
    def adjust(self,a,f):
        for i in range(len(self.default)):
            self.default[i] = self.base[i] + self.type.base[i]
        if a == 0:
            self.stats[a] += 5
        elif a == 5:
            self.stats[a] += 4
        else:
            self.stats[a] += 2
        if f == 0:
            self.stats[f] -= 3
        elif f == 5:
            self.stats[f] -= 2
        else:
            self.stats[f] -= 1
        self.setstats()

    def boost(self,index,amount):
        self.stats[index] += amount
        print('{} increased by {}.'.format(statread[index],amount))
        time.sleep(1)
        self.setstats()

    def setstats(self):
        self.maxHP = self.stats[0]
        self.HP = self.stats[0]
        self.strength = self.stats[1]
        self.magic = self.stats[2]
        self.skill = self.stats[3]
        self.speed = self.stats[4]
        self.luck = self.stats[5]
        self.defense = self.stats[6]
        self.resist = self.stats[7]
 
    def set_position(self, newpos):
        self.position = newpos

    def promote(self):
        sys.stdout.write("\x1b[2J\x1b[H")
        print("Please enter one of the listed classes.\n")
        for i in range(len(self.type.classes)):
            print("{} {}\n".format(i+1, self.type.classes[i]))
        c = checkinput(input(),self.type.classes)
        if c == None:
            print("You have incorrectly entered a class or chose not to enter.")
            print("You will be {} by default.".format(self.type.classes[0]))
            c = 0      
        target = self.type.classes[c]
        self.promoted = 20
        self.autogrow()
        self.editstats(target)

    def reclass(self):
        sys.stdout.write("\x1b[2J\x1b[H")
        able = []
        additionalclasses = self.displvl >= 10 and self.type.classes == None
        print("Please enter one of the listed classes.\n")
        for i in range(len(data)):
            for j in range(len(data[i])):
                able.append(data[i][j].name)
        for k in range(len(able)):
            print("{} {}".format(k+1, able[k]))
        c = checkinput(input(),able)
        if c == None:
            print("You have incorrectly entered a class or chose not to enter.")
            print("You will be {} by default.".format(able[0]))
            c = 0      
        target = able[c]
        if ispromote(target) == 0:
            self.promoted = 0
        calc = self.displvl - 1 + self.promoted
        calc = int(calc / 2)
        self.culmlvl += calc
        self.editstats(target)

    def editstats(self, tar):        
        print("You are now a {}.\n".format(tar))
        self.maxmod(setclass(tar))
        self.statmod(setclass(tar))
        self.growmod(setclass(tar))
        self.type = setclass(tar)        
        self.displvl = 1
        self.actuallvl = self.displvl + self.culmlvl + self.promoted
        time.sleep(2)
        return

    def howtoattack(self,target):
        if self.equip == None:
            return self.struggle(target)
        else:
            return self.attacking(self.equip, target, 0)

    def struggle(self,target):
        damage = 0
        critical = (random.randrange(100) <= self.skill / 2)
        accuracy = 100 + (self.skill * 3 + self.luck) / 2
        if accuracy < random.randrange(100):
            sys.stdout.write("Missed! ")
            return 0
        damage = self.strength - target.defense
        if damage <= 0:
                damage = 1
        if critical:
                damage *= 3
                sys.stdout.write("CRITICAL! ")
        target.HP -= damage
        return damage

    def attacking(self, weapon, target, damage):
        miss = False
        critical = (random.randrange(100) <= weapon.critical + self.skill / 2)
        accuracy = weapon.accuracy + (self.skill * 3 + self.luck) / 2
        ############ These are all skill checks
            

        ############
        if accuracy < random.randrange(100):
            sys.stdout.write("Missed! ")
            miss = True
        if miss == False:
            if weapon.obj.type == "W":
                damage += self.strength + weapon.attack - target.defense
                if damage <= 0:
                    damage = 1
                if critical:
                    sys.stdout.write("CRITICAL! " )
                    damage *= 3
                target.HP -= damage
                if weapon.obj.effect == "Drain": 
                    self.heal(int(damage * .5))                    
            elif weapon.obj.type == "M":
                damage += self.magic + weapon.attack - target.resist
                if damage <= 0:
                    damage = 1
                if critical:
                    sys.stdout.write("CRITICAL! " )
                    damage *= 3
                target.HP -= damage
                if weapon.obj.effect == "Drain":
                    self.heal(int(damage * .5))
        weapon.dur -= 1
        return damage

    def heal(self,amount):
        self.HP += amount
        if self.HP >= self.maxHP:
            self.HP = self.maxHP
        sys.stdout.write("Recovered {} HP. ".format(amount))

    def calcexp(self,target,damage,isdead):
        difference = target.lvl - self.actuallvl
        basedamageexp = 0
        basekillexp = 0 
        if damage <= 1:
            return 1
        if difference >= 0:
            basedamageexp = int((31 + difference) / 3)
            basekillexp = 20 + (difference * 3)
        elif difference == -1:
            basedamageexp = 10
            basekillexp = 20
        elif difference <= -2:
            basedamageexp = max(int((33+difference)/3), 1)
            basekillexp = max(int(26 + (difference * 3)),7)
        if isdead == False:
            return basedamageexp
        elif isdead:
            return basedamageexp + basekillexp

#############################################################################################################################################

                                                         #*YOU ARE NOW ENTERING THE OVERWORLD*#

#############################################################################################################################################
def checkinput(put, array):
    if put == None:
        return None
    for i in range(len(array)):
        if put.lower() == array[i].lower():
            return i
    return None

def enemypos(dir):
    if dir == "N":
        p = Point(char.position.x, char.position.y-2)
    elif dir == "E":
        p = Point(char.position.x+2, char.position.y)
    elif dir == "W":
        p = Point(char.position.x-2, char.position.y)
    elif dir == "S":
        p = Point(char.position.x, char.position.y+2)
    else:
        return None
    return lookformonsters(p) 

def lookformonsters(point):
    for i in range(len(monsters)):
        if point.x == monsters[i].pos.x and point.y == monsters[i].pos.y:
            return monsters[i]

def random_door(level, room):
    '''
    Picks a random side for a door in and out of a room.
    '''
    deltax = deltay = 0
 
    # Pick random side on room
    side = random.randint(0, 3)
    if side == 0 or side == 2:
        deltay = random.randint(1, room.height-1)
    elif side == 1 or side == 3:
        deltax = random.randint(1, room.width-1)
 
    if side == 1:
        deltay = room.height
    elif side == 2:
        deltax = room.width
 
    return Point(room.x + deltax, room.y + deltay)
 
def dxdy(p):
    '''
    Yield the locations around the position to the left, right, above, and
    below.
    '''
    for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        yield Point(p.x+dx, p.y+dy)
 
def fill_room(level, room):
    '''
    Fill in a new room in the level, drawing borders around the room and
    periods inside the room. Returns a copy of the level with the new room
    added if the room did not collide with an existing room. Returns None if
    there was a collision.
    '''
    new_level = copy.deepcopy(level)
 
    # Populate new_level with room
    for j in range(room.height+1):
        for i in range(room.width+1):
            # Check if there's already a room here
            if level[room.x+i][room.y+j] != None:
                return None
 
            if j == 0 or j == room.height:
                new_level[room.x+i][room.y+j] = '-'
            elif i == 0 or i == room.width:
                new_level[room.x+i][room.y+j] = '|'
            else:
                new_level[room.x+i][room.y+j] = '.'
 
    # Ensure MIN_SEP space exists to left and right
    for j in range(room.height+1):
        if level[room.x-MIN_SEP][room.y+j] != None:
            return None
        if level[room.x+room.width+MIN_SEP][room.y+j] != None:
            return None
 
    # Ensure MIN_SEP space exists above and below
    for i in range(room.width+1):
        if level[room.x+i][room.y-MIN_SEP] != None:
            return None
        if level[room.x+i][room.y+room.height+MIN_SEP] != None:
            return None
 
    return new_level
 
 
def dist(p0, p1):
    '''
    Compute the euclidean distance between two points
    '''
    return ((p0.x - p1.x)**2 + (p0.y - p1.y)**2)**0.5
 
 
def create_path(level, p0, p1):
    '''
    Connect two points on the map with a path.
    '''
    # Compute all possible directions from here
    points = []
    for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        p = Point(p0.x+dx, p0.y+dy)
        if p == p1:
            return True
 
        if p.x >= X_DIM or p.x < 0:
            continue
        if p.y >= Y_DIM or p.y < 0:
            continue
        if level[p.x][p.y] not in [None, '#']:
            continue
 
        points.append(p)
 
    # Sort points according to distance from p1
    points.sort(key=lambda i: dist(i, p1))
 
    for p in points:
        old, level[p.x][p.y] = level[p.x][p.y], '$'
        if create_path(level, p, p1):
            level[p.x][p.y] = '#'
            return True
        level[p.x][p.y] = old
 
    return False

def surroundings(level, point): #Let's not block corridors. Seriously.
    return [level[point.x-1][point.y], level[point.x+1][point.y], level[point.x][point.y-1], level[point.x][point.y+1]]

def makepoints(level, point):
    return [Point(point.x-1,point.y), Point(point.x+1,point.y), Point(point.x,point.y-1), Point(point.x,point.y+1)]
 
def generate(level, item):
    points = []
    for j in range(1, len(level)):
        for i in range(1, len(level[0])):
            if level[j][i] == "." and '+' not in surroundings(level, Point(j, i)):
                points.append(Point(j, i))
    if len(points) == 0:
        return False
    p = random.choice(points)
    level[p.x][p.y] = item
    return p

def place(level, point, item): #Use this to place an object next to a an object dependent on point.
    p = random.randrange(4)
    points = makepoints(level, point)
    while '.' not in level[points[p].x][points[p].y] and '+' not in surroundings(level, points[p]):
        p = random.randrange(4)
    final = points[p]
    level[final.x][final.y] = item
    return final
 
def add_to_floor(level, room, item):
    '''
    Add staircase to random location within the room
    '''
    points = []
 
    for j in range(1, room.height):
        for i in range(1, room.width):
            if level[room.x+i][room.y+j] == ".":
                points.append(Point(room.x+i, room.y+j))
    if len(points) == 0:
        return False
    p = random.choice(points)
    level[p.x][p.y] = item
    return p
 
def make_item(level, p):
    i = item.itemwrapper(itemsys.generate_item(), level, p.x, p.y)
    items.append(i)
 
def add_item(level, room, item):
    level[pos.x][pos.y] = item
    return True
 
def make_level():
    '''
    Create a X_DIM by Y_DIM 2-D list filled with a random assortment of rooms.
    '''
    level = []
    for i in range(X_DIM):
        level.append([None] * Y_DIM)
 
    monsters = []
    rooms = []
 
    # Randomly N generate room in level
    for i in range(random.randint(*NUM_ROOMS)):
        # Keep looking, there should be *somewhere* to put this room...
        while True:
            # Generate random room
            x = random.randint(MIN_SEP, X_DIM)
            y = random.randint(MIN_SEP, Y_DIM)
            height = random.randint(*ROOM_HEIGHT)
            width = random.randint(*ROOM_WIDTH)
 
            # Check map boundary
            if x + width + MIN_SEP >= X_DIM:
                continue
            if y + height + MIN_SEP >= Y_DIM:
                continue
 
            room = Room(x, y, width, height)
            new_level = fill_room(level, room)
 
            if not new_level:
                continue
 
            level = new_level
            rooms.append(room)
            for i in range(1):
                if random.randrange(100) < 30:
                    add_to_floor(level, room, '0')
                post = add_to_floor(level, room, '?')
                make_item(level, post)
            break
 
    # Connect the rooms with random paths
    for i in range(len(rooms)-1):
        # Pick two random doors
        door0 = random_door(level, rooms[i])
        door1 = random_door(level, rooms[i+1])
 
        level[door0.x][door0.y] = '+'
        level[door1.x][door1.y] = '+'
 
        # Actually connect them
        if not create_path(level, door0, door1):
            # TODO: Could happen... what should we do?
            pass
 
    # Pick random room for stairs leading up and down
    up, down = random.sample(rooms, 2)
    add_to_floor(level, up, '<')
    add_to_floor(level, down, '>')

    #Insert NPC here
    npcpoint = None
    npclist = checknpc(current)
    for i in range(len(npclist)):
        if npclist[i].job == "Shopkeeper":
#           print("Making shop...")
            npcpoint = generate(level,'п')
            npcs.append(npcwrapper(npclist[i], npcpoint.x, npcpoint.y))
        elif npclist[i].job == "Healer":
            if npcpoint != None:
#               print("This will be next to shop.")
                npcpoint = place(level,npcpoint,'*')
            else:
#               print("There is no shop on this floor.")
                npcpoint = generate(level,'*')
            npcs.append(npcwrapper(npclist[i], npcpoint.x, npcpoint.y))
        elif npclist[i].job == "Blacksmith":
            if npcpoint != None:
#                print("This will be next to shop.")
                npcpoint = place(level,npcpoint,'г')
            else:
#               print("There is no shop on this floor.")
                npcpoint = generate(level,'г')
            npcs.append(npcwrapper(npclist[i], npcpoint.x, npcpoint.y))    
        else:
            npcpoint = generate(level,'!')
            npcs.append(npcwrapper(npclist[i], npcpoint.x, npcpoint.y))
    return level

    
    
 
 
def find_staircase(level, staircase):
    '''
    Scan the level to determine where a particular staircase is
    '''
    for j in range(Y_DIM):
        for i in range(X_DIM):
            if level[i][j] == staircase:
                return Point(i, j)
    return None
 
 
def print_level(level):
    '''
    Print the level using spaces when a tile isn't set
    '''
    for j in range(Y_DIM):
        for i in range(X_DIM):
            if level[i][j] == None:
                sys.stdout.write(' ')
            elif level[i][j] == 'm':
                for m in monsters:
                    if m.pos.x == i and m.pos.y == j:
                        sys.stdout.write(m.what)
                        break
            else:
                sys.stdout.write(level[i][j])
        sys.stdout.write('\n') 
 
 
def read_key():
    '''
    Read a single key from stdin
    '''
    try:
        fd = sys.stdin.fileno()
        tty_settings = termios.tcgetattr(fd)
        tty.setraw(fd)
 
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, tty_settings)
    return key

#################################################################################################################################################################

                                                                   #*YOU ARE NOW INITIALIZING THE GAME*#

#################################################################################################################################################################
 
if __name__ == '__main__':
    
    loadnpc()
#   paramcheck() 
    # Initialize the first level
    current = 0
 
    print("Please enter your name.")
    n = input()
    if n == '':
        n = "Mark"
    print("Please enter your asset.")
    print(statread)
    try:
        a = checkinput(input(), statread)
        if a == None:
            a = 2
    except ValueError:
        a = 2
    print("Your asset is {}.".format(statread[a]))
    time.sleep(1)
    print("Please enter your flaw.")
    print(statread)
    try:
        f = checkinput(input(), statread)
        if f == a or f == None:
            f = 1
    except ValueError:
        f = 1
    print("Your flaw is {}.".format(statread[f]))
    time.sleep(1)
    char = hero(n,a,f)
    char.assetmod(a)
    char.flawmod(f)
    char.adjust(a,f)    
 
    levels = []
    levels.append(make_level())
 
    char.set_position(find_staircase(levels[current], '<'))
    
## Initial Inventory (for debugging) ##############################################
    
    init = []
    init.append(item.itemwrapper(itemsys.make_item("Vulnerary"), 1, char.position.x, char.position.y))
    init.append(item.itemwrapper(itemsys.make_item("Silver Sword"), 1, char.position.x, char.position.y))
    init.append(item.itemwrapper(itemsys.make_item("Thoron"), 1, char.position.x, char.position.y))
    init.append(item.itemwrapper(itemsys.make_item("Seraph Robe"), 1, char.position.x, char.position.y))
    for i in range(len(init)):
        bag.append(init[i])
    
###################################################################################

    sys.stdout.write("\x1b[2J\x1b[H")
    while True:
        wait = False

        # Clear the terminal
        sys.stdout.write("\x1b[2J\x1b[H")

        if char.HP <= 0:
            print("Game over!")
            break        
        
        level = levels[current]
 
        # Swap in an '@' character in the position of the character, print the
        # level, and then swap back
        old, level[char.position.x][char.position.y] = level[char.position.x][char.position.y], 'Д' #changed @ with Д
        print_level(level)
        level[char.position.x][char.position.y] = old               
        if char.displvl == 20:
            sys.stdout.write('{} HP:{}/{} Class:{} Lvl:{} EXP:MAX Money:{}G\n'.format(char.name,char.HP,char.maxHP,char.type.name,char.displvl, char.money))
        else:
            sys.stdout.write('{} HP:{}/{} Class:{} Lvl:{} EXP:{}/100 Money:{}G\n'.format(char.name,char.HP,char.maxHP,char.type.name,char.displvl, char.exp, char.money))
        sys.stdout.write('Str:{} Mag:{} Def:{} Res:{} Skl:{} Spd:{} Lck:{}'.format(char.strength, char.magic, char.defense, char.resist, char.skill, char.speed, char.luck))
        sys.stdout.write('\n')
        if char.equip != None:
            if char.equip.dur == 1:
                sys.stdout.write('Equipped: {}, which has 1 use. Floor: {} Coins: {}'.format(char.equip.name,current+1,char.coins))
            else:
                sys.stdout.write('Equipped: {}, which has {} uses. Floor: {} Coins: {}'.format(char.equip.name, char.equip.dur,current+1,char.coins))
        else:
            sys.stdout.write('Equipped: Nothing! Floor: {}'.format(current+1))
        sys.stdout.write('\n')
 
        if level[char.position.x][char.position.y] == '?':
            for a in range(len(items)):
#                print("One item at {}, {} and I'm at {}, {}.".format(items[a].x,items[a].y,char.position.x,char.position.y))
                if items[a].x == char.position.x and items[a].y == char.position.y:
                    it = items[a]
            if len(bag) < capacity:
                bag.append(it)
                level[char.position.x][char.position.y] = '.'
                print("{} obtained.".format(it.obj.name))
                items.remove(it)
            else:
                print("Bag full")
 
        key = read_key()

        newpos = Point(char.position.x, char.position.y)
        didyoumove = True

        if key == 'q':
            break
        elif key == 'a': #old keys in this order: h,j,k,l
            newpos = Point(char.position.x-1, char.position.y)
            direction = "W"
        elif key == 's':
            newpos = Point(char.position.x, char.position.y+1)
            direction = "S"
        elif key == 'w':
            newpos = Point(char.position.x, char.position.y-1)
            direction = "N"
        elif key == 'd':
            newpos = Point(char.position.x+1, char.position.y)
            direction = "E"
        elif key == 'e':
            if char.equip != None and char.equip.obj.range == 2:
                target = enemypos(direction)
                if target != None:
                    herodamage = char.howtoattack(m)
                    sys.stdout.write('{} has dealt {} damage to {}.\n'.format(char.name, herodamage, m.name))
                    time.sleep(1)
                    if char.equip != None and char.equip.dur <= 0:
                        print("{} broke!".format(char.equip.obj.name))
                        char.equip = None
                    if char.equip != None and char.equip.dur > 0 and char.equip.obj.effect == "Brave" and m.HP > 0:
                        herodamage = char.howtoattack(m)
                        sys.stdout.write('ATTACK AGAIN! {} has dealt {} damage to {}.\n'.format(char.name, herodamage, m.name))
                    if m.HP > 0:
                        exppending = True
        elif key == 'h':
            direction = None
            help.display()
        elif key == 'i':
            if len(bag) == 0:
                continue
            else:
                direction = None
                didyoumove = False
                printinv(char, level, char.position, items, didyoumove)
                print_level(level)
        elif key == 'o':
            sys.stdout.write("Please set the direction that you are facing(WASD).")
            sys.stdout.flush()
            k = read_key()
            if k == 'a':
                direction = "W"
                sys.stdout.write("Facing west.")
            elif k == 's':
                direction = "S"
                sys.stdout.write("Facing south.")
            elif k == 'd':
                direction = "E"
                sys.stdout.write("Facing east.")
            elif k == 'w':
                direction = "N"
                sys.stdout.write("Facing north.")
            else:
                continue
            sys.stdout.flush()
            didyoumove = False
        else:
            continue
        if didyoumove == True:

            exppending = False
            target = None

            if random.random() < MONSTER_PROB:
                    p = generate(level,'m')
                    which = 0
                    if p:
                        if current >= 20:
                            which = 1
                        m1 = MONSTERS[which][random.randrange(len(MONSTERS))]
                        #print("Making a {}".format(m1[0])) #debug
                        m = Monster(p,m1[0],m1[1],getbase(m1[0]),m1[2])
                        m.lvlchange()
                        #print("It is level {}".format(m.lvl)) #debug
                        m.grow(m.lvl)
                        monsters.append(m)
     
            if level[newpos.x][newpos.y] == '>':
                #clear monsters
                for i in range(len(monsters) - 1, -1, -1):
                    monsters[i].die(level)
                    monsters.remove(monsters[i]) 
                # Moving down a level
                if current == len(levels) - 1:
                    levels.append(make_level())
                current += 1                            
                print("Entering level {}".format(current))
                if current == 40:
                    sys.stdout.write("Looks like you reached the end of this labyrinth.")
                    read_key()
                    sys.stdoud.write("I applaud you, {}. Thanks for playing.".format(char.name))
                    read_key()
                    break
                newpos = find_staircase(levels[current], '<')

            elif level[newpos.x][newpos.y] == '<':
                # Moving up a level
                if current > 0:
                    #clear monsters
                    for i in range(len(monsters) - 1, -1, -1):
                        monsters[i].die(level)
                        monsters.remove(monsters[i])
                    current -= 1
                    newpos = find_staircase(levels[current], '>')

            elif level[newpos.x][newpos.y] == '?':
                newitem = True

            elif level[newpos.x][newpos.y] == '0':
                char.coins += 1
                sys.stdout.write("Obtained 1 coin. These will reveal more items in shops.")
                sys.stdout.flush()
                time.sleep(1)
                level[newpos.x][newpos.y] = '.'

            elif level[newpos.x][newpos.y] in NPC_ICONS:
                for i in range(len(npcs)):
                    if level[newpos.x][newpos.y] == level[npcs[i].x][npcs[i].y] and direction != None:
                        print("You are standing on a {}".format(npcs[i].i.job))
                        dothings(char, npcs[i], current)
                

            elif level[newpos.x][newpos.y] == 'm':
                # Walked into a monster, attack!
                for m in monsters:
                   if m.pos == newpos:
                        herodamage = char.howtoattack(m)
                        sys.stdout.write('{} has dealt {} damage to {}.\n'.format(char.name, herodamage, m.name))
                        time.sleep(1)
                        if char.equip != None and char.equip.dur <= 0:
                            print("{} broke!".format(char.equip.obj.name))
                            char.equip = None
                        if char.equip != None and char.equip.dur > 0 and char.equip.obj.effect == "Brave" and m.HP > 0:
                            herodamage = char.howtoattack(m)
                            sys.stdout.write('ATTACK AGAIN! {} has dealt {} damage to {}.\n'.format(char.name, herodamage, m.name))
                        if m.HP > 0:
                            exppending = True
                            target = m             
                newpos = char.position

            elif level[newpos.x][newpos.y] not in MOVEABLE and level[newpos.x][newpos.y] not in NPC_ICONS:
                # Hit a wall, should stay put
                newpos = char.position
     
            char.set_position(newpos)
           
            # Update the monsters
            for m in monsters:
                if m.HP <= 0:
                    m.die(level)
                    monsters.remove(m)
                    sys.stdout.write('{} has killed a {}.\n'.format(char.name, m.name))
                    if char.displvl < 20:
                        print('Dealt {} damage.'.format(herodamage))
                        char.expgain(char.calcexp(m,herodamage,True))
                    wait = True
                    continue

                d0 = dist(newpos, m.pos)
                if d0 < 15:
                    # Move the monster towards the player
                    for p in dxdy(m.pos):
                        d1 = dist(newpos, p)
                        if newpos == p:
                            # Monster moves into player, attack!
                            d = m.howtoattack(char)
                            sys.stdout.write('{} took {} damage from {}.\n'.format(char.name,d, m.name))
                            if m.equip != None and m.equip.dur > 0 and m.equip.obj.effect == "Brave" and char.HP > 0:
                                d = char.howtoattack(m)
                                sys.stdout.write('ATTACK AGAIN! {} took {} damage from {}.\n'.format(char.name,d, m.name))
                            wait = True
                        elif level[p.x][p.y] in MOVEABLE and d1 < d0:
                            m.move(level, p)
                            break

        #Print statements and gains here?
            if exppending and char.displvl < 20:
                char.expgain(char.calcexp(target,herodamage,False))

        #Update inventory here
            update()

        if wait:
            sys.stdout.flush()
            time.sleep(1)
