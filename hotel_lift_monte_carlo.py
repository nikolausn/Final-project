import numpy as np
import networkx as nx
import logging
import random
import math
from pynput import keyboard
import threading
import time
import typing

logging.getLogger().setLevel(logging.DEBUG)
logging.debug("TEST")

# make a rules using graph network
lift_number = 4
number_of_floor = 20
conference_room_floor = 2


# define the class Person, Attendance, and Room for name requirement
# implementation later
class Person:
    pass


class Attendance:
    pass


class Room:
    pass


class RandomMovementGenerator():
    """
    initiate random movement for target object
    since generating random in the object will
    result in the same value (same seed)
    This class should be a singleton, but I think we don't need to use this since we add
    the implementation in the object level
    """

    def __init__(self, person, lift):
        self._random_move_time = GaussianDist(mu=person["move_time"], sigma=person["move_time"] / 2, low=1,
                                              high=person["move_time"] * 2)
        self._random_outside_time = GaussianDist(mu=person["outside_time"], sigma=person["outside_time"] / 2, low=1,
                                                 high=person["outside_time"] * 2)
        self._random_close_door = GaussianDist(mu=lift["max_waiting_time"] / 2, sigma=lift["sigma"], low=1,
                                               high=lift["max_waiting_time"])

    def random_move_time(self):
        return self._random_move_time.random()

    def random_outside_time(self):
        return self._random_outside_time.random()

    def gen_close_door(self):
        self._door
        return math.ceil(self._random_close_door.random())


class RoomType:
    """
    RoomType is a base class of a room class,
    this class contains name and capacity to determine how many people can a room handle
    """

    def __init__(self, name_type: str, capacity: int):
        self._name_type = name_type
        self._capacity = capacity

    @property
    def name_type(self):
        return self._name_type

    @property
    def capacity(self):
        return self._capacity


class RandomDist():
    """
    RandomDist is a base abstract class to build a Random distribution.
    This class contains an abstract method for building a random generator
    Inherited class must implement this method
    """

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def random(self):
        """
        This class is an abstract method for implementation class
        should return a random value based on the configuration given in the implementation
        :return:
        """
        pass


class GaussianDist(RandomDist):
    """
    A random Gaussian Distribution generator
    """

    def __init__(self, mu: float, sigma: float, low: float, high: float):
        """
        To use this class we must provide mu (mean), sigma (standard deviation), low value, and high value

        :param mu: mean, in which the normal gaussian will have most distribution
        :param sigma: a standard deviation for a random gaussian parameter
        :param low: the lowest value this random generator must provide
        :param high: the highest value this random generator must provide
        """
        RandomDist.__init__(self, "Gaussian")
        self._mu = mu
        self._sigma = sigma
        self._low = low
        self._high = high

    def random(self):
        """
        This will return a random gaussian generator by checking the low value and highest value
        :return:
        """
        x = self._low - 1
        while x < self._low or x > self._high:
            x = random.gauss(self._mu, self._sigma)
        return x


class GaussianDiscrete(GaussianDist):
    """
    A random Gaussian Discrete generator
    This will include all the feature that gaussian has but will return a discrete value using round
    """

    def __init__(self, mu: float, sigma: float, low: float, high: float):
        """
               To use this class we must provide mu (mean), sigma (standard deviation), low value, and high value

               :param mu: mean, in which the normal gaussian will have most distribution
               :param sigma: a standard deviation for a random gaussian parameter
               :param low: the lowest value this random generator must provide
               :param high: the highest value this random generator must provide
               """
        GaussianDist.__init__(self, mu, sigma, low, high)
        RandomDist.__init__(self, "GaussianDiscrete")

    def random(self):
        return round(GaussianDist.random(self))


class CapacityLimit:
    """
    A base class for defining classes that has capacity
    like Floor, Lift, Room
    """

    def __init__(self, capacity=0):
        """
        determine the capacity in the initialization
        :param capacity: capacity limit of the class
        """
        self._capacity = capacity

    @property
    def capacity(self):
        return self._capacity


class Floor(CapacityLimit):
    """
    Floor is a base class for determining a hotel floor
    It is also inherited from the CapacityLimit
    """

    def __init__(self, capacity=0):
        CapacityLimit.__init__(self, capacity)


class HotelFloor(Floor):
    """
    HotelFloor is a class for determining a hotel floor
    """

    def __init__(self, floor_name: str, rooms_floor_count: dict, room_types: dict):
        """
        Initialize the hotel floor, you must define the floor name, floor rooms
        and room types.

        :param floor_name: name of the floor
        :param rooms_floor_count: To customize the floor the rooms_floor_count will be a dictionary
        containgin the numbe of rooms and their types
        :param room_types: dictionary of the room types detail
        """
        self._rooms = {}
        number = 1
        self._floor_name = floor_name

        capacity = 0
        # initialize room type
        for key in rooms_floor_count:
            self._rooms[key] = []
        # create the Room object
        for key in rooms_floor_count:
            for i in range(rooms_floor_count[key]):
                room = Room(str(floor_name) + str(number), room_types[key].name_type, room_types[key].capacity,
                            floor=self)
                self._rooms[key].append(room)
                capacity += room.capacity
                number += 1

        self._total_rooms = number
        self._lift_queue_up = []
        self._lift_queue_down = []

        Floor.__init__(self, capacity)

    @property
    def rooms(self) -> typing.List[Room]:
        """

        :return: list of rooms in the floor
        """
        return self._rooms

    @property
    def floor_name(self):
        return self._floor_name

    @property
    def lift_queue_up(self) -> typing.List[Attendance]:
        """

        :return: the queue of guests that calling the lift to go up
        """
        return self._lift_queue_up

    @property
    def lift_queue_down(self) -> typing.List[Attendance]:
        """

        :return: the queue of guests that calling the lift to go down
        """
        return self._lift_queue_down

    def __repr__(self):
        return "Floor: {}, Total Rooms: {}".format(self.floor_name, self._total_rooms)


class Room(RoomType):
    """
    Class of Room, inherited from the RoomType class
    will include the HotelFloor object
    """

    """
    def __init__(self,number: str,room_type: RoomType):
        self._room_type = room_type
        self._number = number

    @property
    def room_type(self):
        return self._room_type
    """

    def __init__(self, number: str, name: str, capacity: int, floor: HotelFloor):
        """
        Define the room number, room type name, capacity and designated floor
        :param number: room number
        :param name: room type name
        :param capacity: capacity of the Room
        :param floor: HotelFloor object where the room exists
        """
        RoomType.__init__(self, name, capacity)
        self._number = number
        self._occupied = False
        self._attendance = []
        self._floor = floor

    @property
    def floor(self):
        """

        :return: the designated floor
        """
        return self._floor

    @property
    def number(self):
        return self._number

    @property
    def occupied(self):
        return self._occupied

    """
    @occupied.setter
    def occupied(self,status:bool):
        self._occupied = status
    """

    @property
    def attendance(self):
        """

        :return: List of attendance that checked in to this room
        """
        return self._attendance

    @property
    def attendance_number(self):
        return len(self._attendance)

    @property
    def occupied_status(self):
        """

        :return: will return "occupied" if it is occupied or "empty" if it isn't
        """
        return "occupied" if self.occupied else "empty"

    def attendance_checkin(self, person: Person):
        """
        Method to add attendance to this room
        person will be added to the List of attendance
        :param person: Attendance
        :return: None
        """
        self.attendance.append(person)
        # There is a person checkin, set occupancy status of this room into True
        if self.attendance_number > 0:
            self._occupied = True

    def attendance_checkout(self, person: Person):
        """
        Method to checkout the Attendance
        List of attendance will be poped out
        :param person: Attendance
        :return: None
        """
        self.attendance.remove(person)
        # if attendance number is zero than the room is empty
        if self.attendance_number == 0:
            self._occupied = False

    def __repr__(self):
        return ("Room {}, Type: {}, Capacity: {}, Status: {}".format(self.number, self.name_type, self.capacity,
                                                                     self.occupied_status))


class Lift(CapacityLimit):
    """
    Lift class that describing the properties of lift and every method the lift has
    """
    _status_list = ["go_up", "go_down", "idle"]

    def __init__(self, name: str, random_generator: RandomMovementGenerator, average_speed: int = 1,
                 floor_configuration: dict = {}, capacity: int = 0, position: int = 0,
                 max_waiting_time: int = 10):
        """

        :param name:
        :param random_generator: we might not used this
        :param average_speed: this is not used
        :param floor_configuration: configuration of a floor in dictionary
        :param capacity: capacity of a lift
        :param position: position of the lift
        :param max_waiting_time: maximum waiting time for a door to close
        """
        CapacityLimit.__init__(self, capacity)
        self._name = name
        self._position = position
        self._graph = nx.DiGraph()
        self._attendance_number = 0
        self._max_waiting_time = max_waiting_time
        self._timer = 0
        self._attendance: typing.List[Attendance] = []

        # variables for moving act
        self._status = "idle"
        self._target = ""
        self._action = ""
        self._stop_floor = []
        self._call_floor = []
        self._call_imediate = ""
        self._next_move = "idle"
        self._door_open = False

        self._just_imediate = False

        # Random distribution for maximum waiting time
        # it should use skewed distribution
        # This will effect the lift door closing time
        self._random_gauss = GaussianDist(mu=self.max_waiting_time / 2, sigma=5, low=2, high=self.max_waiting_time)

        self._random_generator = random_generator

        if len(floor_configuration) > 0:
            # floor configuration is exist
            # we can make a fully customized lift graph
            logging.debug(floor_configuration)
            self._served_floor = floor_configuration["floor"]
            for i, x in enumerate(floor_configuration["floor"]):
                self.graph.add_node(x)
                if i > 0:
                    previous_floor = floor_configuration["floor"][i - 1]
                    speed = floor_configuration["speed"][i - 1]
                    self.graph.add_edge(previous_floor, x, attr={"speed": speed, "dir": "up"})
                    self.graph.add_edge(x, previous_floor, attr={"speed": speed, "dir": "down"})

    @property
    def max_waiting_time(self):
        return self._max_waiting_time

    @property
    def random_gauss(self) -> GaussianDist:
        return self._random_gauss

    def gen_close_door(self) -> int:
        """
        Generate close door for simulation
        :return: random gaussian of the closing door based on maximum waiting time
        """
        self._door_open = True
        return math.ceil(self._random_gauss.random())

    @property
    def waiting_time(self) -> int:
        return self._waiting_time

    @property
    def name(self) -> str:
        return self._name

    @property
    def position(self) -> int:
        return self._position

    @position.setter
    def position(self, position) -> int:
        self._position = position

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    @property
    def attendance(self) -> int:
        return self._attendance_number

    @property
    def served_floor(self) -> list:
        return self._served_floor

    @attendance.setter
    def attendance(self, new_att: int):
        """
        attendance_number setter
        if it greaters than the maximum capacity it will be rejected
        :param new_att: number of attendance to be added to the _attendance_number property
        :return: None
        """
        if new_att > self.capacity:
            raise Exception("Attendance reach it's maximum capacity: {}".format(self.capacity))
        if new_att < 0:
            raise Exception("Attendance can't be lower than zero: {}".format(new_att))
        """
        if self.attendance + new_att > self.capacity:
            throw Exception("Attendance reach it's maximum capacity: {}".format(self.capacity))
        """
        self._attendance_number = new_att

    def add_attendance(self, new_att: Attendance):
        """
        Method to add attendance object to the lift
        This will append the attendance to the _attendance list
        After it is added, the lift will be asked to stop to the attendance target floor
        :param new_att: Attendance object, that want to use the lift
        :return: None
        """
        self.attendance += new_att.capacity_unit
        self._attendance.append(new_att)
        new_att.position = "waiting_lift"
        self.goto(new_att._target_floor)

    def pop_attendance(self, drop_att: Attendance):
        """
        Method to remove the attendance from lift
        If the attendance arrived in the target floor
        :param drop_att: attendance to be dropped
        :return: None
        """
        self._attendance.remove(drop_att)
        self.attendance -= drop_att.capacity_unit

    def go_up(self):
        """
        Ask the lift to go_up
        :return: target floor
        """

        """
        edge = self.graph.edge[self.position]
        for target_node in edge:
            if edge[target_node]["attr"]["dir"] == "up":
                self.position = target_node
        return self.position
        """
        edge = self.graph.edge[self.position]
        for target_node in edge:
            # logging.debug("Target Node: {}".format(target_node))
            # logging.debug("Direction: {}".format(edge[target_node]["attr"]["dir"]))
            if edge[target_node]["attr"]["dir"] == "up":
                self._target = target_node
                self._timer += edge[target_node]["attr"]["speed"]
                # logging.debug("Target Node: {}".format(self._target))
                # logging.debug("Timer: {}".format(self._timer))
        return self._target

    def go_down(self):
        """
        Ask the lift to go down
        :return: target_floor
        """

        """
        edge = self.graph.edge[self.position]
        for target_node in edge:
            if edge[target_node]["attr"]["dir"] == "down":
                self.position = target_node
        return self.position
        """
        edge = self.graph.edge[self.position]
        for target_node in edge:
            if edge[target_node]["attr"]["dir"] == "down":
                self._target = target_node
                self._timer += edge[target_node]["attr"]["speed"]
        return self._target

    def call(self, floor, direction):
        """
        Lift is called to particular floor,
        append the floor to the stop list

        :param floor: from where
        :param direction: to where
        :return: None
        """

        if self._status == "idle" and self.attendance == 0 and not self._just_imediate:
            # check which direction the lift should move
            try:
                path = nx.shortest_path(self._graph, self._position, floor)

                self._status = self._graph.edge[path[0]][path[1]]["attr"]["dir"]

                self._call_imediate = floor
                self._next_move = direction

                if self._status == "up":
                    self.go_up()
                else:
                    self.go_down()
            except BaseException as ex:
                None
        else:
            if floor not in self._call_floor:
                #if self._call_imediate == "":
                #if self._status == direction and self._next_move == "":
                if self._status == direction and not self._just_imediate:
                    self._call_floor.append(floor)

            """
            if self._status == "up":
                self.go_up()
            else:
                self.go_down()
            """

    def goto(self, floor):
        """
        Same operation with call, just to make variance statement
        between calling and pushing the button inside lift

        :param floor: which floor the lift want to go to
        :return: None
        """

        if floor not in self._stop_floor:
            if self._status == "idle":
                # check which direction the lift should move
                path = nx.shortest_path(self._graph, self._position, floor)
                self._status = self._graph.edge[path[0]][path[1]]["attr"]["dir"]
            self._stop_floor.append(floor)

    def perform_move(self):
        """
        check the stop_floor, if the lift is called to stop at that floor,
        perform waiting time generator

        :return:
        """

        if self._timer == 0:
            # if there is no stop call

            if self._door_open:
                self._door_open = False
            else:
                if self._target != "" and not self._just_imediate:
                    self._position = self._target

                if len(self.graph.edge[self._position]) == 1:
                    if len(self._stop_floor) > 0:
                        if self._status == "down":
                            self._status = "up"
                        elif self._status == "up":
                            self._status = "down"


            if len(self._stop_floor) == 0 and len(self._call_floor) == 0 and self._call_imediate == "":
                self._status = "idle"
            elif self._call_imediate != "":
                if self._position == self._call_imediate:
                    self._call_imediate = ""
                    self._status = self._next_move
                    self._next_move = ""
                    self._timer += self.gen_close_door()
                    self._just_imediate = True

            if self._call_imediate == "" and not self._just_imediate:
                # reset the lift call if this is the last floor
                if len(self._stop_floor) == 0:
                    self._call_floor.clear()
                    self._status = "idle"
            else:
                if len(self._stop_floor) == 0:
                    self._call_floor.clear()
                self._just_imediate = False


            if self._position in self._stop_floor:
                # remove the position from the stop floor
                # print("position: {}".format(self._position))
                self._stop_floor.remove(self._position)
                if self._position in self._call_floor:
                    self._call_floor.remove(self._position)
                # perform additional waiting time
                self._timer += self.gen_close_door()

                # logging.debug("Lift {} arrive on {}, closing door in {}".format(self.name,self.position,self._timer))
            if self._position in self._call_floor:
                self._call_floor.remove(self._position)
                if self.attendance < self.capacity:
                    self._timer += self.gen_close_door()
                    # logging.debug("Lift {} arrive on {}, closing door in {}".format(self.name,self.position,self._timer))

                    # if self._status != "idle":
                    # logging.debug("Position Move {} Target {}".format(self.position,self._target))
                    #    self._position = self._target
                    # logging.debug("Position Move {}".format(self.position))


            """
            move the lift
            """
            if self._status == "up":
                self.go_up()
            elif self._status == "down":
                self.go_down()

        if self._timer > 0:
            if self._door_open:
                logging.debug("Lift {} arrive on {}, closing door in {}".format(self.name, self.position, self._timer))
                # pick up attendance
            else:
                logging.debug("Lift {} go {} from {} to {} arrive in {}".format(self.name, self._status, self._position,
                                                                                self._target, self._timer))
            self._timer -= 1

        logging.debug("Stop Floor: {}".format(self._stop_floor))
        logging.debug("Call Floor: {}".format(self._call_floor))
        logging.debug("Call Immediate: {}".format(self._call_imediate))


    def __repr__(self):
        # print(self.served_floor)
        return "Lift {}, capacity: {}, attendance: {}, position: {}, imm: {}, next_move: {}, serve: {}".format(self.name, self.capacity,
                                                                                       self.attendance, self.position,
                                                                                        self._call_imediate, self._next_move,
                                                                                       ",".join([str(x) for x in
                                                                                                 self.served_floor]))


class HotelLift():
    """
    HotelLift
    is a class that combining the HotelFloor and the Lift, it also can be called as a simple hotel class
    """

    def __init__(self, number_of_floor: int, number_of_lift: int, rooms_floor_count, room_types: dict,
                 random_generator: RandomMovementGenerator):
        """
        give number of floor, room_types, and rooms_floor_count configuration
        The class will generate all the Object needed based on configuration

        :param number_of_floor: number of floor
        :param number_of_lift: number of lift
        :param rooms_floor_count: configuration for rooms in a floor
        :param room_types: configuration of room types
        :param random_generator: might not be used
        """
        self._floors = []
        self._rooms = []
        self._total_capacity = 0
        for x in range(number_of_floor):
            floor = HotelFloor(x, rooms_floor_count, room_types)
            self._total_capacity += floor.capacity
            self._floors.append(floor)
            # print(floor.rooms)
            for rooms in floor.rooms.values():
                # print(rooms)
                self._rooms.extend(rooms)

        self._lifts = {}
        for x in lift_floor_configuration:
            # logging.debug(x)
            config = lift_floor_configuration[x]
            self.lifts[x] = Lift(name=x, floor_configuration=config, capacity=20, position=0,
                                 random_generator=random_generator)

        """
        for x in range(number_of_lift):
            lift = Lift(x,20,0)
            for y in range(number_of_floor):
                lift.graph.add_node(y)
                if y > 0:
                    lift.graph.add_edge(y-1,y)
                    lift.graph.add_edge(y,y-1)

            self._lifts.append(lift)     
        """

    @property
    def lifts(self) -> typing.Dict[str, Lift]:
        return self._lifts

    @property
    def floors(self) -> typing.List[HotelFloor]:
        return self._floors

    @property
    def rooms(self):
        return self._rooms

    @property
    def total_capacity(self):
        return self._total_capacity

    def drop_pick_up_attendance(self):
        """
        Method to drop or pick up attendance

        :return: None
        """

        for floor in self.floors:
            logging.debug("Floor: {}".format(floor.floor_name))
            logging.debug("Queue down: {}".format(len(floor.lift_queue_down)))
            logging.debug("Queue up: {}".format(len(floor.lift_queue_up)))

        for lift in self.lifts.values():
            logging.debug("Drop Pick Up: {}, status: {}".format(lift, lift._status))
            logging.debug(
                "Lift: {}, attendance floor: {}".format(lift.name, [x._target_floor for x in lift._attendance]))
            # drop people that come out
            copy_attendance = lift._attendance.copy()
            for attend in copy_attendance:
                if attend._target_floor == lift._position:
                    lift.pop_attendance(attend)
                    # attend._target_floor = ""
                    # attend._from_floor = ""
                    attend.position = attend._moving_path[0]

            if lift._door_open:
                # check people that come in
                if lift._status == "down":
                    lift_queue = self.floors[lift._position].lift_queue_down
                    # while lift.attendance < lift.capacity or len(lift_queue)>0 :
                    for attend in lift_queue:
                        if lift.attendance == lift.capacity:
                            # if total attendance equal with capacity
                            # then the lift must not accepting any more attendance
                            break
                        if attend._target_floor in lift.served_floor:
                            if attend.capacity_unit + lift.attendance <= lift.capacity:
                                lift.add_attendance(attend)
                                attend.position = "waiting_lift"
                                lift_queue.remove(attend)
                elif lift._status == "up":
                    lift_queue = self.floors[lift._position].lift_queue_up
                    # while lift.attendance < lift.capacity or len(lift_queue)>0 :
                    for attend in lift_queue:
                        if lift.attendance == lift.capacity:
                            # if total attendance equal with capacity
                            # then the lift must not accepting any more attendance
                            break
                        if attend._target_floor in lift.served_floor:
                            if attend.capacity_unit + lift.attendance <= lift.capacity:
                                lift.add_attendance(attend)
                                attend.position = "waiting_lift"
                                lift_queue.remove(attend)

    def __repr__(self):
        output = ""
        for x in self.lifts.values():
            output += x.__repr__() + "\n"
        return output


class HotelLiftQueue():
    """
    Helper class for a lift queue
    """

    def __init__(self, hotel_lift: HotelLift):
        """
        give the HotelLift object

        :param hotel_lift: HotelLift Object
        """
        self._hotel_lift = hotel_lift
        self._hotel_floor = hotel_lift.floors

    @property
    def hotel_lift(self) -> HotelLift:
        return self._hotel_lift

    def call_lift(self, att: Attendance, floor: str, target: str):
        """
        The function will activate the lift by calling it
        and append the floor to the called_stack lift

        :param att: Attendance for the floor lift stack
        :param floor: from where this lift called
        :param target: to where the person want to go to
        :return:
        """
        # if att not in self._hotel_floor[int(floor)].lift_queue:
        #    self._hotel_floor[int(floor)].lift_queue.append(att)
        # initialize lift_path to check the shortest lift_path
        lift_path = [x for x in range(len(self.hotel_lift.floors) * 2)]
        lift_call = None
        direction = None

        for lift in self.hotel_lift.lifts.values():
            try:
                path = nx.shortest_path(lift._graph, floor, target)
                direction = lift._graph.edge[path[0]][path[1]]["attr"]["dir"]
                # check the shortest path for the lift
                lift_to_pos = nx.shortest_path(lift._graph, lift._position, floor)
                lift_to_pos_dir = lift._graph.edge[lift_to_pos[0]][lift_to_pos[1]]["attr"]["dir"]
                if lift._status == "idle":
                    if len(lift_path) > len(lift_to_pos_dir):
                        lift_path = lift_to_pos_dir
                        lift_call = lift
                elif lift_to_pos_dir == lift._status and lift._door_open:
                    if len(lift_path) > len(lift_to_pos_dir):
                        lift_path = lift_to_pos_dir
                        lift_call = lift
                if lift_call != None:
                    lift.call(floor, direction)
            except BaseException as ex:
                path = []

        if direction == "up":
            if att not in self.hotel_lift.floors[floor].lift_queue_up:
                self.hotel_lift.floors[floor].lift_queue_up.append(att)
        elif direction == "down":
            if att not in self.hotel_lift.floors[floor].lift_queue_down:
                self.hotel_lift.floors[floor].lift_queue_down.append(att)

        return (lift_call, lift_path, direction)
        """
        for lift in self._hotel_lift.lifts.values():
            if lift._status == "idle":
        """

    def call_lift_priority(self, att: Attendance, floor: str, target: str):
        """
        Call the lift using the priority queue in each floor
        :param att:
        :param floor:
        :param target:
        :return:
        """
        lift_path = [x for x in range(len(self.hotel_lift.floors) * 2)]
        lift_call = None
        direction = None

        for lift in self.hotel_lift.lifts.values():
            try:
                path = nx.shortest_path(lift._graph, floor, target)
                direction = lift._graph.edge[path[0]][path[1]]["attr"]["dir"]
                break;
            except BaseException as ex:
                path = []

        # add the attendance to the lift queue
        if direction == "up":
            if att not in self.hotel_lift.floors[floor].lift_queue_up:
                self.hotel_lift.floors[floor].lift_queue_up.append(att)
        elif direction == "down":
            if att not in self.hotel_lift.floors[floor].lift_queue_down:
                self.hotel_lift.floors[floor].lift_queue_down.append(att)

    def move_immediate(self):
        # check the busiest floor
        # busy_up = None
        # busy_down = None

        # len_busy_up = 0
        # len_busy_down = 0

        # make a list of tuple queue
        busy_queue_up = []
        busy_queue_down = []

        for floor in self.hotel_lift.floors:
            busy_queue_up.append((floor, len(floor.lift_queue_up)))
            busy_queue_down.append((floor, len(floor.lift_queue_down)))
            """
            if len(floor.lift_queue_up) > len_busy_up:
                len_busy_up = len(floor.lift_queue_up)
                busy_up = floor
            if len(floor.lift_queue_down) > len_busy_down:
                len_busy_down = len(floor.lift_queue_down)
                busy_down = floor
            """

        # sort the busy queue based on the attendance
        busy_queue_up = sorted(busy_queue_up, key=lambda x: x[1])[::-1]
        busy_queue_down = sorted(busy_queue_down, key=lambda x: x[1])[::-1]

        print("busy_queue_up: {}".format(busy_queue_up))
        print("busy_queue_down: {}".format(busy_queue_down))

        for queue_tuple in busy_queue_up:
            if queue_tuple[1] > 0:
                floor = queue_tuple[0]
                lift_path_up = [x for x in range(len(self.hotel_lift.floors) * 2)]
                # lift_path_down = [x for x in range(len(self.hotel_lift.floors) * 2)]
                direction = None
                lift_call_up = None
                # lift_call_down = None
                for lift in self.hotel_lift.lifts.values():
                    try:
                        lift_to_pos = nx.shortest_path(lift._graph, lift._position, floor.floor_name)
                        # print(lift_to_pos)
                        if len(lift_to_pos) > 1:
                            lift_to_pos_up = lift._graph.edge[lift_to_pos[0]][lift_to_pos[1]]["attr"]["dir"]
                        else:
                            if lift.attendance < lift.capacity and lift._just_imediate:
                                lift_call_up = lift
                        """
                        else:
                            # immediate open
                            if not lift._door_open and lift.attendance < lift.capacity:
                                lift._timer+=lift.gen_close_door()
                                lift._status = "up"
                                break
                        """

                        """
                        if busy_down!=None:
                            lift_to_pos = nx.shortest_path(lift._graph, lift._position, busy_down.floor_name)
                            #if len(lift_to_pos) > 1:
                            lift_to_pos_down = lift._graph.edge[lift_to_pos[0]][lift_to_pos[1]]["attr"]["dir"]
                        """

                        if lift._status == "idle":
                            if len(lift_path_up) > len(lift_to_pos):
                                lift_path_up = lift_to_pos
                                lift_call_up = lift
                        elif "up" == lift._status and lift_to_pos_up == lift._status:
                            if len(lift_path_up) > len(lift_to_pos):
                                lift_path_up = lift_to_pos
                                lift_call_up = lift

                        """
                        if busy_down!=None:
                            if lift._status == "idle":
                                if len(lift_path_down) > len(lift_to_pos_down):
                                    lift_path_down = lift_to_pos_down
                                    lift_call_down = lift
                            elif lift_to_pos_down == lift._status:
                                if len(lift_path_down) > len(lift_to_pos_down):
                                    lift_path_down = lift_to_pos_down
                                    lift_call_down = lift
                        """
                    except BaseException as ex:
                        # print(ex)
                        pass

                #print("lift to pos up: {}".format(lift_to_pos_up))
                #print("lift._status: {}".format(lift._status))

                # print(lift_call_up)
                if lift_call_up != None:
                    lift_call_up.call(floor.floor_name, "up")

        for queue_tuple in busy_queue_down:
            if queue_tuple[1] > 0 :
                floor = queue_tuple[0]
                lift_path_up = [x for x in range(len(self.hotel_lift.floors) * 2)]
                # lift_path_down = [x for x in range(len(self.hotel_lift.floors) * 2)]
                direction = None
                lift_call_up = None
                # lift_call_down = None
                for lift in self.hotel_lift.lifts.values():
                    try:
                        lift_to_pos = nx.shortest_path(lift._graph, lift._position, floor.floor_name)
                        # print(lift_to_pos)
                        if len(lift_to_pos) > 1:
                            lift_to_pos_up = lift._graph.edge[lift_to_pos[0]][lift_to_pos[1]]["attr"]["dir"]
                        else:
                            if lift.attendance < lift.capacity and lift._just_imediate:
                                lift_call_up = lift
                        """
                        else:
                            if not lift._door_open and lift.attendance < lift.capacity:
                                lift._timer+=lift.gen_close_door()
                                lift._status = "down"
                                break
                        """

                        """
                        if busy_down!=None:
                            lift_to_pos = nx.shortest_path(lift._graph, lift._position, busy_down.floor_name)
                            #if len(lift_to_pos) > 1:
                            lift_to_pos_down = lift._graph.edge[lift_to_pos[0]][lift_to_pos[1]]["attr"]["dir"]
                        """

                        if lift._status == "idle":
                            if len(lift_path_up) > len(lift_to_pos):
                                lift_path_up = lift_to_pos
                                lift_call_up = lift
                        elif "down" == lift._status and lift_to_pos_up == lift._status:
                            if len(lift_path_up) > len(lift_to_pos):
                                lift_path_up = lift_to_pos
                                lift_call_up = lift

                        """
                        if busy_down!=None:
                            if lift._status == "idle":
                                if len(lift_path_down) > len(lift_to_pos_down):
                                    lift_path_down = lift_to_pos_down
                                    lift_call_down = lift
                            elif lift_to_pos_down == lift._status:
                                if len(lift_path_down) > len(lift_to_pos_down):
                                    lift_path_down = lift_to_pos_down
                                    lift_call_down = lift
                        """
                    except BaseException as ex:
                        # print(ex)
                        pass

                #print("lift to pos down: {}".format(lift_to_pos_up))
                #print("lift._status: {}".format(lift._status))

                # print(lift_call_up)
                if lift_call_up != None:
                    lift_call_up.call(floor.floor_name, "down")


class Person():
    """
    Base class for the Attendance
    """

    def __init__(self, name: str, move_time: int, outside_time: int, random_generator: RandomMovementGenerator,
                 schedule={}, capacity_unit=1):
        """
        Define the attendance name and capacity unit of attendance
        Different person might have different capacity unit to further
        realize the different capacity scenario

        :param name:
        :param move_time: might not be used
        :param outside_time: might not be used
        :param random_generator: might not be used
        :param schedule: might not be used
        :param capacity_unit:
        """
        self._name = name
        self._capacity_unit = capacity_unit

    @property
    def capacity_unit(self):
        return self._capacity_unit

    @property
    def name(self):
        return self._name


class Attendance(Person):
    """
    Attendance of the hotel
    This class will have all methods that can be performed for one attendance
    """
    _target_dest = ["room", "outside", "conference", "dining"]
    _status = ["idle", "go_lift", "waiting_lift", "in_lift", "on_move"]

    # destination floor contains dictionary that refer to designated floor
    _dest_floor = {
        "outside": 0,
        "conference": 1,
        "dining": 2
    }

    # Create a DAG for moving behaviour

    _nodes = ["room", "waiting_lift", "in_lift", "outside"]

    _move_graph = nx.DiGraph()
    for node in _nodes:
        _move_graph.add_node(node)

    # _move_graph.add_edge("room","go_lift")
    # _move_graph.add_edge("go_lift","waiting_lift")
    _move_graph.add_edge("room", "waiting_lift")
    _move_graph.add_edge("waiting_lift", "in_lift")
    _move_graph.add_edge("in_lift", "outside")
    # _move_graph.add_edge("outside","go_lift")
    _move_graph.add_edge("outside", "waiting_lift")
    _move_graph.add_edge("in_lift", "room")

    # move graph for dining
    _move_graph.add_edge("dining", "waiting_lift")
    _move_graph.add_edge("in_lift", "dining")

    # move graph for conference
    _move_graph.add_edge("conference", "waiting_lift")
    _move_graph.add_edge("in_lift", "conference")

    def __init__(self, room: Room, name: str, move_time: int, outside_time: int,
                 random_generator: RandomMovementGenerator, lift_queue: HotelLiftQueue, schedule: list = [],
                 capacity_unit: int = 1):
        """

        :param room: room object the attendance assigned for
        :param name: attendance name
        :param move_time: attendance moving time
        :param outside_time: attendance outside time
        :param random_generator: might not be used
        :param lift_queue: if the attendance assigned in one lift queue
        :param schedule: schedule of the attendance
        :param capacity_unit: capacity unit of an attendance, higher capacity unit will reflect on
        how the attendance occupied the lift
        """
        Person.__init__(self, name, move_time=move_time, outside_time=outside_time, capacity_unit=capacity_unit,
                        schedule=schedule, random_generator=random_generator)
        self._room = room
        self._lift_queue = lift_queue

        self._schedule = schedule
        self._schedule_queue = schedule.copy()
        # print(self._schedule_queue)

        self._move_time = move_time
        self._outside_time = outside_time
        self._random_move_time = GaussianDist(mu=move_time, sigma=move_time / 2, low=0, high=move_time * 2)
        self._random_outside_time = GaussianDist(mu=outside_time, sigma=outside_time / 2, low=0, high=outside_time * 2)
        self._next_move = 0
        self._random_generator = random_generator
        self._waiting_lift_time = 0
        self._in_lift_time = 0

        """
        status for a person is

        """
        self._status = "idle"
        self._position = "outside"
        self._target = ""
        self._from_floor = ""
        self._target_floor = ""
        self._action = ""
        self._moving_path = []

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, room: Room):
        self._room = room

    def call_lift(self):
        lift_queue.call_lift_priority(self._position, self._target)

    def go_lift(self):
        lift_queue.go_lift(self._target)

    @property
    def move_time(self):
        return self._move_time

    @property
    def next_move_schedule(self):
        return self._next_move

    @property
    def status(self):
        return self._status

    def perform_move(self):
        """
        This function will be a counter time for moving
        every time this function called, moving time will be reduced
        and if it's reach zero it will perform the moving
        action

        :return:
        """

        # logging.debug(self._moving_path)

        # logging.debug(self.position)

        if len(self._moving_path) == 0:
            self.generate_next_move()

        # print(self._position)
        # print(self._target)
        # print(self._moving_path)

        if len(self._moving_path) > 0:
            if self._next_move == 0 and self._moving_path[0] == self._position:
                # pop the value
                # logging.debug("Position Now: {}".format(self._position))
                popped = self._moving_path.pop(0)
                # logging.debug("person {}, pop path {}".format(self._name, popped))
                self._action = self._moving_path[0]

            if self._action == self._target:
                self._position = self._moving_path.pop(0)
                total_time = self._waiting_lift_time + self._in_lift_time
                with open("result.txt", "a") as file:
                    file.write(",".join([str(x) for x in
                                         [self.name, self._from_floor, self._target_floor, self._waiting_lift_time,
                                          self._in_lift_time, total_time]]) + "\n")

                self._target_floor = ""
                self._from_floor = ""
                self._waiting_lift_time = 0
                self._in_lift_time = 0

            if self._action == "waiting_lift":
                """
                call the lift
                """

                """
                if self._position == "room":
                    from_where = self._room.floor.floor_name
                elif self._position == "outside":
                    from_where = 0
    
                if self._target == "room":
                    to_where = self._room.floor.floor_name
                elif self._target == "outside":
                    to_where = 0
                """
                from_where = self.transform_place(self._position)
                to_where = self.transform_place(self._target)

                self._from_floor = from_where
                self._target_floor = to_where

                if from_where != to_where:
                    # call lift only if the attendance go to another floor
                    # logging.debug("Person {}, from {} to {}".format(self._name,self._position,to_where))
                    # lift, path, direction = self._lift_queue.call_lift_priority(self, from_where, to_where)
                    # logging.debug("Person {}, call lift {}, path: {}".format(self._name, lift, path))

                    self._lift_queue.call_lift_priority(self, from_where, to_where)

                    """
                    if direction == "up":
                        if self not in self._lift_queue.hotel_lift.floors[from_where].lift_queue_up:
                            self._lift_queue.hotel_lift.floors[from_where].lift_queue_up.append(self)
                    elif direction == "down":
                        if self not in self._lift_queue.hotel_lift.floors[from_where].lift_queue_down:
                            self._lift_queue.hotel_lift.floors[from_where].lift_queue_down.append(self)
                    """
                self._waiting_lift_time += 1

                """
                # check if there is a lift available for the attendance
                for lift in self._lift_queue.hotel_lift.lifts.values():
                    if lift.position == from_where:
                        if lift._status == direction:
                            # if the direction is the same
                            lift.add_attendance()
                """

            if self._action == "in_lift":
                self._in_lift_time += 1

            if self._next_move > 0:
                self._next_move -= 1
                # logging.debug(
                #    "Person {}, move from {} to {} in {}".format(self._name, self._position, self._target, self._next_move))

    @property
    def target(self):
        return self._target

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos: str):
        self._position = pos

    @property
    def action(self):
        return self._action

    def transform_place(self, place):
        if place in self._dest_floor.keys():
            return self._dest_floor[place]
        elif place == "room":
            return self._room.floor.floor_name
        elif place == "random":
            floor = np.random.randint(len(self._lift_queue.hotel_lift.floors), size=1)
            return self._lift_queue.hotel_lift.floors[floor].floor_name

        return None

    def generate_next_move(self):
        """
        Method to generate next move for the attendance
        might include the move that are assigned in the schedule
        :return:
        """
        # print(self._schedule_queue)
        if len(self._schedule) > 0:
            if len(self._schedule_queue) > 1:
                action_now = self._schedule_queue.pop(0)
                # print(action_now)
                self._position = action_now[0]
                # only if the schedule has next move
                self._next_move = GaussianDiscrete(mu=action_now[1], sigma=2 / 3 * action_now[1], low=0,
                                                   high=2 * action_now[1]).random()
                # next position
                self._target = self._schedule_queue[0][0]

                self._moving_path = nx.shortest_path(self._move_graph, self._position, self._target)

            else:
                self._target = ""
        else:
            if self._position == "room":
                self._next_move = round(self._random_move_time.random())
                # self._next_move = self._random_generator.random_move_time()
                self._target = "outside"
            else:
                self._next_move = round(self._random_outside_time.random())
                # self._next_move = self._random_generator.random_outside_time()
                self._target = "room"

            self._moving_path = nx.shortest_path(self._move_graph, self._position, self._target)

    def set_schedule(self, schedule):
        """
        Method to set the schedule of an attendance

        :return: None
        """
        self._schedule = schedule
        self._schedule_queue = schedule.copy()

    def __repr__(self):
        return "name: {}, room: {}".format(self.name, self.room)


class InitialGenerator():
    """
    InitialGenerator is a class to generate random attendance
    """

    def __init__(self, room_stack: list, room_occupancy_pctg: float, move_time: int, outside_time: int,
                 random_generator: RandomMovementGenerator, lift_queue: HotelLiftQueue, schedule=[]):
        # sample room_stack based on occupancy percentage
        total_rooms = len(room_stack)
        occupied_index = np.random.randint(total_rooms, size=np.int(room_occupancy_pctg * total_rooms))
        self._room_stack = room_stack
        logging.debug(occupied_index)
        # occupied = [room_stack[x] for x in occupied_index]
        self._attendance: typing.List[Attendance] = []
        number = 0
        for i in occupied_index:
            room = room_stack[i]
            # room.occupied = True
            # for every room occupied, create attendance person based on the capacity
            number_of_attendance = np.random.randint(room.capacity) + 1
            # print(room)

            # default move, people just going back and forth within room and outside
            for j in range(number_of_attendance):
                # create new attendance
                new_att = Attendance(room, number, move_time=move_time, outside_time=outside_time,
                                     random_generator=random_generator, lift_queue=lift_queue)
                new_att.position = "room"
                room.attendance_checkin(new_att)
                self._attendance.append(new_att)
                number += 1

        # custom schedule
        if len(schedule) > 0:
            # shufle the attendance
            random.shuffle(self._attendance)
            attendance_number = len(self._attendance)

            # print(schedule)

            for x in schedule:
                # print(x)
                number = math.ceil(x[1] * attendance_number)
                # print(number)
                number = number if (attendance_number - number > 0) else attendance_number
                for i in range(number):
                    self._attendance[attendance_number - 1 - i].set_schedule(x[0])
                attendance_number -= number

    @property
    def attendance(self):
        return self._attendance

    @property
    def room_stack(self):
        return self._room_stack

    @property
    def number_of_attendance(self):
        return len(self._attendance)


class SimulationHelper():
    """
    SimulationHelper is a class that run the simulation in a Thread
    """

    def __init__(self, attendance: list, hotel_lift: HotelLift, lift_queue: HotelLiftQueue, interval: float = 1):
        self._attendance = attendance
        self._hotel_lift = hotel_lift
        self._lifts = hotel_lift.lifts
        self._status = "stop"
        self._interval = interval
        self._lift_queue = lift_queue

        # self._timer = threading.Timer(self._interval,self.run_simulation)
        # self._thread = threading.Thread(name="move_timer")
        # self._thread = threading.Thread(name='my_service', target=self.run_simulation)

    def on_press(self, key):
        try:
            print('alphanumeric key {0} pressed'.format(
                key.char))
        except AttributeError:
            print('special key {0} pressed'.format(
                key))

    def on_release(self, key):
        print('{0} released'.format(
            key))
        if key == keyboard.Key.cmd:
            if self._status == "start":
                self.stop()
                #                self._timer.cancel()
            else:
                if not self._thread.is_alive():
                    #                    self._timer = threading.Timer(self._interval,self.run_simulation)
                    self.start()
                    # self._timer.start()
                    # if key == keyboard.Key.esc:
                    # Stop listener
                    #    return False

    def simulate_timer(self):
        # move all the object
        # logging.debug(self._attendance)

        for attendance in self._attendance:
            attendance.perform_move()

        self._hotel_lift.drop_pick_up_attendance()

        for lift in self._lifts.values():
            lift.perform_move()

        self._lift_queue.move_immediate()

    def run_simulation(self):
        while self._status == "start":
            # print(self._status)
            self.simulate_timer()
            time.sleep(self._interval)
        # print(self._status)

        """
        print(self._status)
        if self._status == "start":
            self.simulate_timer()
        else:
            None
        """

    def run(self, duration=3600):
        # Collect events until released
        self.start()
        # self._thread.start()

        with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()
            # check stop signal

            # self._thread.join()

    def start(self):
        self._status = "start"
        self._thread = threading.Thread(name='my_service', target=self.run_simulation)
        self._thread.start()
        # run the timer again
        """
        if not self._timer.is_alive():
            self._timer.start()
        """
        # print(self._status)

    def stop(self):
        self._status = "stop"
        # self._thread.name.exit()
        print(self._status)


# configuration
number_of_floor = 20

custom_floor = [0, 10]
custom_floor.extend(range(11, number_of_floor))
custom_speed = [10]
custom_speed.extend([1 for x in range(10, number_of_floor - 1)])

lift_floor_configuration = {
    # speed 1 for every floor
    0: {"floor": range(0, number_of_floor), "speed": [1 for x in range(number_of_floor - 1)]},
    1: {"floor": range(0, number_of_floor), "speed": [1 for x in range(number_of_floor - 1)]},
    2: {"floor": range(0, int(number_of_floor / 2)), "speed": [1 for x in range(0, int(number_of_floor / 2) - 1)]},
    3: {"floor": range(0, int(number_of_floor / 2)), "speed": [1 for x in range(0, int(number_of_floor / 2) - 1)]},
    4: {"floor": custom_floor, "speed": custom_speed},
    5: {"floor": custom_floor, "speed": custom_speed}
}

room_types_list = ["single", "double", "deluxe"]

room_types = {
    "single": RoomType("single", 2),
    "double": RoomType("double", 2),
    "deluxe": RoomType("deluxe", 4),
}

rooms_floor_count = {
    "single": 20,
    "double": 20,
    "deluxe": 10
}

# the schedule configuration for each person
# a list of tuple contains from position and waiting time until next move in seconds
schedule_1 = [("room", 14400), ("outside", 10800), ("dining", 3600), ("room", 0)]
schedule_2 = [("outside", 3600), ("dining", 3600), ("room", 0)]
schedule_3 = [("room", 3600), ("dining", 1800), ("conference", 3600), ("room", 0)]

normal_schedule_list = [(schedule_1, 0.5), (schedule_2, 0.3), (schedule_3, 0.2)]

# evacuation schedule
evac_schedule = [([("room", 5), ("outside", 0)], 1)]

# registration_schedule
batch_registration_schedule = [([("outside", 1800), ("room", 0)], 1)]

# HotelFloor(rooms_floor_count,room_types)
random_generator = RandomMovementGenerator(person={"move_time": 14400, "outside_time": 3600},
                                           lift={"max_waiting_time": 10, "sigma": 5})

hotel = HotelLift(20, 4, rooms_floor_count, room_types, random_generator=random_generator)
# print(hotel)
len(hotel.rooms)

lift_queue = HotelLiftQueue(hotel_lift=hotel)
simulate = InitialGenerator(room_stack=hotel.rooms, room_occupancy_pctg=0.8, move_time=200, outside_time=100,
                            random_generator=random_generator, lift_queue=lift_queue, schedule=normal_schedule_list)

helper = SimulationHelper(attendance=simulate.attendance, hotel_lift=hotel, lift_queue=lift_queue, interval=0.1)

helper.run()
