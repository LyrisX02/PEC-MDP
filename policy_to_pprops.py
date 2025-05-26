import PEC_Parser
import numpy as np 

def find_minimal_discriminators(tuples):
    if not tuples:
        return {}
    
    # Create a dictionary to store result
    result = {}
    
    # Get the length of tuples
    tuple_len = len(tuples[0])
    
    for current_tuple in tuples:
        # Start with an empty discriminator
        discriminator = {}
        
        # Try adding one position at a time until we have a unique identifier
        for position in range(tuple_len):
            # Add this position to our discriminator
            discriminator[position] = current_tuple[position]
            
            # Check if this discriminator is unique
            is_unique = True
            for other_tuple in tuples:
                if current_tuple == other_tuple:
                    continue
                
                # Check if the other tuple matches our discriminator on all positions
                matches = True
                for pos, val in discriminator.items():
                    if other_tuple[pos] != val:
                        matches = False
                        break
                
                if matches:
                    is_unique = False
                    break
            
            if is_unique:
                # We found a minimal discriminator
                result[current_tuple] = discriminator
                break
                
    return result.values()

def translate_pprops(file_path, policy):
    
    file = open(file_path, "r")
    domain_string = file.read()
    # Instantiate a domain object
    domain = PEC_Parser.domain()
    domain.initialise_all(domain_string)
    
    state_dict = domain.state_dict
    reverse_state_dict = {v: k for k, v in state_dict.items()}
    action_dict = domain.action_dict
    reverse_action_dict = {v: k for k, v in action_dict.items()}
    value_dict = domain.value_dict
    reverse_value_dict = {v: k for k, v in value_dict.items()}
    fluent_dict = domain.fluent_dict
    reverse_fluent_dict = {v: k for k, v in fluent_dict.items()}

    # Define dictionaries of integer states and literals
    full_state_dict = {}
    reversed_full_state_dict = {}
    for i in range(len(state_dict)):
        full_state_dict[i] = domain.translate_int_to_lit(i)
        reversed_full_state_dict[domain.translate_int_to_lit(i)] = i
        
    initial_distribution = domain.get_initial(domain_string)
    transition_matrix = domain.get_transition(domain_string)
    #n_steps = domain.max_instant

    states = list(state_dict.values())
    actions = list(action_dict.values())
    
    
    # Cast transition matrix as array
    T = np.array(transition_matrix)
    print("transition shape:", T.shape)

    # Replace empty policy (in finished states) with null action
    Pi_matrix = np.array([[0.0]*(len(action_dict)-1)+[1.0] if i == [] else i for i in list(policy.values())])
    print("policy shape:", Pi_matrix.shape)

    # T starts (A, S, S'), make it (S', S, A)
    T_reshaped = np.transpose(T, (2, 1, 0))

    # Flatten policy matrix
    # policy has shape (S, A)
    policy_flat = Pi_matrix.reshape(-1)

    # Define starting state probs as vector array
    S = np.zeros(len(state_dict))
    for i in range(len(initial_distribution[0])):
        S[initial_distribution[0][i]] = initial_distribution[1][i]

    # Define list containing state vectors
    states_at_instant = [S]

    # Iterate
    current = S
    for i in range(14):
        S_reshaped = current.reshape(1, -1, 1)
        # Multiply together to scale probabilities based on starting probabilities
        T_matrix = T_reshaped * S_reshaped

        # Reshape T_matrix to prepare for dot product with policy
        T_matrix = T_matrix.reshape(T_matrix.shape[0], -1)
        next_state_probs = np.dot(T_matrix, policy_flat)
        states_at_instant.append(next_state_probs)
        current = next_state_probs
    
    # Cast transition matrix as array
    T = np.array(transition_matrix)


    # Replace empty policy (in finished states) with null action
    Pi_matrix = np.array([[0.0]*(len(action_dict)-1)+[1.0] if i == [] else i for i in list(policy.values())])

    all_p_props = []

    # Outer loop: for each instant
    for instant in range(len(states_at_instant)):
        # Define lists for states, actions and probs performed each instant
        states = []
        actions = []
        probs = []
        # For each state that possible at an instant
        for s in range(len(states_at_instant[instant])):
            if states_at_instant[instant][s] != 0:
                
                # For each action that may be taken at each possible state
                for a in range(len(policy[s])):
                    if policy[s][a] != 0:
                        
                        # Append the state and the corresponding action
                        states.append(reverse_state_dict[s])
                        actions.append(a)
                        probs.append(policy[s][a])
                        #print(reverse_state_dict[s])
                        #print(f"{reverse_action_dict[a]} performed-at {instant} with-probs {policy[s][a]} if-holds {full_state_dict[s]}")

        # When there is only one possible state at an instant
        if len(states) == 1:
            action = reverse_action_dict[actions[0]]
            prob = probs[0]
            all_p_props.append(f"{action} performed-at {instant} with-prob {prob}")
            
        # When multiple states are possible at an instant
        # reduce number of literals through mining minimally strict sets
        else:         
        # Calculate minimally strict sets at each instant
            minimal_sets = list(find_minimal_discriminators(states))
            # Convert to fluent and value
            for i in range(len(minimal_sets)):
                state_string = ",".join(["=".join([reverse_fluent_dict[key], reverse_value_dict[value]]) for key, value in minimal_sets[i].items()])
                action = reverse_action_dict[actions[i]]
                prob = probs[i]
                all_p_props.append(f"{action} performed-at {instant} with-prob {prob} if-holds {state_string}")
                
    filename = "p_propositions.txt"

    with open(filename, 'w', encoding='utf-8') as file:
        file.write("\n".join(all_p_props))
        
    return()