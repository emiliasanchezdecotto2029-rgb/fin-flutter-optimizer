"""
bridge_test.py — proves the OpenRocket <-> Python bridge works.

Only job: load a .ork file, run its first simulation, print the apogee.
If a number prints, the whole foundation (Java + JPype + orlab + jar) works.

Before running:
  - venv activated
  - OpenRocket-23.09.jar in this folder
  - a .ork file in this folder (edit ORK_FILE below to match its name)
"""

import orlab

# ---- EDIT THESE TWO LINES to match your actual filenames ----
JAR_FILE = "OpenRocket-23.09.jar"
ORK_FILE = "stars_rocket.ork"  # <-- change to your .ork file's name
# -------------------------------------------------------------

with orlab.OpenRocketInstance(JAR_FILE) as instance:
    orh = orlab.Helper(instance)

    # Load the rocket design
    doc = orh.load_doc(ORK_FILE)

    # Grab the first simulation in the file
    sim = doc.getSimulation(0)

    # Run it
    orh.run_simulation(sim)

    # Pull the apogee (max altitude) out of the results
    altitudes = orh.get_timeseries(sim, ["TYPE_ALTITUDE"])
    apogee = max(altitudes["TYPE_ALTITUDE"])

    print(f"Apogee: {apogee:.1f} meters")