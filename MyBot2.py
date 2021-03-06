#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction
import random
import math
import logging

"""<<<Game Begin>>>"""

# This game object contains the initial game state.
game = hlt.Game()
width = game.game_map.width
height = game.game_map.height

def calculateDistance(x1, y1, x2, y2):
    vals = math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2)
    return math.sqrt(vals)


class Miner:
    def __init__(self, id):
        self.id = id
        self.hasTarget = False
    def find_path(self):
        return Direction.Still
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

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

ship_states = {}
while True:

    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map


    command_queue = []

    #order of directions
    direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

    position_choices = []
    for ship in me.get_ships():
        if ship.id not in ship_states:
            #assuming that since it is not in dict, it just spawned, so start collecting!
            ship_states[ship.id] = "collection"
        #for each turn, a ship can only move one direction
        #here is getting the choices, like coordinates
        position_options = ship.position.get_surrounding_cardinals() + [ship.position]

        #movement mapped to coordinate i.e. {(0,1): (19,38)}
        position_dict = {}

        #mapped to halite amount i.e. {(0,1): 500}
        halite_dict = {}

        #populating the position dictionary
        for n, direction in enumerate(direction_order):
            position_dict[direction] = position_options[n]


        #populating the halite dictionary
        for direction in position_dict:
            position = position_dict[direction]
            halite_amount = game_map[position].halite_amount
            #if we don't have a ship movign towards same halite
            if position_dict[direction] not in position_choices:
                if direction == Direction.Still:
                    halite_dict[direction] = halite_amount*3
                else:
                    halite_dict[direction] = halite_amount

        #ship.position.get_all_cardinals() returns [Direction.North, Dir...]<-what we need to pass to moves

        if game.turn_number != game.turn_number%15:
            logging.info(position_options)


        #TODO:LOOK INTO naive_navigate() make it better :D
        #we are going to be depositing
        if ship_states[ship.id] == "depositing":
            #look into multiple shipyards
            move = game_map.naive_navigate(ship, me.shipyard.position)
            position_choices.append(position_dict[directional_choice])
            command_queue.append(ship.move(move))
            if move == Direction.Still:
                ship_states[ship.id] = "collection"
                
        elif ship_states[ship.id] == "collection":
            #navigate to highest halite square, that shouldn't be headed towards
            directional_choice = max(halite_dict, key = halite_dict.get)
            position_choices.append(position_dict[directional_choice])
            #navigating to the most halite
            command_queue.append(ship.move(directional_choice))
            #if we want to  stop collecting at 900 halite
            if ship.halite_amount > constants.MAX_HALITE *.85:
                ship_states[ship.id] = "depositing"


    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())


    game.end_turn(command_queue)
