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

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")

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

newSpawn = False
shipRange = 6


class Miner:
    def __init__(self, shipId):
        self.targetX = 0
        self.targetY = 0
        self.ship = me.get_ship(shipId)
        self.hasTarget = False
        self.headingHome = False

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
            for x in range(width):
                for y in range(height):
                    tempAmount = game.game_map[hlt.entity.Position(x, y)].halite_amount
                    distance = game.game_map.calculate_distance(hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y), hlt.entity.Position(x, y))
                    if tempAmount > highest and distance <= shipRange and self.target_avoid(x, y) is True:
                        highest = tempAmount
                        highX = x
                        highY = y

                    #Calculate average
                    if distance <= shipRange:
                        sumCount += 1
                        sum += tempAmount
            self.targetX = highX
            self.targetY = highY
            target_list.append((highX, highY))
            self.hasTarget = True
            self.adjust_range(sum / sumCount)

    def seek(self):
        # self.check_home()

        self.target_highest()
        x = self.ship.position.x
        y = self.ship.position.y

        # logging.info("X and Y {} {}.".format(self.targetX, self.targetY))

        if x < self.targetX:
            self.miner_avoid(x, y, 1)
        elif x  > self.targetX:
            self.miner_avoid(x, y, 3)
        elif y  < self.targetY:
            self.miner_avoid(x, y, 2)
        elif y > self.targetY:
            self.miner_avoid(x, y, 0)
        else:
            #If we are heading home clear the target and look for a new one.
            if self.headingHome is True:
                self.headingHome = False
                self.hasTarget = False
                return
            #Else we want to gather the target halite.
            command_list.append(self.ship.stay_still())

            #Check if we should stop collecting and head back to the base.
            if self.ship.halite_amount > 999 or game.game_map[hlt.entity.Position(self.targetX, self.targetY)].halite_amount < 30:
                if self.headingHome is False:
                    self.target_home()

    def target_home(self):
        self.targetX = me.shipyard.position.x
        self.targetY = me.shipyard.position.y
        self.headingHome = True

    def adjust_range(self, avg):
        if avg < 80:
            global shipRange
            shipRange += 1
            logging.info("Range extended to: {}.".format(shipRange))

    def target_avoid(self, x, y):
        for coord in target_list:
            if x == coord[0] and y == coord[1]:
                return False

        # if game.game_map[hlt.entity.Position(self.targetX, self.targetY)].is_occupied

        return True

    # Dir is the desired direction that the ship wants to move.
    # 0 -> North
    # 1 -> East
    # 2 -> South
    # 3 -> West
    def miner_avoid(self, x, y, dir):
        newDir = dir

        if dir == 0:
            desireX = x
            desireY = y - 1
        if dir == 1:
            desireX = x + 1
            desireY = y
        if dir == 2:
            desireX = x
            desireY = y + 1
        if dir == 3:
            desireX = x - 1
            desireY = y

        switched = False
        still = False

        while True:
            #Is this spot already filled with another ship?
            if game.game_map[hlt.entity.Position(desireX, desireY)].is_occupied:
                #If another ship is trying to move to this spot, then
                #Try and temporarily switch the direction that the turtle is traveling.
                # (This direction is prependicular to the current desired direction)
                if switched is False:
                    if dir == 0:
                        newDir = 3
                        desireX = x - 1
                        desireY = y
                    elif dir == 1:
                        newDir = 0
                        desireX = x
                        desireY = y - 1
                    elif dir == 2:
                        newDir = 1
                        desireX = x + 1
                        desireY = y
                    elif dir == 3:
                        newDir = 2
                        desireX = x
                        desireY = y + 1
                    switched = True
                else:
                    still = True
                    break
            else:
                break

        #Is another ship trying to move to this spot?
        for coord in move_list:
            if desireX == coord[0] and desireY == coord[1]:
                still = True
                break

        if still is True:
            command_list.append(self.ship.stay_still())
            # return False
        else:
            move_list.append((desireX, desireY))

            if newDir == 0:
                command_list.append(self.ship.move(Direction.North))
                return
            elif newDir == 1:
                command_list.append(self.ship.move(Direction.East))
                return
            elif newDir == 2:
                command_list.append(self.ship.move(Direction.South))
                return
            elif newDir == 3:
                command_list.append(self.ship.move(Direction.West))
                return
        # move_list.append((desireX, desireY))
        # return True

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

while True:
    #Update the frame
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    #Reset the command list
    command_list = []
    move_list = []

    checkDead()

    safeSpawn = True
    for curShip in ship_list:
        if game.game_map.calculate_distance(hlt.entity.Position(curShip.ship.position.x, curShip.ship.position.y), hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y)) < 3:
            safeSpawn = False
            break

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


    #Spawn a new ship for this temp condition
    if len(me.get_ships()) < 5 and me.halite_amount > 1000:
        if game.game_map[hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y)].is_occupied is False and safeSpawn is True:
            command_list.append(me.shipyard.spawn())
            newSpawn = True
            tempList = []
            for i in me.get_ships():
                tempList.append(i.id)
            logging.info("ship_list: {}".format(tempList))


    for tempShip in ship_list:
        tempShip.seek()

    # Send your moves back to the game environment, ending this turn.
    # tempMoves = []
    # for i in command_list:
    #     sep = i.split(" ")
    #     if len(sep) > 1:
    #         id = sep[1]
    #         for move in tempMoves:
    #             if move == id:
    #                 logging.info("REMOVED A DUPLICATE")
    #                 command_list.remove(i)
    #         tempMoves.append(id)
        # logging.info("Move: {}".format(i))
        # logging.info("Type: {}".format(type(i)))
    game.end_turn(command_list)
