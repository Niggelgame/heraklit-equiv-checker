import json

steps = []

NEXT_MODULE_READY = "Next Module Ready"


# returns the three steps in a tuple
def get_pick_steps(module):
    pick_start = {
        "name": f"{module} Pick",
        "left_places": [f"Start {module} Pick", f"AGV at {module}"],
        "right_places": [f"{module} Picking"],
    }

    pick_succ = {
        "name": f"{module} Picked",
        "left_places": [f"{module} Picking"],
        "right_places": [f"Finish {module} Pick", f"AGV at {module}"],
    }

    pick_fail = {
        "name": f"{module} Pick Failed",
        "left_places": [f"{module} Picking"],
        "right_places": [f"Order Failed", f"AGV at {module}"],
    }

    return pick_start, pick_succ, pick_fail


# returns the three steps in a tuple
def get_drop_steps(module):
    drop_start = {
        "name": f"{module} Drop",
        "left_places": [f"Start {module} Drop", f"AGV at {module}"],
        "right_places": [f"{module} Dropping"],
    }

    drop_succ = {
        "name": f"{module} Dropped",
        "left_places": [f"{module} Dropping"],
        "right_places": [f"Finish {module} Drop", f"AGV at {module}"],
    }

    drop_fail = {
        "name": f"{module} Drop Failed",
        "left_places": [f"{module} Dropping"],
        "right_places": [f"Order Failed", f"AGV at {module}"],
    }

    return drop_start, drop_succ, drop_fail


def get_action_steps(module, action):
    action_start = {
        "name": f"{module} {action}",
        "left_places": [f"Finish {module} Pick"],
        "right_places": [f"{module} {action}ing"],
    }

    action_succ = {
        "name": f"{module} {action}ed",
        "left_places": [f"{module} {action}ing"],
        "right_places": [f"Start {module} Drop"],
    }

    action_fail = {
        "name": f"{module} {action} Failed",
        "left_places": [f"{module} {action}ing"],
        "right_places": [f"Order Failed"],
    }

    return action_start, action_succ, action_fail


def wrap_invisible_module_start(step):
    inv_step = {
        "name": f"Invisible start {step["name"]}",
        "left_places": [NEXT_MODULE_READY],
        "right_places": [step["left_places"][0]],  # first one is "start" one
    }

    total_step = {
        "type": "InvisibleStep",
        "invisible_prefix_step": inv_step,
        "step": step,
    }

    return total_step


def wrap_invisible_module_end(step):
    # tool only supports prefix naming -> "invisible step" is the
    # real step, suffix is invisible

    inv_step = {
        "name": f"{step["name"]}",
        "left_places": [step["right_places"][0]],  # first one is "Finish" one
        "right_places": [NEXT_MODULE_READY],
    }

    # rename "real" step
    step["name"] = f"Invisible end {step["name"]}"

    total_step = {
        "type": "InvisibleStep",
        "invisible_prefix_step": step,
        "step": inv_step,
    }

    return total_step


###
# AGV steps
###
agv_steps = []

stations = ["HBW", "DPS", "MILL", "DRILL", "AIQS"]
place = lambda s: f"AGV at {s}"

for s in stations:
    for k in stations:
        # pos at s
        # go to k
        if s == k:
            continue

        step = {
            "name": f"AGV move {s} to {k}",
            "left_places": [place(s)],
            "right_places": [place(k)],
        }

        agv_steps.append(step)

# each station should be reach all others
assert len(agv_steps) == len(stations) * (len(stations) - 1)

steps.extend(agv_steps)

###
# HBW steps
###
hbw_pick_start, hbw_pick_succ, hbw_pick_fail = get_pick_steps("HBW")
hbw_drop_start, hbw_drop_succ, hbw_drop_fail = get_drop_steps("HBW")

# pick and drop can be independently executed
hbw_pick_start = wrap_invisible_module_start(hbw_pick_start)
hbw_drop_start = wrap_invisible_module_start(hbw_drop_start)

hbw_pick_succ = wrap_invisible_module_end(hbw_pick_succ)
hbw_drop_succ = wrap_invisible_module_end(hbw_drop_succ)

hbw_steps = [
    hbw_pick_start,
    hbw_pick_succ,
    hbw_pick_fail,
    hbw_drop_start,
    hbw_drop_succ,
    hbw_drop_fail,
]

steps.extend(hbw_steps)

###
# DPS steps
###
dps_pick_start, dps_pick_succ, dps_pick_fail = get_pick_steps("DPS")
dps_drop_start, dps_drop_succ, dps_drop_fail = get_drop_steps("DPS")

# pick and drop can be independently executed
dps_pick_start = wrap_invisible_module_start(dps_pick_start)
dps_drop_start = wrap_invisible_module_start(dps_drop_start)

dps_pick_succ = wrap_invisible_module_end(dps_pick_succ)
dps_drop_succ = wrap_invisible_module_end(dps_drop_succ)

dps_steps = [
    dps_pick_start,
    dps_pick_succ,
    dps_pick_fail,
    dps_drop_start,
    dps_drop_succ,
    dps_drop_fail,
]

steps.extend(dps_steps)

###
# DRILL
###
drill_pick_start, drill_pick_succ, drill_pick_fail = get_pick_steps("DRILL")
drill_drop_start, drill_drop_succ, drill_drop_fail = get_drop_steps("DRILL")
drill_drill_start, drill_drill_succ, drill_drill_fail = get_action_steps(
    "DRILL", "Drill"
)

drill_pick_start = wrap_invisible_module_start(drill_pick_start)
drill_drop_succ = wrap_invisible_module_end(drill_drop_succ)

drill_steps = [
    drill_pick_start,
    drill_pick_succ,
    drill_pick_fail,
    drill_drop_start,
    drill_drop_succ,
    drill_drop_fail,
    drill_drill_start,
    drill_drill_succ,
    drill_drill_fail,
]

steps.extend(drill_steps)

###
# MILL
###
mill_pick_start, mill_pick_succ, mill_pick_fail = get_pick_steps("MILL")
mill_drop_start, mill_drop_succ, mill_drop_fail = get_drop_steps("MILL")
mill_mill_start, mill_mill_succ, mill_mill_fail = get_action_steps(
    "MILL", "Mill"
)

mill_pick_start = wrap_invisible_module_start(mill_pick_start)
mill_drop_succ = wrap_invisible_module_end(mill_drop_succ)

mill_steps = [
    mill_pick_start,
    mill_pick_succ,
    mill_pick_fail,
    mill_drop_start,
    mill_drop_succ,
    mill_drop_fail,
    mill_mill_start,
    mill_mill_succ,
    mill_mill_fail,
]

steps.extend(mill_steps)

###
# AIQS
###
aiqs_pick_start, aiqs_pick_succ, aiqs_pick_fail = get_pick_steps("AIQS")
aiqs_drop_start, aiqs_drop_succ, aiqs_drop_fail = get_drop_steps("AIQS")
aiqs_check_start, aiqs_check_succ, aiqs_check_fail = get_action_steps(
    "AIQS", "Check"
)

aiqs_pick_start = wrap_invisible_module_start(aiqs_pick_start)
aiqs_drop_succ = wrap_invisible_module_end(aiqs_drop_succ)

aiqs_steps = [
    aiqs_pick_start,
    aiqs_pick_succ,
    aiqs_pick_fail,
    aiqs_drop_start,
    aiqs_drop_succ,
    aiqs_drop_fail,
    aiqs_check_start,
    aiqs_check_succ,
    aiqs_check_fail,
]

steps.extend(aiqs_steps)

print(len(steps))

print(json.dumps(steps))


# TODO: Order failed to NEXT_MODULE_READY?
