import PEC_Parser
import numpy as np

def calculate_temporal_query(file_path, query_time, query_literal, conditions):
    """_summary_

    Args:
        file_path (string): _description_
        query_time (int): _description_
        query_literal (string): _description_
        conditions (list containing tuples (int, string)): _description_
    """
    # Read string
    file = open(file_path, "r")
    domain_string = file.read()

    # Create dictionary of conditions
    conditions_dict = {time: condition for time, condition in conditions}
    
    # Instantiate a domain object
    domain = PEC_Parser.domain()

    # Compute fluents, values, states, and actions as dictionaries for domain object
    domain.initialise_all(domain_string)
    initial_distribution = domain.get_initial(domain_string)
    transition_matrix = domain.get_transition(domain_string)
    policy_matrix = domain.get_policy(domain_string)
    n_steps = domain.max_instant
    state_dict = domain.state_dict
    action_dict = domain.action_dict

    # Cast transition matrix as array
    T = np.array(transition_matrix)

    # Replace empty policy (in finished states) with null action
    policy_container = []
    for policy in policy_matrix:
        Pi_matrix = np.array([[0.0]*(len(action_dict)-1)+[1.0] if i == [] else i for i in policy])
        #print("policy shape:", Pi_matrix.shape)
        policy_container.append(Pi_matrix)
        
    # T starts (A, S, S'), make it (S', S, A)
    T_reshaped = np.transpose(T, (2, 1, 0))

    # Define starting state probs as vector array
    S = np.zeros(len(state_dict))
    for i in range(len(initial_distribution[0])):
        S[initial_distribution[0][i]] = initial_distribution[1][i]

    # Define list containing state vectors
    states_at_instant = [S]

    # Iterate
    current = S
    for i in range(n_steps):
        # Flatten policy matrix
        # policy has shape (S, A)
        policy_flat = policy_container[i].reshape(-1)
        S_reshaped = current.reshape(1, -1, 1)
        # Multiply together to scale probabilities based on starting probabilities
        T_matrix = T_reshaped * S_reshaped

        # Reshape T_matrix to prepare for dot product with policy
        T_matrix = T_matrix.reshape(T_matrix.shape[0], -1)
        next_state_probs = np.dot(T_matrix, policy_flat)
        
        # Weight state probabilities with condition
        if i in list(conditions_dict.keys()):
            partial = conditions_dict[i]
            states_associated = list(set(domain.partial_to_states(partial)))
            indicator_vector = np.zeros(len(state_dict), dtype=int)
            indicator_vector[states_associated] = 1
            next_state_probs = np.multiply(next_state_probs, indicator_vector)
            next_state_probs = next_state_probs / np.sum(next_state_probs)
        states_at_instant.append(next_state_probs)
        current = next_state_probs
        
    states_associated = set(domain.partial_to_states(query_literal))
    return(sum([states_at_instant[query_time][i] for i in states_associated]))