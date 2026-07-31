"""
First version of python file that aims to be able to calculate stability and altitude from an Open Rocket File.
"""

import orlab
import numpy as np

JAR_FILE = "OpenRocket-23.09.jar"
ORK_FILE = "stars_rocket.ork"

#---- unit conversion constants ----
M_TO_IN = 39.3701          # meters -> inches
M2_TO_IN2 = 1550.0031      # square meters -> square inches (39.3701^2)
PA_TO_PSI = 0.000145038    # pascals -> psi


def simulate(orh, ork_file):
    #loading open rocket file
    doc = orh.load_doc(ork_file)
    rocket = doc.getRocket()

    #running simulation
    sim = doc.getSimulation(0)
    orh.run_simulation(sim)

    #pulling apogee from results
    data_altitudes = orh.get_timeseries(sim, ["TYPE_ALTITUDE"])
    apogee = max(data_altitudes["TYPE_ALTITUDE"])

    # grab the REAL fins (trapezoidal, 4 fins) — match by type, not just "FinSet"
    fins = None
    for component in rocket.getAllChildren():
        if "TrapezoidFinSet" in type(component).__name__:
            fins = component
            break

    #simulated conditions (launch environment)
    sim_conditions = sim.getSimulatedConditions()

    #GET LAUNCH TEMPERATURE (Fahrenheit)
    launch_temp = sim_conditions.getLaunchTemperature()
    launch_temp_f = (launch_temp - 273.15) * (9/5) + 32

    #####################
    #GET ALTITUDE AT TIME OF MAX VELOCITY
    #first extract time at which maximum velocity is reached
    data_velocity = orh.get_timeseries(sim, ["TYPE_VELOCITY_Z"])
    velocities = data_velocity["TYPE_VELOCITY_Z"]
    time_max_velocity = np.where(velocities == max(velocities))[0][0]  # scalar index of max velocity

    #then get the altitude at that time
    altitudes = data_altitudes["TYPE_ALTITUDE"]
    altitude_max_velocity = altitudes[time_max_velocity]

    ###########
    #GET TIP CHORD, ROOT CHORD, HEIGHT, THICKNESS, AND SWEEP LENGTH (all converted to inches)
    tip_chord = fins.getTipChord() * M_TO_IN
    root_chord = fins.getRootChord() * M_TO_IN
    height = fins.getHeight() * M_TO_IN            # semi-span
    thickness = fins.getThickness() * M_TO_IN
    sweep_length = fins.getSweep() * M_TO_IN

    #calculate fin area (square inches)
    fin_area = (tip_chord + root_chord)/2 * height

    #air pressure at altitude where speed of sound was determined (psi)
    data_pressure = orh.get_timeseries(sim, ["TYPE_AIR_PRESSURE"])
    pressures = data_pressure["TYPE_AIR_PRESSURE"]
    pressure_max_velocity = pressures[time_max_velocity] * PA_TO_PSI

    #air pressure ASL (LAUNCH) (psi)
    launch_pressure = sim_conditions.getLaunchPressure() * PA_TO_PSI

    #####################
    #SPEED OF SOUND at max-velocity altitude (ft/sec)
    #T_F at altitude = 59 - (0.00356 * altitude in ft)   [ASL, default sea level temp]
    altitude_max_velocity_ft = altitude_max_velocity * 3.28084
    temp_at_altitude_f = 59 - (0.00356 * altitude_max_velocity_ft)
    speed_of_sound = 49.03 * np.sqrt(459.7 + temp_at_altitude_f)

    #getting rocket static stability
    config = rocket.getSelectedConfiguration()

    # CG at launch (motor loaded)
    MassCalculator = orh.openrocket.masscalc.MassCalculator
    cg = MassCalculator.calculateLaunch(config).getCM()

    # CP (worst case across angle of attack)
    aero = orh.openrocket.aerodynamics.BarrowmanCalculator().newInstance()
    FlightConditions = orh.openrocket.aerodynamics.FlightConditions
    conditions = FlightConditions(config)
    WarningSet = orh.openrocket.logging.WarningSet
    cp = aero.getWorstCP(config, conditions, WarningSet())

    diameter = config.getReferenceLength()
    stability = (cp.x - cg.x) / diameter

    #return everything calculated (imperial units)
    return {
        "apogee": apogee,                             # meters (OpenRocket native)
        "stability": stability,                       # calibers
        "launch_temp_f": launch_temp_f,               # F
        "altitude_max_velocity": altitude_max_velocity,  # meters
        "tip_chord": tip_chord,                       # in
        "root_chord": root_chord,                     # in
        "height": height,                             # in (semi-span)
        "thickness": thickness,                       # in
        "sweep_length": sweep_length,                 # in
        "fin_area": fin_area,                         # in^2
        "pressure_max_velocity": pressure_max_velocity,  # psi
        "launch_pressure": launch_pressure,           # psi
        "speed_of_sound": speed_of_sound,             # ft/sec
    }


#open the OpenRocket engine once, then call simulate() inside it
with orlab.OpenRocketInstance(JAR_FILE, log_level="ERROR") as instance:
    orh = orlab.Helper(instance)
    results = simulate(orh, ORK_FILE)

    print(f"Apogee (m):                    {results['apogee']:.1f}")
    print(f"Stability (cal):               {results['stability']:.2f}")
    print(f"Launch Temperature (F):        {results['launch_temp_f']:.1f}")
    print(f"Altitude at max velocity (m):  {results['altitude_max_velocity']:.1f}")
    print(f"Tip Chord (in):                {results['tip_chord']:.3f}")
    print(f"Root Chord (in):               {results['root_chord']:.3f}")
    print(f"Fin height / semi-span (in):   {results['height']:.3f}")
    print(f"Fin thickness (in):            {results['thickness']:.3f}")
    print(f"Sweep Length (in):             {results['sweep_length']:.3f}")
    print(f"Fin Area (in^2):               {results['fin_area']:.3f}")
    print(f"Pressure at max velocity (psi):{results['pressure_max_velocity']:.3f}")
    print(f"Launch Pressure (psi):         {results['launch_pressure']:.3f}")
    print(f"Speed of Sound (ft/s):         {results['speed_of_sound']:.1f}")