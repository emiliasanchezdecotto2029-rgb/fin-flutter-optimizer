"""
searches fin dimensions to find the design that maximizes apogee while meeting 
minimum stability and a flutter safety margin. All candidates written to csv file.

Steps:
  1. set the candidate fin dimensions
  2. get_stability()  -> no flight sim. If below MIN_STABILITY, don't consider.
  3. get_flight_data() -> expensive flight sim (gives apogee, max velocity,
     AND the speed-of-sound / pressure that flutter needs)
  4. calculate_flutter() -> flutter velocity must be above max velocity by a 50% margin
  5. for remaining fin dimensions, record apogee, keep the best.
"""

import csv
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

#PARAMETERS
#------------------------------------------------------------

#for saving results to CSV
RESULTS_CSV = "results.csv"
FIELDNAMES = [
    "status",
    "root_chord", "tip_chord", "height", "sweep_length", "thickness", "fin_area",
    "stability", "sim",
    "apogee_m", "apogee_ft",
    "max_velocity_fts", "flutter_velocity_fts", "flutter_ratio"
]

#max unsupported fin extending past the aft end of the root, inches
#(sweep + tip_chord - root_chord). the 2026 flown fins have 2.0
MAX_OVERHANG = 2.0

#taper ratio below ~0.2 the tip gets thin and flutter-prone; 
# literature suggests ~0.4 for an elliptical lift distribution
MIN_TAPER = 0.2

#mnimum stability threshold
MIN_STABILITY = 1.5 

# flutter margin: flutter velocity must be at least this factor
FLUTTER_MARGIN = 1.5

# m/s -> ft/s
MS_TO_FTS = 3.28084

#inches:
ROOT_CHORD_RANGE = np.linspace(8.0, 12.0, 9)     #8" floor from fin tab geometry
TIP_CHORD_RANGE = np.linspace(1.0, 8.0, 8)     
HEIGHT_RANGE = np.linspace(5.25, 6.0, 4)         #>= 1 caliber (5.15" OD)
SWEEP_RANGE = np.linspace(0.0, 12.0, 13)         
THICKNESS_RANGE = np.linspace(0.125, 0.25, 3)

#set fin dimensions on the rocket
def set_fin_dimensions(fins, root_chord, tip_chord, height, sweep, thickness):
    fins.setRootChord(root_chord / M_TO_IN)
    fins.setTipChord(tip_chord / M_TO_IN)
    fins.setHeight(height / M_TO_IN)
    fins.setSweep(sweep / M_TO_IN)
    fins.setThickness(thickness / M_TO_IN)

#optimization process
if __name__ == "__main__":
    with orlab.OpenRocketInstance(JAR_FILE, log_level="ERROR") as instance, \
            open(RESULTS_CSV, "w", newline="") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()

        orh = orlab.Helper(instance)
        doc = orh.load_doc(ORK_FILE)
        rocket = doc.getRocket()
        fins = get_fins(rocket)

        # keep the best design found so far
        best = None          
        best_apogee = -1.0

        #every feasible design goes here
        results = []         

        #sweeping combinations
        for root_chord in ROOT_CHORD_RANGE:
            for tip_chord in TIP_CHORD_RANGE:

                #taper ratio floor (also rules out tip wider than root)
                if tip_chord / root_chord < MIN_TAPER:
                    continue

                for height in HEIGHT_RANGE:
                    for sweep in SWEEP_RANGE:

                        #reject unbuildable overhang
                        if sweep + tip_chord - root_chord > MAX_OVERHANG:
                            continue
                        for thickness in THICKNESS_RANGE:

                            #Update OpenRocket with FinDimensions
                            set_fin_dimensions(fins, root_chord, tip_chord,
                                            height, sweep, thickness)

                            #Cheap stability check (no sim)
                            stability = get_stability(orh, rocket)
                            dims = get_fin_dimensions(rocket)

                            if stability < MIN_STABILITY:
                                writer.writerow({
                                    "status": "rejected_stability",
                                    "root_chord": dims["root_chord"],
                                    "tip_chord": dims["tip_chord"],
                                    "height": dims["height"],
                                    "sweep_length": dims["sweep_length"],
                                    "thickness": dims["thickness"],
                                    "fin_area": dims["fin_area"],
                                    "stability": stability,
                                    "sim": False,
                                })
                                csvfile.flush()
                                continue

                            #Flight sim gives apogee, max velocity, flutter values
                            flight = get_flight_data(orh, doc)
                            values = {**dims, **flight}

                            #flutter check
                            flutter_velocity = calculate_flutter(values)
                            max_velocity_fts = values["max_velocity"] * MS_TO_FTS
                            flutter_ratio = flutter_velocity / max_velocity_fts
                            apogee = values["apogee"]

                            row = {
                                "root_chord": dims["root_chord"],
                                "tip_chord": dims["tip_chord"],
                                "height": dims["height"],
                                "sweep_length": dims["sweep_length"],
                                "thickness": dims["thickness"],
                                "fin_area": dims["fin_area"],
                                "stability": stability,
                                "sim": True,
                                "apogee_m": apogee,
                                "apogee_ft": apogee * 3.28084,
                                "max_velocity_fts": max_velocity_fts,
                                "flutter_velocity_fts": flutter_velocity,
                                "flutter_ratio": flutter_ratio,
                            }

                            if flutter_ratio < FLUTTER_MARGIN:
                                writer.writerow({"status": "rejected_flutter", **row})
                                csvfile.flush()
                                continue

                            row["status"] = "feasible"
                            writer.writerow(row)
                            csvfile.flush()

                            #record surviving designs and compare
                            results.append(row)

                            if apogee > best_apogee:
                                best_apogee = apogee
                                best = row

        #printing results
        print("\nRESULTS")
        print(f"Feasible designs found: {len(results)}")
        if best is not None:
            print("\nOPTIMAL DESIGN:")
            for k in ("root_chord", "tip_chord", "height", "sweep_length",
                      "thickness", "stability", "max_velocity_fts",
                      "flutter_velocity_fts", "flutter_ratio", "apogee_ft"):
                print(f"  {k}: {best[k]:.3f}")
        else:
            print("0 designs met requirements")