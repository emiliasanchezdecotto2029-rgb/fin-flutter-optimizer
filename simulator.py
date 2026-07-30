"""
First version of python file that aims to be able to calculate stability and altitude from an Open Rocket File.
"""

import orlab
import numpy as np

JAR_FILE = "OpenRocket-23.09.jar"
ORK_FILE = "stars_rocket.ork"


def simulate(orh, ork_file):
    doc = orh.load_doc(ork_file)
    sim = doc.getSimulation(0)

    #running simulation
    orh.run_simulation(sim)

    #pulling apogee from results
    data = orh.get_timeseries(sim, ["TYPE_ALTITUDE"])
    apogee = max(data["TYPE_ALTITUDE"])

    #getting rocket static stability
    rocket = doc.getRocket()
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

    return {"apogee": apogee, "stability": stability}


#open the OpenRocket engine once, then call simulate() inside it
with orlab.OpenRocketInstance(JAR_FILE, log_level="ERROR") as instance:
    orh = orlab.Helper(instance)
    results = simulate(orh, ORK_FILE)
    print(f"Apogee: {results['apogee']:.1f} meters")
    print(f"Stability: {results['stability']:.2f} cal")