from collections import defaultdict
import json
import argparse

### Step class defines a single step in the equivalence checking process.
class Step:
    def __init__(self, name, left_places, right_places):
        self.name = name
        self.left_places = left_places
        self.right_places = right_places


# Since we have invisible steps (steps that are modelled, but not in the original runs),
# and we know exactly when they must exist 
# (e.g. before a Mill Pick there must have been a Control step mapping the Drill Drop to it)
# These steps are not dynamically added to the runs, but can be added to the suffix steps

def InvisibleStep(invisible_prefix_step, step):
    # merge matching right places of invisble into left of step - removing them from the total new step, keep remaining
    invisible_right_places = invisible_prefix_step.right_places
    step_left_places = step.left_places

    new_left_places = invisible_prefix_step.left_places
    new_right_places = step.right_places


    for place in invisible_right_places:
        if not place in step_left_places:
            new_right_places.append(place)

    for place in step_left_places:
        if not place in invisible_right_places:
            new_left_places.append(place)

    return Step(step.name, new_left_places, new_right_places)

def parse_step(json_data):
    if "type" in json_data.keys() and json_data["type"] == "InvisibleStep":
        invisible_prefix_step = parse_step(json_data["invisible_prefix_step"])
        step = parse_step(json_data["step"])
        return InvisibleStep(invisible_prefix_step, step)
    else:
        return Step(json_data["name"], json_data["left_places"], json_data["right_places"])

def parse_steps_from_file(file_path):
    steps = []
    with open(file_path, "r") as f:
        json_data = json.load(f)
        for step_data in json_data:
            steps.append(parse_step(step_data))
    return steps

def step_list_to_dict(step_list):
    step_dict = {}
    for step in step_list:
        if step.name in step_dict:
            raise ValueError(f"Duplicate step name: {step.name}")
        step_dict[step.name] = step
    return step_dict

### To build the reference run, we 
### 1.  build a directed graph of the steps using the composition calculus, 
###     explicitely storing all steps without any previous steps as intial states
### 2.  build the same graph for the second run
### 3.  Check whether the second graph is a subgraph of the first graph, i.e. whether all steps in the second graph are also in the first graph, and whether all edges in the second graph are also in the first graph


def build_graph_from_run(step_names, step_dict):
    # build graph -> probably sparse, use dict of lists
    next_graph_index = 0
    graph = defaultdict(list) # map of index to tuple(step, list of next step indicees)
    initial_steps = [] # list of initial step indicee
    unused_right_places = defaultdict(list) # map of place to list of graph step indicee that have this place as the right place, but are not yet connected to a next step

    debug_unused_left_places = defaultdict(list) # map of place to list of steps that have this place on the left side but not connected to anything, should just contain initial trigger places in the end

    for step_name in step_names:
        if not step_name in step_dict:
            raise ValueError(f"Step {step_name} is not defined in the step definitions")
        step = step_dict[step_name]
        graph[next_graph_index] = (step, [])
        
        consumed = 0

        # consume as many unused right places as possible, then connect them to the current step
        for place in step.left_places:
            if place in unused_right_places.keys() and len(unused_right_places[place]) > 0:
                prev_step_index = unused_right_places[place].pop(0)
                graph[prev_step_index][1].append(next_graph_index)
                consumed += 1
            else:
                debug_unused_left_places[place].append(next_graph_index)
                continue
        
        # initial step if there is no predecessor step
        if consumed == 0:
            initial_steps.append(next_graph_index)
        
        # expose the right places of the current step as unused
        for place in step.right_places:
            unused_right_places[place].append(next_graph_index)

        next_graph_index += 1
    
    for place, step_indices in debug_unused_left_places.items():
        # if there are still unused left places that are not part of the initial steps
        if len(step_indices) > 0 and not all([index in initial_steps for index in step_indices]):
            print(f"Warning: place {place} is a left place of steps {list(map(lambda x: graph[x][0].name, step_indices))} but is not consumed by any step")

    # we assume that every initial step is a unique step, i.e. that there are no two initial steps with the same name
    assert len(set([graph[index][0].name for index in initial_steps])) == len(initial_steps), "There are multiple initial steps with the same name, this is not supported"

    return graph, initial_steps

def display_graph(graph):
    # plot the graph using graphviz, with the step names as labels and the edges as arrows
    from graphviz import Digraph
    dot = Digraph()
    dot.attr('node', shape='rect')
    graph, initial_steps = graph
    for index, (step, next_steps) in graph.items():
        dot.node(str(index), step.name)
        for next_step in next_steps:
            dot.edge(str(index), str(next_step))
    return dot

def print_graph(graph):
    graph, initial_steps = graph
    for index, (step, next_steps) in graph.items():
        print(f"Step {index}: {step.name}, next steps: {[next_step for next_step in next_steps]}")
    
    for initial_step in initial_steps:
        print(f"Initial step:  {graph[initial_step][0].name}")

# steps of the same name are the same, so no further checks necessary
def is_subgraph(graph1, graph2):
    graph1, initial_steps1 = graph1
    initial_steps1 = list(initial_steps1)
    graph2, initial_steps2 = graph2
    initial_steps2 = list(initial_steps2)

    further_checks = [] # list of tuples of step indices (step_index1, step_index2) that need to be checked for their next steps
    already_checked = set() # set of tuples of step indices already checked
    # check initial steps are contained
    for step in initial_steps1:
        step_name = graph1[step][0].name

        for step2 in initial_steps2:
            if graph2[step2][0].name == step_name:
                further_checks.append((step, step2))
                already_checked.add((step, step2))
                initial_steps2.remove(step2)
                break
        else: 
            # executed if no break was executed
            print(f"Initial step {step_name} is not contained in the reference graph")
            return False

    # for (step1, step2) in further_checks:
    #     print(f"Initial step pair {step1}-{step2}: {graph1[step1][0].name} is contained in the reference graph, checking next steps...")

    # print("Reference graph:")
    # print_graph((graph2, initial_steps2))

    # print("Check graph:")
    # print_graph((graph1, initial_steps1))
    
    # check graph2 contains graph1 -> performs BFS through graph1
    while len(further_checks) > 0:
        step_index1, step_index2 = further_checks.pop(0)
        step1, next_steps1 = graph1[step_index1]
        step2, next_steps2 = graph2[step_index2]

        for next_step1 in next_steps1:
            next_step_name1 = graph1[next_step1][0].name

            for next_step2 in next_steps2:
                if graph2[next_step2][0].name == next_step_name1:
                    if (next_step1, next_step2) not in already_checked:
                        further_checks.append((next_step1, next_step2))
                        already_checked.add((next_step1, next_step2))
                    next_steps2.remove(next_step2)
                    break
            else: 
                # executed if no break was executed
                print(f"Step {next_step_name1} is not contained in the reference graph after step {step1.name}")

                # print(f"\nRef graph next steps: {[graph2[next_step][0].name for next_step in next_steps2]}")
                # print(f"Check graph next steps: {[graph1[next_step][0].name for next_step in next_steps1]}")
                return False
    
    return True


def check_equivalence(ref_run_steps, check_run_steps, step_dict, display=False):
    graph2 = build_graph_from_run(ref_run_steps, step_dict)
    graph1 = build_graph_from_run(check_run_steps, step_dict)

    if display:
        display_graph(graph1).render("check_graph", format="png")
        display_graph(graph2).render("reference_graph", format="png")

    return is_subgraph(graph1, graph2)

def check_equivalence_step_file(ref_run_steps, check_run_steps, step_file, display=False):
    step_dict = step_list_to_dict(parse_steps_from_file(step_file))
    return check_equivalence(ref_run_steps, check_run_steps, step_dict, display)

if __name__ == "__main__":
    # use argparse to get the file paths of the two runs and the file path of the step defs
    parser = argparse.ArgumentParser(description="Check whether two runs are equivalent according to the composition calculus")
    parser.add_argument("ref_run", help="File path of the reference run")
    parser.add_argument("check_run", help="File path of the run to check")
    parser.add_argument("steps", help="File path of the step definitions")
    parser.add_argument("--display", action="store_true", help="Display the graphs of the runs")
    args = parser.parse_args()

    with open(args.ref_run, "r") as f:
        ref_run_steps = f.readall().split(" ")
    with open(args.check_run, "r") as f:
        check_run_steps = f.readall().split(" ")
    
    if check_equivalence_step_file(ref_run_steps, check_run_steps, args.steps, display=args.display):
        print("The run is a prefix of the reference run")
    else:
        print("The runs don't match")


