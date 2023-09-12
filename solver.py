import pandas as pd
from ortools.sat.python import cp_model
import math
import time
import warnings

warnings.filterwarnings('ignore')


# Function to calculate the distance between two coordinates
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


def solve(tolerance, drivers_data, riders_data, shifters_data):
    # Convert query results to dataframes
    drivers_df = pd.DataFrame(drivers_data)
    riders_df = pd.DataFrame(riders_data)
    shifters_df = pd.DataFrame(shifters_data)
    model = cp_model.CpModel()
    cp_solver = cp_model.CpSolver()

    n_drivers = len(drivers_df)
    n_riders = len(riders_df)
    n_shifters = len(shifters_df)

    # Variables
    n_drivers = len(drivers_df)
    n_riders = len(riders_df)
    n_shifters = len(shifters_df)

    # Define decision variables
    # Define decision variables
    x = [[model.NewBoolVar('x[%i][%i]' % (i, j)) for j in range(n_riders)] for i in range(n_drivers)]
    y = [[model.NewBoolVar('y[%i][%i]' % (i, j)) for j in range(n_riders)] for i in range(n_shifters)]
    z = [model.NewBoolVar('z[%i]' % i) for i in range(n_shifters)]
    y_rider = [[model.NewBoolVar('x_rider[%i][%i]' % (i, j)) for j in range(n_shifters)] for i in range(n_drivers)]
    w = [[model.NewBoolVar('w[%i][%i]' % (i, j)) for j in range(n_shifters)] for i in
         range(n_shifters)]  # shifter driver i has been assigned to shifter rider j

    # Each rider is taken by at most one driver or shifter acting as a driver
    for j in range(n_riders):
        model.Add(sum(x[i][j] for i in range(n_drivers)) + sum(y[i][j] for i in range(n_shifters)) <= 1)

    # Each shifter, when acting as a rider, is taken by at most one driver
    for j in range(n_shifters):
        model.Add(sum(y_rider[i][j] for i in range(n_drivers)) <= 1)

    # Each driver takes riders up to their capacity
    for i in range(n_drivers):
        model.Add(
            sum([x[i][j] for j in range(n_riders)] + [y_rider[i][j] for j in range(n_shifters)]) <= drivers_df.loc[
                i, 'seats'])

    # Each shifter, when acting as a driver, takes riders up to their capacity
    for i in range(n_shifters):
        model.Add(sum(y[i][j] for j in range(n_riders)) <= shifters_df.loc[i, 'seats'] * z[i])

    # A shifter cannot act as both a driver and a rider at the same time
    for i in range(n_shifters):
        model.Add(z[i] + sum(y_rider[k][i] for k in range(n_drivers)) <= 1)

    # Constraints for departure times
    for i in range(n_drivers):
        for j in range(n_riders):
            if abs(drivers_df.loc[i, 'departure_time'] - riders_df.loc[j, 'departure_time']) > pd.Timedelta(minutes=30):
                model.Add(x[i][j] == 0)

    # Define distances for drivers and shifters
    dist_drivers_start = [[haversine(drivers_df.loc[i, 'start_long'], drivers_df.loc[i, 'start_lat'],
                                     riders_df.loc[j, 'start_long'], riders_df.loc[j, 'start_lat'])
                           for j in range(n_riders)] for i in range(n_drivers)]
    dist_drivers_end = [[haversine(drivers_df.loc[i, 'end_long'], drivers_df.loc[i, 'end_lat'],
                                   riders_df.loc[j, 'end_long'], riders_df.loc[j, 'end_lat'])
                         for j in range(n_riders)] for i in range(n_drivers)]
    # Constraints for distances
    for i in range(n_drivers):
        for j in range(n_riders):
            model.Add(
                x[i][j] <= (1 if dist_drivers_start[i][j] <= tolerance and dist_drivers_end[i][j] <= tolerance else 0))

    # Each driver takes riders up to their capacity and considering their constraints for pets, smokers, and disabled
    for i in range(n_drivers):
        for j in range(n_riders):
            if (drivers_df.loc[i, 'pet'] == 'NO' and riders_df.loc[j, 'pet'] == 'YES') or \
                    (drivers_df.loc[i, 'smoker'] == 'NO' and riders_df.loc[j, 'smoker'] == 'YES') or \
                    (drivers_df.loc[i, 'disable'] == 'NO' and riders_df.loc[j, 'disable'] == 'YES') or \
                    (drivers_df.loc[i, 'pet'] == 'YES' and riders_df.loc[j, 'pet'] == 'NO') or \
                    (drivers_df.loc[i, 'smoker'] == 'YES' and riders_df.loc[j, 'smoker'] == 'NO'):
                model.Add(x[i][j] == 0)
            elif (drivers_df.loc[i, 'pet'] == 'YES' and (
                    riders_df.loc[j, 'pet'] == 'YES' or riders_df.loc[j, 'pet'] == 'BOTH')) and \
                    (drivers_df.loc[i, 'pet'] == 'NO' and riders_df.loc[j, 'pet'] == 'BOTH') and \
                    (drivers_df.loc[i, 'smoker'] == 'YES' and (
                            riders_df.loc[j, 'smoker'] == 'YES' or riders_df.loc[j, 'smoker'] == 'BOTH')) and \
                    (drivers_df.loc[i, 'smoker'] == 'NO' and riders_df.loc[j, 'smoker'] == 'BOTH') and \
                    (drivers_df.loc[i, 'disable'] == 'YES' and riders_df.loc[j, 'disable'] == 'YES'):
                model.Add(x[i][j] == 1)

    # Shifter as rider constraints for driver -driver takes shifter (as a rider)
    for i in range(n_drivers):
        for j in range(n_shifters):
            # If a driver and a shifter have matching preferences
            if (drivers_df.loc[i, 'pet'] == shifters_df.loc[j, 'pet'] and
                    drivers_df.loc[i, 'smoker'] == shifters_df.loc[j, 'smoker'] and
                    drivers_df.loc[i, 'disable'] == shifters_df.loc[j, 'disable'] and
                    abs(drivers_df.loc[i, 'departure_time'] - shifters_df.loc[j, 'departure_time']) <= pd.Timedelta(
                        minutes=30) and
                    haversine(drivers_df.loc[i, 'start_long'], drivers_df.loc[i, 'start_lat'],
                              shifters_df.loc[j, 'start_long'], shifters_df.loc[j, 'start_lat']) <= tolerance and
                    haversine(drivers_df.loc[i, 'end_long'], drivers_df.loc[i, 'end_lat'],
                              shifters_df.loc[j, 'end_long'], shifters_df.loc[j, 'end_lat']) <= tolerance):
                # The shifter can be a rider of this driver
                model.Add(y_rider[i][j] == 1)
                # If the shifter is a rider of this driver, it cannot be a driver
            else:
                # The shifter cannot be a rider of this driver
                model.Add(y_rider[i][j] == 0)

    # Constraints for departure times shifter
    for i in range(n_shifters):
        for j in range(n_riders):
            if abs(shifters_df.loc[i, 'departure_time'] - riders_df.loc[j, 'departure_time']) > pd.Timedelta(
                    minutes=30):
                model.Add(y[i][j] == 0)

    dist_shifters_start = [[haversine(shifters_df.loc[i, 'start_long'], shifters_df.loc[i, 'start_lat'],
                                      riders_df.loc[j, 'start_long'], riders_df.loc[j, 'start_lat'])
                            for j in range(n_riders)] for i in range(n_shifters)]
    dist_shifters_end = [[haversine(shifters_df.loc[i, 'end_long'], shifters_df.loc[i, 'end_lat'],
                                    riders_df.loc[j, 'end_long'], riders_df.loc[j, 'end_lat'])
                          for j in range(n_riders)] for i in range(n_shifters)]

    for i in range(n_shifters):
        for j in range(n_riders):
            model.Add(y[i][j] <= (
                1 if dist_shifters_start[i][j] <= tolerance and dist_shifters_end[i][j] <= tolerance else 0))

    # Each shifter, when acting as a driver, takes riders up to their capacity and considering their constraints for pets, smokers, and disabled
    for i in range(n_shifters):
        for j in range(n_riders):
            if (shifters_df.loc[i, 'pet'] == 'NO' and riders_df.loc[j, 'pet'] == 'YES') or \
                    (shifters_df.loc[i, 'smoker'] == 'NO' and riders_df.loc[j, 'smoker'] == 'YES') or \
                    (shifters_df.loc[i, 'disable'] == 'NO' and riders_df.loc[j, 'disable'] == 'YES') or \
                    (shifters_df.loc[i, 'pet'] == 'YES' and riders_df.loc[j, 'pet'] == 'NO') or \
                    (shifters_df.loc[i, 'smoker'] == 'YES' and riders_df.loc[j, 'smoker'] == 'NO'):
                model.Add(y[i][j] == 0)
            elif (shifters_df.loc[i, 'pet'] == 'YES' and (
                    riders_df.loc[j, 'pet'] == 'YES' or riders_df.loc[j, 'pet'] == 'BOTH')) and \
                    (shifters_df.loc[i, 'pet'] == 'NO' and riders_df.loc[j, 'pet'] == 'BOTH') and \
                    (shifters_df.loc[i, 'smoker'] == 'YES' and (
                            riders_df.loc[j, 'smoker'] == 'YES' or riders_df.loc[j, 'smoker'] == 'BOTH')) and \
                    (shifters_df.loc[i, 'smoker'] == 'NO' and riders_df.loc[j, 'smoker'] == 'BOTH') and \
                    (shifters_df.loc[i, 'disable'] == 'YES' and riders_df.loc[j, 'disable'] == 'YES'):
                model.Add(y[i][j] == 1)

    # Each shifter-driver can take shifter-riders up to their capacity
    for i in range(n_shifters):
        model.Add(sum(w[i][j] for j in range(n_shifters) if i != j) <= shifters_df.loc[i, 'seats'])

    # Each shifter-rider is taken by at most one shifter-driver
    for j in range(n_shifters):
        model.Add(sum(w[i][j] for i in range(n_shifters) if i != j) <= 1)

    # A shifter cannot act as both a driver and a rider at the same time
    for i in range(n_shifters):
        model.Add(sum(w[i][j] for j in range(n_shifters) if i != j) +
                  sum(w[j][i] for j in range(n_shifters) if i != j) <= 1)

    # Shifter-driver takes shifter-rider if preferences match and within distance and time constraints
    for i in range(n_shifters):
        for j in range(n_shifters):
            if i != j:
                # If a shifter-driver and a shifter-rider have matching preferences
                if (shifters_df.loc[i, 'pet'] == shifters_df.loc[j, 'pet'] and
                        shifters_df.loc[i, 'smoker'] == shifters_df.loc[j, 'smoker'] and
                        shifters_df.loc[i, 'disable'] == shifters_df.loc[j, 'disable'] and
                        abs(shifters_df.loc[i, 'departure_time'] - shifters_df.loc[
                            j, 'departure_time']) <= pd.Timedelta(minutes=30) and
                        haversine(shifters_df.loc[i, 'start_long'], shifters_df.loc[i, 'start_lat'],
                                  shifters_df.loc[j, 'start_long'], shifters_df.loc[j, 'start_lat']) <= tolerance and
                        haversine(shifters_df.loc[i, 'end_long'], shifters_df.loc[i, 'end_lat'],
                                  shifters_df.loc[j, 'end_long'], shifters_df.loc[j, 'end_lat']) <= tolerance):
                    # The shifter-rider can be taken by this shifter-driver
                    pass  # Do nothing as the assignment is feasible
                else:
                    # The shifter-rider cannot be taken by this shifter-driver
                    model.Add(w[i][j] == 0)

    # Objective: maximize the total number of riders taken
    total_matches = (sum(x[i][j] for i in range(n_drivers) for j in range(n_riders)) +
                     sum(y[i][j] for i in range(n_shifters) for j in range(n_riders)) +
                     sum(w[i][j] for i in range(n_shifters) for j in range(n_shifters)) +
                     sum(y_rider[i][j] for i in range(n_drivers) for j in range(n_shifters)))

    model.Maximize(total_matches)

    # Solve the problem and print the solution
    status = cp_solver.Solve(model)

    result_list = []

    # Inside your if condition for OPTIMAL results:
    if status == cp_model.OPTIMAL:
        result_list.append('')

        # For Driver-Rider matches
        for i in range(n_drivers):
            for j in range(n_riders):
                if cp_solver.Value(x[i][j]) > 0:
                    departure_time = str(drivers_df.loc[i, 'departure_time'])
                    result_list.append(
                        'Driver ({}) takes rider ({}) on {}.'.format(drivers_df.loc[i, 'name'],
                                                                     riders_df.loc[j, 'name'], departure_time))

        # For Shifter acting as Driver-Rider matches
        for i in range(n_shifters):
            for j in range(n_riders):
                if cp_solver.Value(y[i][j]) > 0:
                    departure_time = str(shifters_df.loc[i, 'departure_time'])
                    result_list.append(
                        'Shifter ({}) acts as a driver and takes rider ({}) on {}.'.format(shifters_df.loc[i, 'name'],
                                                                                           riders_df.loc[j, 'name'],
                                                                                           departure_time))

        # For Driver-Shifter acting as Rider matches
        for i in range(n_drivers):
            for j in range(n_shifters):
                if cp_solver.Value(y_rider[i][j]) > 0:
                    departure_time = str(drivers_df.loc[i, 'departure_time'])
                    result_list.append('Driver ({}) takes shifter ({}) who will act as a rider on {}.'.format(
                        drivers_df.loc[i, 'name'], shifters_df.loc[j, 'name'], departure_time))

        # For Shifter acting as Driver taking another Shifter as Rider matches
        for i in range(n_shifters):
            for j in range(n_shifters):
                if i != j and cp_solver.Value(w[i][j]) > 0:
                    departure_time = str(shifters_df.loc[i, 'departure_time'])
                    result_list.append(
                        'Shifter ({}) acts as a driver and takes shifter ({}) who will act as a rider on {}.'.format(
                            shifters_df.loc[i, 'name'], shifters_df.loc[j, 'name'], departure_time))
    else:
        result_list.append('Solution not found.')

    print("Results:", result_list)
    return result_list
