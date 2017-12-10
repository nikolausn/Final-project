# Title: Hotel Lift Monte Carlo Simulation

## Team Member(s): nikolausn

# Monte Carlo Simulation Scenario & Purpose:
In this project, I tried to simulate the lifts traffic in a hotel. Often in the real world, we are asking about how long we must wait for a lift in order to get to our designated floor, how much travel time needed, and how the lift handle traffic queue in a busy time. In a hotel, the lift is an important feature for attendance or even hotel staffs. The usage of the hotel's lifts depends on how many guests are there in the hotel and how often they move between floors. 

To simulate the real world Hotel Lift, I make a program that can simulate a real-life situation. I build the code using an Object-Oriented method in which we can configure the environment of the hotel by using dictionary parameters. For example, we can configure how many floors that a hotel has, how many lifts, which floor that a lift serves, how many rooms for each floor, what are the room type and its capacity, how many people can a lift handle, etc. By using this complexity, I expect this code to be able to accommodate different scenarios.

For the simulation purpose, I tried to handle 3 different scenarios. Firstly, evacuation scenario, given the configuration in the particular hotel, we want to measure how long we can evacuate all the guest in the hotel room using lifts in the hotel. This scenario is useful to understand the effectiveness of the hotel lift configuration to handle evacuation and further can be used to develop a better queue or system for evacuation handling. Next, conference bulk check-in scenario, using the same configuration we will try to bring all the guest that comes at the random time to the designated floor. This scenario is useful to understand how long the attendance needs to spend the time to go to the designated floor in the busy situation. Finally, we can also try the real world lift usage by simulating people going in and out in a designated random time by configuring hotel occupancy and movement time.

### Hypothesis before running the simulation:
For the simulation purpose I used this following configuration:

Room Type:
- Single, Capacity: 2
- Double, Capacity: 2
- Deluxe, Capacity: 4

Hotel Floors: 20

Rooms every Floors:
- Single: 20
- Double: 20
- Deluxe: 10

Number of Lifts: 6
Configuration:
- 1: floor 0 - 19, speed 1 each floor
- 2: floor 0 - 19, speed 1 each floor
- 3: floor 0 - 9, speed 1 each floor
- 4: floor 0 - 9, speed 1 each floor
- 5: floor 10 - 19, speed 10 for 0 - 10, next speed 1 each floor
- 6: floor 10 - 19, speed 10 for 0 - 10, next speed 1 each floor

The time measure in this simulation is second, so we compute every single second for each object (Lift, and Guests) to measure they spending time.

Before running the simulation, I might use my hypothesis for every scenario:
- evacuation scenario: there is no relation within hotel occupancy and average waiting time and average in lift time in the evacuation scneario
- bulk check-in scenario: there is no relation within hotel occupancy and average waiting time and average in lift time in the evacuation scneario
- normal schedule scenario: there is no relation within hotel occupancy and average waiting time and average in lift time in the normal schedule scenario.

### Simulation's variables of uncertainty
There are several variables I used for the uncertainty:
- movement_waiting_time: is a movement parameter to produce a random variable of a person movement. Generating this random number will trigger the movement of a person after the designated time is reached. The waiting time itself is highly configurable and distributed in a Gaussian manner which skewed 2/3 to the left of the maximum time to simulate real-life behavior. The maximum waiting movement time can be configured in the json configuration file according to which schedule or what scenario we want to use
- door_closing_time: every time a lift door open in a floor, it has generated random waiting time to wait for another guest to get into the lift. This random waiting time is useful to simulate people behavior in a lift. People often push the close door button to close the lift immediately or just leave it closed automatically (maximum time). This variable is generated using normal Gaussian distribution with half of the maximum time as the mean. For this parameter, I used 10 seconds for the maximum door closing time
- assigned_schedule: attendances will be randomly assigned to a room and specific schedule according to the configuration file. To understand about the configuration more, look at the instructions on how to use the program

## Instructions on how to use the program:
To use the program we can just run the script hotel_lift_monte_carlo.py and it will run the simulation using the parameter in the code (for now, and might be stored in a config file later). The program itself run in a thread, and right now it will run forever until you pause the program using Command button (in mac), or push a control-C to stop the code. The program will produce a statistic file named results.txt which is described as this example

```
AttendanceName,FromFloor,ToFloor,WaitingTime,InLiftTime,TotalSpendTime
984,17,0,40,38,78
1051,17,0,14,38,52
1135,14,0,13,29,42
1136,14,0,72,29,101
1154,14,0,32,29,61
1248,14,0,1,24,25
```

## Hypothesis Testing


## Sources Used:
- 9.6. random - Generate pseudo-random numbers¶. (n.d.). Retrieved November 28, 2017, from https://docs.python.org/2/library/random.html
- Monte Carlo method. (2017, November 20). Retrieved November 28, 2017, from https://en.wikipedia.org/wiki/Monte_Carlo_method
- (n.d.). Retrieved November 28, 2017, from https://pypi.python.org/pypi/pynput
- 16.2. threading - Higher-level threading interface¶. (n.d.). Retrieved November 28, 2017, from https://docs.python.org/2/library/threading.html
