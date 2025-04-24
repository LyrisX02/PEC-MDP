import re
from itertools import product
from itertools import chain, combinations
import numpy as np


##############################################
# DEFAULT NATURAL LANGUAGE PATTERNS

v_prop_template = r"(\w+)\s+takes-values\s*{([^}]+)}"
i_prop_template = r"initially-one-of\s*{(.*?)}\s*$"
i_prop_pairs_template = r"\(\s*{((?:[^{}]+(?:,\s*)?)+)},\s*([^)]+)\)"
action_pattern = r"(\w+)\s+performed-at\s+(\d+)"

p_prop_pattern_1 = r"(\w+)\s+performed-at\s+(\d+)"
p_prop_pattern_2 = r"(\w+)\s+performed-at\s+(\d+)\s+with-prob\s+(\d+(?:/\d+|\.\d+)?)"
p_prop_pattern_3 = r"(\w+)\s+performed-at\s+(\d+)\s+if-holds\s+\{([^}]+)\}"
p_prop_pattern_4 = r"(\w+)\s+performed-at\s+(\d+)\s+with-prob\s+(\d+(?:/\d+|\.\d+)?)\s+if-holds\s+\{([^}]+)\}"


c_prop_template = r"""(\{[^}]+\}\s*causes-one-of\s*\{  
    (?:                         
        \s*\(                  
        \s*\{[^}]*\}\s*,        
        \s*(?:\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)\s* 
        \)\s*,?                 
    )+                          
\s*\}) """

body_pattern = r"\{([^}]+)\}\s*causes-one-of"
outcome_template = r"\(\s*\{([^}]*)\}\s*,\s*(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)\s*\)"

min_template = "minimum instant: (-?\d+)"
max_template = "maximum instant: (-?\d+)"

#############################################

# FLUENT, VALUE, STATE, AND OTHER INITIAL DICTIONARIES

class domain():
    def __init__(self):
        self.fluent_dict = {}
        self.value_dict = {}
        self.state_dict = {}
        self.action_dict = {}
        self.sim_act_dict = {}
        self.reverse_joined_action_dict = {}
        self.max_instant = 0
        self.time_difference = 0
        
    def initialise_all(self, domain_string):
        '''
        This function takes the entire PEC domain string as input.
        ---
        Output in format of fluent_dict, value_dict, state_dict
        '''
######## STATES
        v_prop_matches = re.findall(v_prop_template, domain_string, re.DOTALL | re.MULTILINE)
        
        # Retrieve fluents 
        fluents = [prop[0] for prop in v_prop_matches]
        self.fluent_dict = {fluent: i for i, fluent in enumerate(fluents)}

        # Retrive values 
        values = [[item.strip(",") for item in prop[1].split()] for prop in v_prop_matches]
        value_set = []
        for value in list(chain(*values)):
            if value not in value_set:
                value_set.append(value)
        self.value_dict = {value: i for i, value in enumerate(value_set)}

        # Define states
        encoded_values = [[self.value_dict[v] for v in val] for val in values]
        state_combinations = list(product(*encoded_values))
        self.state_dict = {combo: i for i, combo in enumerate(state_combinations)}
        
######## ACTIONS
        action_matches = re.findall(action_pattern, domain_string)
        
        # Dictionary contains the possible actions at each time instant
        time_to_actions = {}
        for action, time in action_matches:
            if time not in time_to_actions:
                time_to_actions[time] = set()
            time_to_actions[time].add(action)

        # Find simultaneous actions including all subsets
        simultaneous_actions = []
        simultaneous_actions_time = []
        for actions in time_to_actions.values():
            action_combos = list(chain.from_iterable(combinations(actions, r) for r in range(2, len(actions) + 1)))
            simultaneous_actions_time.append(action_combos)
            for combo in action_combos:
                if list(combo) not in simultaneous_actions:
                    simultaneous_actions.append(list(combo))
        
        joined_actions = [" and ".join(i) for i in simultaneous_actions]
        
        # Get single actions, we want singles to be at the start of the action dict
        actions = [p_prop[0] for p_prop in action_matches]
        action_set = list(set(actions))
        
        # Create complete action dictionary
        self.action_dict = {value: i for i, value in enumerate(action_set+joined_actions)}
        self.action_n = len(self.action_dict)
        self.action_dict["null"] = self.action_n
        
        # Calculate dictionary of encoded action combinations mapping to simultaneous actions
        # Shows a mapping between integer encoded combined actions and their components
        for joined in joined_actions:
            key = self.action_dict[joined]
            value = [self.action_dict[single] for single in joined.split(" and ")]
            self.sim_act_dict[key] = value
        self.reverse_joined_action_dict = {frozenset(v): k for k, v in self.sim_act_dict.items()}

        
######## TIME

        # Get minimum and maximum time instants 
        times = [int(match[1]) for match in action_matches]

        minimum_match = re.search(min_template, domain_string)
        maximum_match = re.search(max_template, domain_string)

        # If domain contains explicit instants
        # Else, retrieve instants from p-proposition times
        if minimum_match:
            minimum_instant = int(minimum_match.group(1))
        else:
            minimum_instant = min(times)
            
        if maximum_match:
            maximum_instant = int(maximum_match.group(1))
        else:
            maximum_instant = max(times) + 1
        
        # Set max instant to number of instants in domain
        self.max_instant = maximum_instant - minimum_instant
        
        # Get difference between MDP max instant and domain max instant
        self.time_difference = maximum_instant - self.max_instant

        return(self.fluent_dict, self.value_dict, self.state_dict, self.action_dict)

#############################################

# USEFUL FUNCTIONS FOR PROCESSING PARTIAL FLUENTS AND STATES


    def literal_to_encoded(self, fluent_state):
        """_summary_

        Args:
            fluent_state (_type_): string containing full fluent state
        """
        fluents = re.findall(r"(\w+)\s*=\s*(\w+)", fluent_state)
        
        # Order by cannonical order
        ordered_fluents = sorted(fluents, key=lambda x: self.fluent_dict[x[0]])
        
        # Encode through value dictionary
        state = tuple(self.value_dict[fluent[1]] for fluent in ordered_fluents)
        
        # Retrieve integer encoding from state dictionary
        int_state = self.state_dict[state]
        
        return(int_state)

    def partial_to_states(self, partial_fluent):
        """_summary_

        Args:
            partial_fluent (_type_): string containing partial fluent state
        """
        # Split partial string into fluents
        fluents = [i.strip() for i in partial_fluent.split(",")]
        
        # Encode fluents as integers
        fluent_integers = []
        for fluent in fluents:
            fluent_components = fluent.split("=")
            fluent_index = self.fluent_dict[fluent_components[0]]
            value_index = self.value_dict[fluent_components[1]]
            fluent_integers.append([fluent_index, value_index])
            
        # Append states which meet condition
        possible_fluent_states = []
        for key, value in self.state_dict.items():
            condition_met = all(key[fluent_int[0]]==fluent_int[1] for fluent_int in fluent_integers)
            if condition_met:
                possible_fluent_states.append(value)
                
        return(possible_fluent_states)



    def update_fluent_state(self, current_state, partial_fluent):
        """_summary_

        Args:
            current_state (_type_): integer encoded state (type integer and not tuple)
            partial_fluent (_type_): string containing partial fluent state
        """
        # Retrieve current state as a vector of values
        reverse_state_dict = {v: k for k, v in self.state_dict.items()}
        current_state_vector = reverse_state_dict[current_state]
        
        # Process partial string
        if type(partial_fluent) == str:
            fluents = [i.strip() for i in partial_fluent.split(",")]
        else:
            fluents = partial_fluent
            
        # Create dictionary of partial fluents as fluent_index: value_index
        fluent_integers = []
        for fluent in fluents:
            fluent_components = [i.replace(" ", "") for i in fluent.split("=")]
            fluent_index = self.fluent_dict[fluent_components[0]]
            value_index = self.value_dict[fluent_components[1]]
            fluent_integers.append([fluent_index, value_index])
        partial_dict = dict(fluent_integers)

        # Get the updated state
        updated_state = []
        for i in range(len(current_state_vector)):
            if i in partial_dict.keys():
                updated_state.append(partial_dict[i])
            else:
                updated_state.append(current_state_vector[i])
        final_state = self.state_dict[tuple(updated_state)]
        
        return(final_state)

    
    def translate_int_to_lit(self, integer_state):
        """_summary_

        Args:
            integer_state (_type_): integer encoded fluent state
        """
        # Get reverse dictionaries
        reverse_state_dict = {v: k for k, v in self.state_dict.items()}
        reverse_value_dict = {v: k for k, v in self.value_dict.items()}
        
        # Translate integer state back into fluent representation
        tuple_state = reverse_state_dict[integer_state]
        state_string = []
        for i in range(len(tuple_state)):
            fluent = list(self.fluent_dict.keys())[i]
            value = reverse_value_dict[tuple_state[i]]
            state_string.append(fluent+"="+value)
        return(",".join(state_string))
            
######################################

# DEFINE MDP COMPONENTS 

    def get_initial(self, domain_string):
        i_prop_match = re.search(i_prop_template, domain_string, re.DOTALL | re.MULTILINE)
        
        if i_prop_match:
            content = i_prop_match.group(1)
            # Extract individual state-probability pairs
            pairs = re.findall(i_prop_pairs_template, content)
            encoded_literal = [self.literal_to_encoded(pair[0]) for pair in pairs]
            try: 
                initial_probs = [float(pair[1]) for pair in pairs] # If probability is decimal
            except:
                probs_as_fractions = [pair[1].split("/") for pair in pairs] # If probability is fraction
                initial_probs = [int(num[0]) / int(num[1]) for num in probs_as_fractions]
                
        return(encoded_literal, initial_probs)


    def get_policy(self, domain_string):
        # 4 types of p-propositions
        p_prop_matches_1 = re.findall(p_prop_pattern_1, domain_string) 
        p_prop_matches_2 = re.findall(p_prop_pattern_2, domain_string) 
        p_prop_matches_3 = re.findall(p_prop_pattern_3, domain_string)
        p_prop_matches_4 = re.findall(p_prop_pattern_4, domain_string)

        # Get identities of p-props type 2 and 3 
        overlap_prop_1 = [(match[0], match[1]) for match in p_prop_matches_2 + p_prop_matches_3]
        overlap_prop_2 = [(match[0], match[1], match[2]) for match in p_prop_matches_4]
        # Remove overlapping p-props found
        p_prop_matches_1_cleaned = [match for match in p_prop_matches_1 if match not in overlap_prop_1]
        p_prop_matches_2_cleaned = [match for match in p_prop_matches_2 if match not in overlap_prop_2]


        # P-proposition with the form: A performed-at I
        p_prop_1 = []
        for prop in p_prop_matches_1_cleaned:
            action = self.action_dict[prop[0]]
            instant = int(prop[1]) + self.time_difference
            prob = 1
            states = list(self.state_dict.values())
            p_prop_1.append((action, instant, prob, states))

        # P-proposition with the form: A performed-at I with-prob P
        p_prop_2 = [] 
        for prop in p_prop_matches_2_cleaned:
            action = self.action_dict[prop[0]]
            instant = int(prop[1]) + self.time_difference
            try:
                prob = float(prop[2])
            except:
                fraction = prop[2].split("/")
                prob = int(fraction[0]) / int(fraction[1])
            states = list(self.state_dict.values())
            p_prop_2.append((action, instant, prob, states))
            
        # P-proposition with the form: A performed at I if-holds X
        p_prop_3 = [] 
        for prop in p_prop_matches_3:
            action = self.action_dict[prop[0]]
            instant = int(prop[1]) + self.time_difference
            prob = 1
            states = self.partial_to_states(prop[2])
            p_prop_3.append((action, instant, prob, states))

        # P-proposition with the form: A performed at I with-prob P if-holds X
        p_prop_4 = [] 
        for prop in p_prop_matches_4:
            action = self.action_dict[prop[0]]
            instant = int(prop[1]) + self.time_difference
            try:
                prob = float(prop[2])
            except:
                fraction = prop[2].split("/")
                prob = int(fraction[0]) / int(fraction[1])
            states = self.partial_to_states(prop[3])
            p_prop_4.append((action, instant, prob, states))
            
        all_p_props = p_prop_1 + p_prop_2 + p_prop_3 + p_prop_4

        # Create policy matrix 
        policy_matrices = []
        # Iterate over time instants
        for instant in range(self.max_instant+1):
            
            # Create temporary matrix action * state for each time instant
            temp_matrix = [[0 for _ in range(len(self.action_dict))] for _ in range(len(self.state_dict))]
            # Identify all p-propositions at that instant
            current_p_props = [i for i in all_p_props if i[1] == instant]
            for prop in current_p_props:
                for s in prop[3]: # For each state
                    temp_matrix[s][prop[0]] += prop[2] # Add probability 

            matrix = []
            
            # Iterate through each state row
            for state_row in temp_matrix:
                new_row = [0 for _ in range(len(state_row))]
                action_prob = {} # Dictionary for possible actions and their probabilities
                for action in range(len(state_row)):
                    if state_row[action] != 0:
                        action_prob[action] = state_row[action]
                
                # If there are simultaneous actions
                if len(action_prob) > 1:
                    # Process possible combined actions
                    possible_actions = list(action_prob.keys())
                    # Get all possible action combinations
                    combos = list(chain.from_iterable(combinations(possible_actions, r) for r in range(2, len(possible_actions) + 1)))
                    # Iterate through combinations
                    for c in combos:
                        combo = frozenset(c)
                        combo_state = self.reverse_joined_action_dict[combo] # Integer combined action state
                        combo_prob = np.prod([action_prob[a] for a in combo]) # Product of probabilities 
                        if combo_prob > 1: # Restrict upper threshold
                            combo_prob = 1
                        # Add the calculated combined probability to the new row
                        new_row[combo_state] += combo_prob
                    
                    # Process single actions 
                    for current_action, current_prob in action_prob.items():
                        non_occurance_probs = []
                        # Get probabilities of other actions not happening
                        for other_action, other_prob in action_prob.items():
                            if other_action != current_action:
                                non_occurance_probs.append(1-other_prob)
                        # Calculate single action probability
                        single_prob = current_prob * np.prod(non_occurance_probs)
                        # Add the calculated independent probability to the new row
                        new_row[current_action] += single_prob
                        
                # If there are no simultaneous actions
                elif len(action_prob) == 1:
                    only_key, only_value = list(action_prob.items())[0]
                    new_row[only_key] += only_value
                
                # Process null actions
                current_sum = sum(new_row)
                if current_sum < 1:
                    new_row[-1] += (1-current_sum)
                    
                matrix.append(new_row)
                        
            policy_matrices.append(matrix)

            
        return(policy_matrices)
            

    def get_transition(self, domain_string):
        
        # Find all c-proposition matches in domain string
        c_prop_match = re.findall(c_prop_template, domain_string, re.VERBOSE | re.DOTALL)
        match_probs = [] # Create overall container for the conditions of each c-prop
        partial_container = [] # Create a container for partial fluents
        
        # Parse through each c-proposition
        for match in c_prop_match:
            

            # Body parsing 
            body = re.search(body_pattern, match)
            body = body.group(1)
            body_components = [i.strip() for i in body.split(",")]
            # Retrieve action(s) and partial fluent conditions
            temporary_body_action = []
            body_partial = []
            for component in body_components:
                if any(action_key in component.split("=") for action_key in self.action_dict.keys()):
                    action = component.split("=")
                    if action[1] == "true":
                        temporary_body_action.append(self.action_dict[action[0]])
                else:

                    body_partial.append(component)

            # Retrieve all possible current states based on partial fluent conditions
            if body_partial:
                body_partial_string = ",".join(body_partial)
                body_current_state = self.partial_to_states(body_partial_string)
            else:
                body_current_state = list(self.state_dict.values())
                
            if len(temporary_body_action) > 1:
                body_action = self.reverse_joined_action_dict[frozenset(temporary_body_action)]
            else:
                body_action = temporary_body_action[0]
            
########          
            # Outcome parsing
            outcomes = re.findall(outcome_template, match) 
            outcome_state = [] 
            outcome_state_prob = []
            
            # Add partial fluents of effect to container
            partial_container.append([outcome[0] for outcome in outcomes])

            for outcome in outcomes:
                
                partial_fluent = outcome[0]
                probability_string = outcome[1]
                updated_state = []
                # Process updated state for each potential current state
                for current_state in body_current_state:
                    if partial_fluent:
                        updated_state.append(self.update_fluent_state(current_state, partial_fluent))
                    else:
                        updated_state.append(current_state)
                    
                outcome_state.append(updated_state)
                
                # Process outcome probability
                try: 
                    probability = float(probability_string)
                    outcome_state_prob.append(probability)
                except:
                    probability = probability_string.split("/")
                    probability = float(probability[0]) / float(probability[1])
                    outcome_state_prob.append(probability)
                    
            # Append all components for detailed c-proposition effects
            match_probs.append([body_action, body_current_state, outcome_state, outcome_state_prob])

########
    # Put into matrix form
        transition_matrices = []
        
        # Loop through each action
        for action in list(self.action_dict.values()):
            # Find matches for an action
            action_match = [match for match in match_probs if action == match[0]]
            # Initialise state by state matrix
            matrix = [[0 for _ in range(len(self.state_dict))] for _ in range(len(self.state_dict))]
            for match in action_match:
                for p in range(len(match[-1])): # Loop through outcomes/probabilities
                    for s in range(len(match[1])): # Loop through state combinations
                        current = match[1][s]
                        next = match[2][p][s]
                        prob = match[-1][p]
                        matrix[current][next] += prob
            # For each row without transitional effects, it takes the form of an identity matrix 
            for row in range(len(matrix)):
                if sum(matrix[row]) == 0:
                    matrix[row][row] += 1
            # Append each action's (state * state) matrix to overall matrix
            transition_matrices.append(matrix)
        
        return(transition_matrices)

########################################################################################


class pecmdp:
    def __init__(self, states, actions, transition_probs, initial_probs):
        self.states = states
        self.actions = actions
        self.transition_probs = transition_probs
        self.initial_probs = initial_probs
        self.reset() 
        
    def step(self, current_state, action):
        probs = self.transition_probs[action][current_state]
        probs = probs / np.sum(probs) # Normalise
        next_state = np.random.choice(self.states, p=probs)
        return next_state

    def reset(self):
        self.current_state = np.random.choice(self.initial_probs[0], p=self.initial_probs[1])
        return self.current_state
    
    def sample_trajectory(self, n_steps, policy):
        trajectory = [self.reset()]  # Start with the initial state from reset

        for step in range(n_steps):
            action = np.random.choice(self.actions, p=policy[step][self.current_state])
            next_state = self.step(self.current_state, action)
            trajectory.append(next_state)
            self.current_state = next_state

        return trajectory