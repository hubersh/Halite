#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction

# This library allows you to generate random numbers.
import random

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging
from random import randint

import math

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("New")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

count = 10
width = game.game_map.width
height = game.game_map.height
command_list = []
ship_list = []
target_list = []
move_list = []
drop_list = []

newSpawn = False
# global num_turns
num_turns = 0
totalShips = 18
slamBool = False
settingDropOff = False
dropCount = 0
currentDrop = None


def calculateDistance(x1, y1, x2, y2):
    vals = math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2)
    return math.sqrt(vals)

class DropOff:
    def __init__(self, drop):
        self.dropOff = drop
        self.dropRange = 5
        self.x = drop.position.x
        self.y = drop.position.y

    def adjust_range(self, avg):
        if avg < 60:
            self.dropRange += 1
            logging.info("Range extended to: {}.".format(self.dropRange))


class Miner:
    def __init__(self, shipId):
        self.targetX = 0
        self.targetY = 0
        self.ship = me.get_ship(shipId)
        self.hasTarget = False
        self.headingHome = False
        self.slam = False
        self.dropOff = False
        self.avoid = False
        self.minPickUp = 50


    def target_highest(self):
        #Dont seek the new highest if we are already seeking a target (Adjust later to handle
        #things like a differnt ship taking a space and such...)
        if self.hasTarget is False:
            highest = 0
            highX= 0
            highY = 0
            #Calculate the average value of halite in our range while looping
            sum = 0
            sumCount = 0
            tempDrop = self.getHomeDrop()
            homeX = tempDrop.x
            homeY = tempDrop.y
            for x in range(homeX - tempDrop.dropRange, homeX + tempDrop.dropRange):
                for y in range(homeY - tempDrop.dropRange, homeY + tempDrop.dropRange):
                    if x >= 0 and x <= width and y >= 0 and y <= height:
                        tempAmount = game.game_map[hlt.entity.Position(x, y)].halite_amount
                        # distance = game.game_map.calculate_distance(hlt.entity.Position(homeX, homeY), hlt.entity.Position(x, y))
                        distance = calculateDistance(homeX, homeY, x, y)
                        if tempAmount > highest and self.target_avoid(x, y) is True:
                            highest = tempAmount
                            highX = x
                            highY = y
                        sumCount += 1
                        sum += tempAmount

            self.targetX = highX
            self.targetY = highY
            target_list.append((highX, highY))
            self.hasTarget = True
            tempDrop.adjust_range(sum / sumCount)

    def target_highest2(self):
        #Dont seek the new highest if we are already seeking a target (Adjust later to handle
        #things like a differnt ship taking a space and such...)
        if self.hasTarget is False:
            highX= 0
            highY = 0
            #Calculate the average value of halite in our range while looping
            sum = 0
            sumCount = 0
            tempDrop = self.getHomeDrop()
            homeX = tempDrop.x
            homeY = tempDrop.y
            for x in range(homeX - tempDrop.dropRange, homeX + tempDrop.dropRange):
                for y in range(homeY - tempDrop.dropRange, homeY + tempDrop.dropRange):
                    if x >= 0 and x <= width and y >= 0 and y <= height:
                        tempAmount = game.game_map[hlt.entity.Position(x, y)].halite_amount

                        if tempAmount > 200 and self.target_avoid(x, y) is True:
                            highX = x
                            highY = y
                        sumCount += 1
                        sum += tempAmount

            self.targetX = highX
            self.targetY = highY
            target_list.append((highX, highY))
            self.hasTarget = True
            tempDrop.adjust_range(sum / sumCount)

    #Second time is the charm?
    def seek2(self):
        # self.adjustMinPick()
        self.target_highest()
        self.avoid = False

        x = self.ship.position.x
        y = self.ship.position.y
        desireX = x
        desireY = y

        if game.game_map[hlt.entity.Position(x, y)].halite_amount > self.minPickUp and self.ship.halite_amount < 999 and self.slam is False:
            command_list.append(self.ship.stay_still())
            return
        if self.ship.halite_amount > 980 and self.setDropOff is False:
            if self.headingHome is False:
                self.clearTarget()
                self.target_home()


        ideal_moves = []
        possible_moves = []


        if x < self.targetX:
            ideal_moves.append((x + 1, y, "e"))
        if x  > self.targetX:
            ideal_moves.append((x - 1, y, "w"))
        if y  < self.targetY:
            ideal_moves.append((x, y + 1, "s"))
        if y > self.targetY:
            ideal_moves.append((x, y - 1, "n"))

        #If our ideal moves are not valid, then pick from all possible moves
        if game.game_map[hlt.entity.Position(x + 1, y)].is_occupied is False and self.willMove(x + 1, y) is False:
            if self.wrap(x+1) is False:
                possible_moves.append((x + 1, y, "e"))
        if game.game_map[hlt.entity.Position(x - 1, y)].is_occupied is False and self.willMove(x - 1, y) is False:
            if self.wrap(x-1) is False:
                possible_moves.append((x - 1, y, "w"))
        if game.game_map[hlt.entity.Position(x, y + 1)].is_occupied is False and self.willMove(x, y + 1) is False:
            if self.wrap(y+1) is False:
                possible_moves.append((x, y + 1, "s"))
        if game.game_map[hlt.entity.Position(x, y - 1)].is_occupied is False and self.willMove(x, y - 1) is False:
            if self.wrap(y-1) is False:
                possible_moves.append((x, y - 1, "n"))

        #No ideal moves means we are standing on the target
        if len(ideal_moves) == 0:
            #Are we a drop off?
            if self.dropOff is True:
                if me.halite_amount > 4000:
                    command_list.append(self.ship.make_dropoff())
                    # global settingDropOff
                    # settingDropOff = False
                else:
                    command_list.append(self.ship.stay_still())
                return

            #If we reached home...
            if self.headingHome is True:
                self.headingHome = False
                self.hasTarget = False
                self.seek2()
                return


            if self.ship.halite_amount > 980 or game.game_map[hlt.entity.Position(self.targetX, self.targetY)].halite_amount < 20:
                if self.headingHome is False:
                    self.target_home()

            #Otherwise continue to collect halite
            else:
                command_list.append(self.ship.stay_still())
            return

        for move in ideal_moves:
            desireX = move[0]
            desireY = move[1]
            tempDrop = self.getHomeDrop()

            if self.slam is True and desireX == tempDrop.x and desireY == tempDrop.y:
                command_list.append(self.ship.move(move[2]))
                return

            if game.game_map[hlt.entity.Position(desireX, desireY)].is_occupied:
                found = False
                for s in ship_list:
                    if s.ship.position.x == desireX and s.ship.position.y == desireY:
                        found = True
                        #Y is to make sure that they will only move randomly if they are not lined up on the ideal Y axis.
                        if (self.headingHome is True and s.headingHome is False and self.ship.position.y == me.shipyard.position.y) or s.avoid is True:
                            command_list.append(self.ship.stay_still())
                            return
                if found is False and desireX == me.shipyard.position.x and desireY == me.shipyard.position.y:
                    command_list.append(self.ship.move(move[2]))
                    return

            #Is this not a safe move?
            if self.willMove(desireX, desireY) is True or game.game_map[hlt.entity.Position(desireX, desireY)].is_occupied:
                ideal_moves.remove(move)

            #If it is safe then just move there.
            else:
                command_list.append(self.ship.move(move[2]))
                move_list.append((desireX, desireY))
                self.avoid = True
                return

        #If there are no possible moves then just stay still
        if len(possible_moves) == 0:
            command_list.append(self.ship.stay_still())
        else:
            self.avoid = True
            rand = randint(0, len(possible_moves) - 1)
            command_list.append(self.ship.move(possible_moves[rand][2]))
            move_list.append((possible_moves[rand][0], possible_moves[rand][1]))

    def isOpposite(self, newDir, dirs):
        for d in dirs:
            if newDir == "s":
                if d[2] == "n":
                    return True
            if newDir == "n":
                if d[2] == "s":
                    return True
            if newDir == "e":
                if d[2] == "w":
                    return True
            if newDir == "w":
                if d[2] == "e":
                    return True
        return False


    def target_home(self):
        tempDrop = self.getHomeDrop()
        self.clearTarget()

        self.targetX = tempDrop.x
        self.targetY = tempDrop.y
        self.headingHome = True

    def wrap(self, num):
        if num <= 0 or num >= width:
            return True
        return False

    def getHomeDrop(self):
        distance = 1000000
        closest = drop_list[0]
        for drop in drop_list:
            tempDistance = calculateDistance(drop.x, drop.y, self.ship.position.x, self.ship.position.y)
            if tempDistance < distance:
                distance = tempDistance
                closest = drop

        return closest

    def target_avoid(self, x, y):
        for coord in target_list:
            if x == coord[0] and y == coord[1]:
                return False
        return True

    def hasAvoided(self, x, y):
        for myShip in ship_list:
            if myShip.ship.position.x == x and myShip.ship.position.y == y:
                return myShip.avoiding
        return False

    def willMove(self, x, y):
        for coord in move_list:
            if x == coord[0] and y == coord[1]:
                # logging.info("Someone will move to:{},{}".format((x,y)))
                return True
        return False

    def clearTarget(self):
        for coord in target_list:
            if self.targetX == coord[0] and self.targetY == coord[1]:
                target_list.remove(coord)

    def setDropOff(self, x, y):
        self.dropOff = True
        self.targetX = x
        self.targetY = y

    def adjustMinPick(self):
        temp = self.getHomeDrop()
        if temp.dropRange > 11:
            self.minPickUp = 15
        else:
            self.minPickUp = 50



def checkDead():
    if len(me.get_ships()) != len(ship_list):
        for myShip in ship_list:
            idFound = False
            tempId = myShip.ship.id
            for s in me.get_ships():
                realId = s.id
                if tempId == realId:
                    idFound = True
            if idFound is False:
                ship_list.remove(myShip)
                command_list = []

def spawnShip():
    global slamBool
    global settingDropOff
    safeSpawn = True
    if game.game_map[hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y)].is_occupied is True or settingDropOff is True:
        safeSpawn = False
    for move in move_list:
        if move[0] == me.shipyard.position.x and move[1] == me.shipyard.position.y:
            safeSpawn = False
            break


    # Spawn a new ship for this temp condition
    if len(me.get_ships()) < totalShips and me.halite_amount >= 1000 and num_turns / (300+25*width/8) < .6 :
        if game.game_map[hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y)].is_occupied is False and safeSpawn is True:
            command_list.append(me.shipyard.spawn())
            newSpawn = True
            tempList = []
            for i in me.get_ships():
                tempList.append(i.id)
            logging.info("ship_list: {}".format(tempList))

def defend():
    if game.game_map[hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y)].is_occupied is True:
        owned = False
        for ship in ship_list:
            if ship.ship.position.x == me.shipyard.position.x and ship.ship.position.y == me.shipyard.position.y:
                owned = True
                break

        if owned is False and me.halite_amount > 1000:
            command_list.append(me.shipyard.spawn())

def slam():
    global slamBool
    global num_turns
    for ship in ship_list:
        # distance = game.game_map.calculate_distance(hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y), hlt.entity.Position(ship.ship.position.x, ship.ship.position.y))
        distance = calculateDistance(ship.ship.position.x, ship.ship.position.y, me.shipyard.position.x, me.shipyard.position.y)
        if (300+25*width/8) - num_turns < distance * 2.3:
            ship.target_home()
            ship.slam = True
    num_turns += 1

#For some reason my bot sometimes can't recognize when a ship dies...
def pickMoves():
    for move in command_list:
        logging.info("Command: {}.".format(move))
        split = move.split(" ")
        try:
            id = int(split[1])
            if me.has_ship(id) is False:
                command_list.remove(move)
        except:
            num = 0

def numMiners():
    sum = 0
    for x in range(width):
        for y in range(height):
            sum += game.game_map[hlt.entity.Position(x, y)].halite_amount

    avg = sum / (width * height)
    global totalShips
    totalShips = int (avg / 8)

def getTotalRange(x, y, r):
    sum = 0
    highX = 0
    highY = 0
    maxAmt = 0
    for tempX in range(x - r, x + r):
        for tempY in range(y - r, y + r):
            amt = game.game_map[hlt.entity.Position(tempX, tempY)].halite_amount
            sum += amt

            if amt > maxAmt:
                maxAmt = amt
                highX = tempX
                highY = tempY

    return (highX, highY, sum)

def determineDrop(r):
    highSum = 0
    highX = 0
    highY = 0
    for x in range(r, width - r):
        for y in range(r, width - r):
            safe = True
            for d in drop_list:
                if game.game_map.calculate_distance(hlt.entity.Position(x, y), hlt.entity.Position(d.dropOff.position.x, d.dropOff.position.y)) <= width * 0.15:
                    safe = False
                if calculateDistance(x, y, me.shipyard.position.x, me.shipyard.position.y) > 0.3 * width:
                    safe = False
            if safe is True:
                tempList = getTotalRange(x, y, r)
                tempSum = tempList[2]
                if tempSum > highSum:
                    highSum = tempSum
                    # highX =  getTotalRange(x, y, r)[0]
                    # highY =  getTotalRange(x, y, r)[1]
                    # highX = tempList[0]
                    # highY = tempList[1]

                    highX = x
                    highY = y
    logging.info("Ideal drop: {}, {}".format(highX, highY))
    return (highX, highY)

def spawnDrop():
    global settingDropOff, totalShips, dropCount, currentDrop
    percent = num_turns / (300+25*width/8)

    if currentDrop.dropRange >= 7 and settingDropOff is False and dropCount < 1:
        loc = determineDrop(int(.15 * width))
        x = loc[0]
        y = loc[1]
        settingDropOff = True
        dropCount += 1
        totalShips = int(totalShips * 1.8)
        logging.info("Ideal drop: {}, {}".format(x, y))

        for ship in ship_list:
            if ship.ship.position.x != me.shipyard.position.x and ship.ship.position.y != me.shipyard.position.y:
                ship.setDropOff(x, y)
                return

def detectNewDrop():
    for d in me.get_dropoffs():
        tempId = d.id
        found = False
        for myDrop in drop_list:
            if tempId == myDrop.dropOff.id:
                found = True
                break
        if found is False:
            newDrop = DropOff(d)
            drop_list.append(newDrop)
            currentDrop = newDrop
            global settingDropOff
            settingDropOff = False

numMiners()

me = game.me
drop_list.append(DropOff(me.shipyard))
currentDrop = drop_list[0]
while True:
    #Update the frame
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    game_map = game.game_map

    checkDead()


    #Reset the command list
    command_list = []
    move_list = []

    #Check if there was a new spawned ship, and add it to the ship object list.
    # if newSpawn is True:
    #     ship_list.append(Miner(me.get_ships()[0].id))
    #     newSpawn = False
    if len(me.get_ships()) > len(ship_list):
        for newShip in me.get_ships():
            found = False
            for knownShip in ship_list:
                if newShip.id == knownShip.ship.id:
                    found = True
                    break
            if found is False:
                ship_list.append(Miner(newShip.id))
        newSpawn = False

    for tempShip in ship_list:
        tempShip.seek2()

    spawnShip()

    defend()
    slam()
    detectNewDrop()
    spawnDrop()
    pickMoves()

    game.end_turn(command_list)
