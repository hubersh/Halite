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
        self.avoiding = False

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

    def target_ideal(self):
        if self.hasTarget is False:
            minDistance = 1000000;
            highX= 0
            highY = 0
            #Calculate the average value of halite in our range while looping
            sum = 0
            sumCount = 0
            for x in range(width):
                for y in range(height):
                    tempAmount = game.game_map[hlt.entity.Position(x, y)].halite_amount
                    distance = game.game_map.calculate_distance(hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y), hlt.entity.Position(x, y))
                    if tempAmount > 30 and distance <= shipRange and self.target_avoid(x, y) is True and distance < minDistance:
                        minDistance = distance
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

    #Seconds time is the charm?
    def seek2(self):
        self.target_highest()
        self.avoiding = False
        # self.target_ideal()
        x = self.ship.position.x
        y = self.ship.position.y
        desireX = x
        desireY = y

        ideal_moves = []
        possible_moves = []

        #Gather ideal moves
        if x < self.targetX:
            ideal_moves.append((x + 1, y, "e"))
        if x  > self.targetX:
            ideal_moves.append((x - 1, y, "w"))
        if y  < self.targetY:
            ideal_moves.append((x, y + 1, "s"))
        if y > self.targetY:
            ideal_moves.append((x, y - 1, "n"))

        #No ideal moves means we are standing on the target
        if len(ideal_moves) == 0:
            #If we reached home...
            if self.headingHome is True:
                self.headingHome = False
                self.hasTarget = False

            #Over 900 halite? Start to head back
            elif self.ship.halite_amount > 900:
                if self.headingHome is False:
                    self.target_home()

            # Space less than 20? Head to another
            elif game.game_map[hlt.entity.Position(self.targetX, self.targetY)].halite_amount < 20:
                self.hasTarget = False
                self.target_ideal()

            #Otherwise continue to collect halite
            else:
                command_list.append(self.ship.stay_still())
            return

        #Pick a random valid move and see if we can move in that direction.
        while len(ideal_moves) != 0:
            rand = randint(0, len(ideal_moves) - 1)
            desireX = ideal_moves[rand][0]
            desireY = ideal_moves[rand][1]
            #Is this not a safe move?
            if game.game_map[hlt.entity.Position(desireX, desireY)].is_occupied or self.willMove(desireX, desireY) is True:
                del ideal_moves[rand]

            #If it is safe then just move there.
            else:
                command_list.append(self.ship.move(ideal_moves[rand][2]))
                move_list.append((desireX, desireY))
                return

        #If our ideal moves are not valid, then pick from all possible moves
        if game.game_map[hlt.entity.Position(x + 1, y)].is_occupied is False and self.willMove(x + 1, y) is False:
            possible_moves.append((x + 1, y, "e"))
        if game.game_map[hlt.entity.Position(x - 1, y)].is_occupied is False and self.willMove(x - 1, y) is False:
            possible_moves.append((x - 1, y, "w"))
        if game.game_map[hlt.entity.Position(x, y + 1)].is_occupied is False and self.willMove(x, y + 1) is False:
            possible_moves.append((x, y + 1, "s"))
        if game.game_map[hlt.entity.Position(x, y - 1)].is_occupied is False and self.willMove(x, y - 1) is False:
            possible_moves.append((x, y - 1, "n"))

        #If there are no possible moves then just stay still
        if len(possible_moves) == 0:
            command_list.append(self.ship.stay_still())
        else:
            rand = randint(0, len(possible_moves) - 1)
            command_list.append(self.ship.move(possible_moves[rand][2]))
            move_list.append((possible_moves[rand][0], possible_moves[rand][1]))

    def target_home(self):
        self.targetX = me.shipyard.position.x
        self.targetY = me.shipyard.position.y
        self.headingHome = True

    def adjust_range(self, avg):
        if avg < 100:
            global shipRange
            shipRange += 1
            logging.info("Range extended to: {}.".format(shipRange))

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
                logging.info("Someone will move to:{}.".format((x,y)))
                return True
        return False

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

while True:
    #Update the frame
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    checkDead()

    #Reset the command list
    command_list = []
    move_list = []

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
    if len(me.get_ships()) < 8 and me.halite_amount > 1000:
        if game.game_map[hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y)].is_occupied is False and safeSpawn is True:
            command_list.append(me.shipyard.spawn())
            newSpawn = True
            tempList = []
            for i in me.get_ships():
                tempList.append(i.id)
            logging.info("ship_list: {}".format(tempList))


    for tempShip in ship_list:
        tempShip.seek2()


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
