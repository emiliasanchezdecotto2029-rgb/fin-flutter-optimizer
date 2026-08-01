"""
Uses data from simulator.py to calculate fin flutter per corrected NACA method
"""

import orlab
import math
from simulator import simulate, JAR_FILE, ORK_FILE

# open OpenRocket once, get all the values
with orlab.OpenRocketInstance(JAR_FILE, log_level="ERROR") as instance:
    orh = orlab.Helper(instance)
    values = simulate(orh, ORK_FILE)

TC = values["tip_chord"]
RC = values["root_chord"]
height = values["height"]
thickness = values["thickness"]
sweep_length = values["sweep_length"]
fin_area = values["fin_area"]
pressure_max_velocity = values["pressure_max_velocity"]
launch_pressure = values["launch_pressure" \
""]
speed_of_sound = values["speed_of_sound"]

# shear modulus for: ALUMINUM 6061-T6 (PSI)
shear_modulus = 3700000

#############################
#CALCULATING FLUTTER VELOCITY
#############################

#Cx
Cx_numerator = (2 * TC * sweep_length) + TC**2 + (sweep_length * RC) + (TC * RC) + RC**2
Cx_denominator = 3 * (TC + RC)
Cx = Cx_numerator/Cx_denominator

#EPSILON
epsilon = (Cx / RC) - 0.25

#Denominator Constant
DN = (24 * epsilon * 1.4 * 14.696) / 3.141592653589793

#ASPECT RATIO
A = (height**2)/fin_area

#THICKNESS RATIO
TR = thickness/RC

#TAPER RATIO
gamma = TC/RC

#PRESSURE RATIO
pressure_ratio = pressure_max_velocity/14.696

### SQUARE ROOT DENOMINATOR ##
root_denominator = ((DN * A**3)/(TR**3 * (A + 2)) * ((gamma + 1)/2)) * pressure_ratio

# FLUTTER VELOCITY IN F/S

flutter_velocity = speed_of_sound * math.sqrt(shear_modulus/root_denominator)

print(f"Flutter Velocity (ft/s): {flutter_velocity:.1f}")


