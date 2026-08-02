"""
optimizer.py — brute-force search over fin dimensions to find the design
that maximizes apogee while meeting minimum stability and a flutter safety margin.

Cascade (cheap checks first, expensive last):
  1. set the candidate fin dimensions
  2. get_stability()  -> cheap, no flight sim. If below MIN_STABILITY, skip.
  3. get_flight_data() -> the expensive flight sim (gives apogee, max velocity,
     AND the speed-of-sound / pressure that flutter needs)
  4. calculate_flutter() -> flutter velocity must beat max velocity by FLUTTER_MARGIN.
  5. survivors: record apogee, compare, keep the best.
"""

import orlab
import numpy as np

from simulator import (
    get_fins,
    get_stability,
    get_fin_dimensions,
    get_flight_data,
    JAR_FILE,
    ORK_FILE,
    M_TO_IN,
)
from flutter import calculate_flutter

#=====================================================================
#  PARAMETERS
#=====================================================================

# minimum acceptable static stability
MIN_STABILITY = 1.5   # calibers

# flutter safety margin: flutter velocity must be at least this factor
# above the rocket's max velocity. 1.5 = 50% margin.
FLUTTER_MARGIN = 1.5

# m/s -> ft/s  (max_velocity comes from OpenRocket in m/s; flutter is in ft/s)
MS_TO_FTS = 3.28084

ROOT_CHORD_RANGE = np.linspace(8.0, 10.0, 3)    # inches
TIP_CHORD_RANGE = np.linspace(1.0, 8.0, 8)      # inches
HEIGHT_RANGE = np.linspace(4.5, 5.5, 5)         # inches (semi-span)
SWEEP_RANGE = np.linspace(0.0, 8.0, 17)          # inches
THICKNESS_RANGE = np.linspace(0.125, 0.25, 3)    # inches

#=====================================================================
#  HELPER — set fin dimensions on the rocket
#=====================================================================

def set_fin_dimensions(fins, root_chord, tip_chord, height, sweep, thickness):
    """
    Set the fin geometry. Values passed IN are in inches; OpenRocket wants meters.
    TODO: fill in the actual setter calls (fins.setRootChord(...), etc.)
          remember to convert inches -> meters (divide by M_TO_IN).
    """
    fins.setRootChord(root_chord / M_TO_IN)
    fins.setTipChord(tip_chord / M_TO_IN)
    fins.setHeight(height / M_TO_IN)
    fins.setSweep(sweep / M_TO_IN)
    fins.setThickness(thickness / M_TO_IN)

#=====================================================================
#  MAIN OPTIMIZER
#=====================================================================

with orlab.OpenRocketInstance(JAR_FILE, log_level="ERROR") as instance:
    orh = orlab.Helper(instance)
    doc = orh.load_doc(ORK_FILE)
    rocket = doc.getRocket()
    fins = get_fins(rocket)

    # keep the best design found so far
    best = None          # will hold a dict of the winning design
    best_apogee = -1.0

    results = []         # every feasible design, for later inspection

    # ---- sweep every combination ----
    for root_chord in ROOT_CHORD_RANGE:
        for tip_chord in TIP_CHORD_RANGE:

            # a trapezoidal fin can't have tip wider than root — skip impossible shapes
            if tip_chord > root_chord:
                continue

            for height in HEIGHT_RANGE:
                for sweep in SWEEP_RANGE:
                    for thickness in THICKNESS_RANGE:

                        # 1. UPDATE ROCKET WITH THESE FIN DIMENSIONS
                        set_fin_dimensions(fins, root_chord, tip_chord,
                                           height, sweep, thickness)

                        # 2. CHECK FOR MIN STABILITY REQUIREMENT (NO SIMULATION RUNNING)
                        stability = get_stability(orh, rocket)
                        if stability < MIN_STABILITY:
                            continue   # reject without ever running a flight sim

                        # 3. MORE TIME-CONSUMING FLIGHT SIM gives apogee, max velocity,
                        #    and the flutter inputs
                        flight = get_flight_data(orh, doc)
                        dims = get_fin_dimensions(rocket)
                        values = {**dims, **flight}

                        # 4. flutter velocity must beat max velocity by 50% margin
                        # (convert max velocity m/s -> ft/s)
                        flutter_velocity = calculate_flutter(values)
                        max_velocity_fts = values["max_velocity"] * MS_TO_FTS
                        if flutter_velocity < max_velocity_fts * FLUTTER_MARGIN:
                            continue

                        # 5. survivor — record it and compare
                        apogee = values["apogee"]
                        design = {
                            "root_chord": root_chord,
                            "tip_chord": tip_chord,
                            "height": height,
                            "sweep": sweep,
                            "thickness": thickness,
                            "stability": stability,
                            "max_velocity_fts": max_velocity_fts,
                            "flutter_velocity": flutter_velocity,
                            "apogee": apogee,
                        }
                        results.append(design)

                        if apogee > best_apogee:
                            best_apogee = apogee
                            best = design

    # ---- report ----
    print("\n===== SEARCH COMPLETE =====")
    print(f"Feasible designs found: {len(results)}")
    if best is not None:
        print("\nBEST DESIGN (highest apogee meeting stability + flutter margin):")
        for k, v in best.items():
            if k == "apogee":
                print(f"  apogee (ft): {v * 3.28084:.1f}")
            else:
                print(f"  {k}: {v:.3f}")
    else:
        print("No design met the stability and flutter requirements.")

        