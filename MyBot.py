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
# global num_turns
num_turns = 0


class Miner:
    def __init__(self, shipId, type):
        self.targetX = 0
        self.targetY = 0
        self.ship = me.get_ship(shipId)
        self.hasTarget = False
        self.headingHome = False
        self.avoiding = False
        self.type = type
        self.slam = False

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
        if self.type == 0:
            self.target_highest()
        else:
            self.target_ideal()

        self.avoiding = False

        x = self.ship.position.x
        y = self.ship.position.y
        desireX = x
        desireY = y

        if game.game_map[hlt.entity.Position(x, y)].halite_amount > 50 and self.ship.halite_amount < 999:
            command_list.append(self.ship.stay_still())
            return
        if self.ship.halite_amount > 980:
            if self.headingHome is False:
                self.clearTarget()
                self.target_home()


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
                return

            if self.type == 0:
                if self.ship.halite_amount > 980 or game.game_map[hlt.entity.Position(self.targetX, self.targetY)].halite_amount < 20:
                    if self.headingHome is False:
                        self.clearTarget()
                        self.target_home()

                #Otherwise continue to collect halite
                else:
                    command_list.append(self.ship.stay_still())
                return

            else:
                if self.ship.halite_amount > 980:
                    if self.headingHome is False:
                        self.clearTarget()
                        self.target_home()

                # Space less than 20? Head to another
                elif game.game_map[hlt.entity.Position(self.targetX, self.targetY)].halite_amount < 20:
                    self.hasTarget = False
                    self.clearTarget()
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

            if self.slam is True and desireX == me.shipyard.position.x and desireY == me.shipyard.position.y:
                command_list.append(self.ship.move(ideal_moves[rand][2]))
                return

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

    def clearTarget(self):
        for coord in target_list:
            if self.targetX == coord[0] and self.targetY == coord[1]:
                target_list.remove(coord)


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
    # Spawn a new ship for this temp condition
    if len(me.get_ships()) < 25 and me.halite_amount > 1000:
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

        if owned is False:
            command_list.append(me.shipyard.spawn())

def slam():
    global num_turns
    if (300+25*width/8) - num_turns < 30:
        for ship in ship_list:
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
        if game.game_map.calculate_distance(hlt.entity.Position(curShip.ship.position.x, curShip.ship.position.y), hlt.entity.Position(me.shipyard.position.x, me.shipyard.position.y)) < 1.5:
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
                ship_list.append(Miner(newShip.id, 0))
        newSpawn = False

    spawnShip()

    for tempShip in ship_list:
        tempShip.seek2()

    defend()
    slam()
    pickMoves()

    game.end_turn(command_list)
