import numpy as np
import networkx as nx
import logging
import random
import math
from pynput import keyboard
import threading
import time

logging.getLogger().setLevel(logging.DEBUG)
logging.debug("TEST")

# make a rules using graph network
lift_number = 4
number_of_floor = 20
conference_room_floor = 2


# define the class person
# implementation later
class Person:
    pass


class Attendance:
    pass


class RandomMovementGenerator():
    """
    initiate random movement for target object
    since generating random in the object will
    result in the same value (same seed)
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
        return math.ceil(self._random_close_door.random())


class RoomType:
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
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def random(self):
        None


class GaussianDist(RandomDist):
    def __init__(self, mu: float, sigma: float, low: float, high: float):
        RandomDist.__init__(self, "Gaussian")
        self._mu = mu
        self._sigma = sigma
        self._low = low
        self._high = high

    def random(self):
        x = self._low - 1
        while x < self._low or x > self._high:
            x = random.gauss(self._mu, self._sigma)
        return x


class GaussianDiscrete(RandomDist):
    def __init__(self, mu: float, sigma: float, low: float, high: float):
        RandomDist.__init__(self, "GaussianDiscrete")
        self._mu = mu
        self._sigma = sigma
        self._low = low
        self._high = high

    def random(self):
        x = self._low - 1
        while x < self._low or x > self._high:
            x = round(random.gauss(self._mu, self._sigma))
        return x


class CapacityLimit:
    def __init__(self, capacity=0):
        self._capacity = capacity

    @property
    def capacity(self):
        return self._capacity


class Floor(CapacityLimit):
    def __init__(self, capacity=0):
        CapacityLimit.__init__(self, capacity)


class HotelFloor(Floor):
    def __init__(self, floor_name: str, rooms_floor_count: dict, room_types: dict):
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
        self._lift_queue = []

        Floor.__init__(self, capacity)

    @property
    def rooms(self):
        return self._rooms

    @property
    def floor_name(self):
        return self._floor_name

    @property
    def lift_queue(self):
        return self._lift_queue

    def __repr__(self):
        return "Floor: {}, Total Rooms: {}".format(self.floor_name, self._total_rooms)


class Room(RoomType):
    """
    def __init__(self,number: str,room_type: RoomType):
        self._room_type = room_type
        self._number = number

    @property
    def room_type(self):
        return self._room_type
    """

    def __init__(self, number: str, name: str, capacity: int, floor: HotelFloor):
        RoomType.__init__(self, name, capacity)
        self._number = number
        self._occupied = False
        self._attendance = []
        self._floor = floor

    @property
    def floor(self):
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
        return self._attendance

    @property
    def attendance_number(self):
        return len(self._attendance)

    @property
    def occupied_status(self):
        return "occupied" if self.occupied else "empty"

    def attendance_checkin(self, person: Person):
        self.attendance.append(person)
        # There is a person checkin, set occupancy status of this room into True
        if self.attendance_number > 0:
            self._occupied = True

    def attendance_checkout(self, person: Person):
        self.attendance.remove(person)
        # if attendance number is zero than the room is empty
        if self.attendance_number == 0:
            self._occupied = False

    def __repr__(self):
        return ("Room {}, Type: {}, Capacity: {}, Status: {}".format(self.number, self.name_type, self.capacity,
                                                                     self.occupied_status))


class Lift(CapacityLimit):
    _status_list = ["go_up", "go_down", "idle"]

    def __init__(self, name: str, random_generator: RandomMovementGenerator, average_speed: int = 1,
                 floor_configuration: dict = {}, capacity: int = 0, position: int = 0,
                 max_waiting_time: int = 10):
        CapacityLimit.__init__(self, capacity)
        self._name = name
        self._position = position
        self._graph = nx.DiGraph()
        self._attendance = 0
        self._max_waiting_time = 10
        self._timer = 0

        # variables for moving act
        self._status = "idle"
        self._target = ""
        self._action = ""
        self._stop_floor = []
        self._call_floor = []

        # Random distribution for maximum waiting time
        # it should use skewed distribution
        # This will effect the lift door closing time

        self._random_gauss = GaussianDist(mu=self.max_waiting_time / 2, sigma=5, low=1, high=self.max_waiting_time)

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
        """
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
        return self._attendance

    @property
    def served_floor(self) -> list:
        return self._served_floor

    @attendance.setter
    def attendance(self, new_att: int):
        if new_att > self.capacity:
            raise Exception("Attendance reach it's maximum capacity: {}".format(self.capacity))
        if new_att < 0:
            raise Exception("Attendance can't be lower than zero: {}".format(new_att))
        """
        if self.attendance + new_att > self.capacity:
            throw Exception("Attendance reach it's maximum capacity: {}".format(self.capacity))
        """
        self._attendance = new_att

    def add_attendance(self, new_att: int):
        self.attendance += new_att

    def pop_attendance(self, drop_att: int):
        self.attendance -= drop_att

    def go_up(self):
        """
        edge = self.graph.edge[self.position]
        for target_node in edge:
            if edge[target_node]["attr"]["dir"] == "up":
                self.position = target_node
        return self.position
        """
        edge = self.graph.edge[self.position]
        for target_node in edge:
            logging.debug("Target Node: {}".format(target_node))
            logging.debug("Direction: {}".format(edge[target_node]["attr"]["dir"]))
            if edge[target_node]["attr"]["dir"] == "up":
                self._target = target_node
                self._timer += edge[target_node]["attr"]["speed"]
            logging.debug("Target Node: {}".format(self._target))
            logging.debug("Timer: {}".format(self._timer))
        return self._target

    def go_down(self):
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

    def call(self, floor):
        """
        Lift is called to particular floor,
        append the floor to the stop list
        """
        if floor not in self._call_floor:
            if self._status == "idle":
                # check which direction the lift should move
                path = nx.shortest_path(self._graph, self._position, floor)
                self._status = self._graph.edge[path[0]][path[1]]["attr"]["dir"]

            if self._status == "up":
                self.go_up()
            else:
                self.go_down()

            self._call_floor.append(floor)

    def goto(self, floor):
        """
        Same operation with call, just to make variance statement
        between calling and pushing the button inside lift
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
        """
        if self._timer == 0:
            # if there is no stop call
            if len(self._stop_floor) and len(self._call_floor) == 0:
                self._status = "idle"
            elif self._position in self._stop_floor:
                # remove the position from the stop floor
                self._stop_floor.remove(self._position)
                if self._position in self._call_floor:
                    self._call_floor.remove(self._position)
                # perform additional waiting time
                self._timer += self._random_generator.gen_close_door()
                logging.debug("Lift {} arrive on {}, closing door in {}".format(self.name,self.position,self._timer))
            elif self._position in self._call_floor:
                self._call_floor.remove(self._position)
                if self.attendance <= self.capacity:
                    self._timer += self._random_generator.gen_close_door()
                logging.debug("Lift {} arrive on {}, closing door in {}".format(self.name,self.position,self._timer))

            if self._status != "idle":
                #logging.debug("Position Move {} Target {}".format(self.position,self._target))
                self._position = self._target
                #logging.debug("Position Move {}".format(self.position))

            """
            move the lift
            """
            if self._status == "up":
                self.go_up()
            elif self._status == "down":
                self.go_down()

        if self._timer > 0:
            self._timer -= 1

        logging.debug("Stop Floor: {}".format(self._stop_floor))
        logging.debug("Call Floor: {}".format(self._call_floor))
        logging.debug("Lift {} go {} from {} to {} arrive in {}".format(self.name,self._status,self._position,self._target,self._timer))


    def __repr__(self):
        # print(self.served_floor)
        return "Lift {}, capacity: {}, attendance: {}, position: {}, serve: {}".format(self.name, self.capacity,
                                                                                       self.attendance, self.position,
                                                                                       ",".join([str(x) for x in
                                                                                                 self.served_floor]))


class HotelLift():
    def __init__(self, number_of_floor: int, number_of_lift: int, rooms_floor_count, room_types: dict,
                 random_generator: RandomMovementGenerator):
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
            #logging.debug(x)
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
    def lifts(self):
        return self._lifts

    @property
    def floors(self) -> list:
        return self._floors

    @property
    def rooms(self):
        return self._rooms

    @property
    def total_capacity(self):
        return self._total_capacity

    def __repr__(self):
        output = ""
        for x in self.lifts.values():
            output += x.__repr__() + "\n"
        return output


class HotelLiftQueue():
    def __init__(self, hotel_lift: HotelLift):
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
        if att not in self._hotel_floor[int(floor)].lift_queue:
            self._hotel_floor[int(floor)].lift_queue.append(att)
        # initialize lift_path to check the shortest lift_path
        lift_path = [x for x in range(len(self.hotel_lift.floors) * 2)]
        lift_call = None
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
                elif lift_to_pos_dir == lift._status:
                    if len(lift_path) > len(lift_to_pos_dir):
                        lift_path = lift_to_pos_dir
                        lift_call = lift
                if lift_call != None:
                    lift.call(floor)
            except BaseException as ex:
                path = []

        return (lift_call,lift_path)
        """
        for lift in self._hotel_lift.lifts.values():
            if lift._status == "idle":
        """


class Person():
    def __init__(self, name: str, move_time: int, outside_time: int, random_generator: RandomMovementGenerator,
                 schedule={}, capacity_unit=1):
        self._name = name
        self._capacity_unit = capacity_unit

    @property
    def capacity_unit(self):
        return self._capacity_unit

    @property
    def name(self):
        return self._name


class Attendance(Person):
    _target_dest = ["room", "outside", "conference", "dining"]
    _status = ["idle", "go_lift", "waiting_lift", "in_lift", "on_move"]

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

    def __init__(self, room: Room, name: str, move_time: int, outside_time: int,
                 random_generator: RandomMovementGenerator, lift_queue: HotelLiftQueue, schedule: dict = {},
                 capacity_unit: int = 1):
        Person.__init__(self, name, move_time=move_time, outside_time=outside_time, capacity_unit=capacity_unit,
                        schedule=schedule, random_generator=random_generator)
        self._room = room
        self._lift_queue = lift_queue

        self._schedule = schedule
        self._move_time = move_time
        self._outside_time = outside_time
        self._random_move_time = GaussianDist(mu=move_time, sigma=move_time / 2, low=0, high=move_time * 2)
        self._random_outside_time = GaussianDist(mu=outside_time, sigma=outside_time / 2, low=0, high=outside_time * 2)
        self._next_move = 0
        self._random_generator = random_generator

        """
        status for a person is

        """
        self._status = "idle"
        self._position = "outside"
        self._target = ""
        self._action = ""
        self._moving_path = []

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, room: Room):
        self._room = room

    def call_lift(self):
        lift_queue.call_lift(self._position, self._target)

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
        """
        if len(self._moving_path) == 0:
            self.generate_next_move()

        if self._next_move == 0 and self._moving_path[0] == self._position:
            # pop the value
            popped = self._moving_path.pop(0)
            logging.debug("person {}, pop path {}".format(self._name, popped))
            self._action = self._moving_path[0]

        if self._action == "waiting_lift":
            """
            call the lift
            """
            if self._position == "room":
                from_where = self._room.floor.floor_name
            elif self._position == "outside":
                from_where = 0

            if self._target == "room":
                to_where = self._room.floor.floor_name
            elif self._target == "outside":
                to_where = 0

            lift, path = self._lift_queue.call_lift(self, from_where, to_where)
            logging.debug("Person {}, call lift {}, path: {}".format(self._name,lift,path))

        if self._next_move > 0:
            self._next_move -= 1
            logging.debug(
                "Person {}, move from {} to {} in {}".format(self._name, self._position, self._target, self._next_move))

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

    def generate_next_move(self):
        if self._position == "room":
            self._next_move = round(self._random_move_time.random())
            # self._next_move = self._random_generator.random_move_time()
            self._target = "outside"
        else:
            self._next_move = round(self._random_outside_time.random())
            # self._next_move = self._random_generator.random_outside_time()
            self._target = "room"

        self._moving_path = nx.shortest_path(self._move_graph, self._position, self._target)

    def __repr__(self):
        return "name: {}, room: {}".format(self.name, self.room)


class InitialGenerator():
    def __init__(self, room_stack: list, room_occupancy_pctg: float, move_time: int, outside_time: int,
                 random_generator: RandomMovementGenerator, lift_queue: HotelLiftQueue):
        # sample room_stack based on occupancy percentage
        total_rooms = len(room_stack)
        occupied_index = np.random.randint(total_rooms, size=np.int(room_occupancy_pctg * total_rooms))
        self._room_stack = room_stack
        logging.debug(occupied_index)
        # occupied = [room_stack[x] for x in occupied_index]
        self._attendance = []
        number = 0
        for i in occupied_index:
            room = room_stack[i]
            # room.occupied = True
            # for every room occupied, create attendance person based on the capacity
            number_of_attendance = np.random.randint(room.capacity) + 1
            # print(room)
            for j in range(number_of_attendance):
                # create new attendance
                new_att = Attendance(room, number, move_time=move_time, outside_time=outside_time,
                                     random_generator=random_generator, lift_queue=lift_queue)
                new_att.position = "room"
                room.attendance_checkin(new_att)
                self._attendance.append(new_att)
                number += 1

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
    def __init__(self, attendance: list, hotel_lift: list, interval: float = 1):
        self._attendance = attendance
        self._hotel_lift = hotel_lift
        self._status = "stop"
        self._interval = interval

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

        for lift in self._hotel_lift.values():
            lift.perform_move()

    def run_simulation(self):
        while self._status == "start":
            # print(self._status)
            self.simulate_timer()
            time.sleep(self._interval)
        print(self._status)

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
        print(self._status)

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

# HotelFloor(rooms_floor_count,room_types)
random_generator = RandomMovementGenerator(person={"move_time": 14400, "outside_time": 3600},
                                           lift={"max_waiting_time": 10, "sigma": 5})

hotel = HotelLift(20, 4, rooms_floor_count, room_types, random_generator=random_generator)
print(hotel)
len(hotel.rooms)

lift_queue = HotelLiftQueue(hotel_lift=hotel)
simulate = InitialGenerator(room_stack=hotel.rooms, room_occupancy_pctg=0.8, move_time=200, outside_time=100,
                            random_generator=random_generator, lift_queue=lift_queue)

helper = SimulationHelper(attendance=simulate.attendance, hotel_lift=hotel.lifts, interval=0.1)

helper.run()
