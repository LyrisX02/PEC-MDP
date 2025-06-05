# PEC-MDP

This repository hosts an implementation of the PEC-MDP. This repository consists of a main Python code file 'PEC_Parser.py' for parsing and translating a PEC domain description into PEC-MDP components, as well as compiling the components into a functioning PEC-MDP. The 'temporal_projection.py' file contains utilities for calculating temporal projections. The 'policy_to_pprops.py' file contains utilities for translating a MDP stationary or non-stationary policy into PEC's p-propositions.

These modules were developed in Python 3.11.2. Requirements include:

* numpy >= 1.24.2
* regex >= 2023.10.3

'PEC_notebook.ipynb' provides a comprehensive tutorial and demonstration of how the utilities of 'PEC_Parser.py' and 'temporal_projection'.

'boxworld.ipynb' consists of a demonstration of how reinforcement learning techniques may be applied to a logistics domain in the PEC-MDP. This also demonstrates how an optimal policy may be translated back to p-propositions through the utilities in 'policy_to_pprops.py'.

This repository also contains examples of PEC domain descriptions showcasing the different properties that may be modelled into a PEC-MDP. These files are found in 'pec_domains/'.

The repository follows the below structure:

```
PEC-MDP/
├── PEC_Parser.py            # Core PEC-MDP translation
├── temporal_projection.py   # Temporal projection calculation
├── policy_to_pprops.py      # Translation of policy to p-propositions
├── notebooks/                   # Jupyter notebooks for demonstrations
│   ├── PEC_notebook.ipynb  # Main notebook for demonstrating the PEC-MDP and temporal projection utilities
│   └── boxworld.ipynb          # BoxWorld domain example for demonstrating objective-directed learning
├── domains/                     # Domain-specific notebooks
│   ├── abstract_domains/        # Abstract/theoretical domains
│   │   ├── domain_syntax_template.txt
│   │   └── decay.txt
│   ├── complex_domains/         # More complex scenarios
│   │   ├── box_world.txt
│   │   ├── box_world_simple.txt
│   │   ├── cooking_robot.txt
│   │   ├── tamogatchi.txt
│   │   ├── tea_making.txt
│   │   └── tuberculosis.txt
│   └── toy_domains/             # Simple domains
│       ├── bacteria.txt
│       ├── coin.txt
│       ├── dice_coin.txt
│       ├── domain_syntax_template.txt
│       └── stairs.txt
└── README.md                   # Project documentation
```



# Syntax Requirements for PEC Domains

As 'PEC_Parser.py' uses predefined regex patterns for matching the text components of a PEC domain, the below requirements must be followed:

For variable names (fluents, values, actions), the regex pattern (\w+) is used, which means naming should follow these conventions:

* Alphanumeric characters (a-z, A-Z, 0-9)
* Underscores (_)
* No spaces, hyphens, or other special characters

Probabilities in i-propositions, c-propositions, and p-propositions may be expressed as integers, fractions or decimals (e.g. 1/2, 0.5).

Any action mentioned in a c-proposition must also be mentioned in a p-proposition as the set of actions is retrieved from p-propositions. For unperformed `action`, please include `action performed at 0 with-prob 0`.

### v-proposition

This defines a fluent and its possible values. The values are comma-separated within curly braces.
```
<fluent> takes-values {<value1>, <value2>, ... ,<valueN>}
```
### i-proposition

Each initial state possibility is enclosed in parentheses and consists of fluent-value assignments for all fluents of a domain enclosed in curly brackets and its corresponding probability.

```
initially-one-of {
  ({<fluent1>=<value1>, <fluent2>=<value2>, ...}, <probability>),
  ({<fluent3>=<value3>, <fluent4>=<value4>, ...}, <probability>),
  ...
}
```
### c-proposition
```
{<fluent1>=<value1>, <fluent2>=<value2>, ..., <action>=true} causes-one-of {
  ({<effect_fluent1>=<effect_value1>, ...}, <probability>),
  ({<effect_fluent2>=<effect_value2>, ...}, <probability>),
  ...
}
```
This defines the effects of actions. The left side specifies the conditions (including the action) that must be true, and the right side specifies the possible outcomes with their probabilities. Each outcome is a set of fluent-value pairs with an associated probability.

### p-proposition

There are four valid formats:

Basic format:

`<action> performed-at <time>`

With probability:

`<action> performed-at <time> with-prob <probability>`

With condition:

`<action> performed-at <time> if-holds {<fluent1>=<value1>, <fluent2>=<value2>, ...}`

With both probability and condition:

`<action> performed-at <time> with-prob <probability> if-holds {<fluent1>=<value1>, <fluent2>=<value2>, ...}`

### time

Default derivation of minimum and maximum instants observes the p-propositions for the first and last instants at which an action may be performed such that the minimum instant is the first instant and the maximum instant is one after the last instant. 

Additional domain specifications may include:
```
minimum instant: <time>
maximum instant: <time>
```
These define the time range for the domain overriding the default derivation.

# Brief Overview on How to Run Core Code

```
import PEC_Parser

# Read domain string
file_path = "../pec_domains/complex_domains/box_world_simple.txt"
file = open(file_path, "r")
domain_string = file.read()

# Instantiate a domain object
domain = PEC_Parser.domain()
# Compute fluents, values, states, and actions as dictionaries for domain object
domain.initialise_all(domain_string)

fluent_dict = domain.fluent_dict
value_dict = domain.value_dict
state_dict = domain.state_dict
action_dict = domain.action_dict

initial_distribution = domain.get_initial(domain_string)
transition_matrix = domain.get_transition(domain_string)
policy_matrix = domain.get_policy(domain_string)
```