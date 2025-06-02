# PEC-MDP

This repository hosts an implementation of the PEC-MDP. The core code translates Probabilistic Event Calculus (PEC) domains to the PEC-MDP framework. The repository follows the below structure:

```
PEC-MDP/
├── PEC_Parser.py            # Core MDP-PEC translation
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


This repository consists of a main Python code file 'PEC_Parser.py' for parsing and translating a PEC domain description into PEC-MDP components, as well as compiling the components into a functioning PEC-MDP. The 'temporal_projection.py' file contains utilities for calculating temporal projections. The 'policy_to_pprops.py' file contains utilities for translating a MDP stationary or non-stationary policy into PEC's p-propositions.

All source code was developed in Python 3.11.2. Requirements include:

* numpy >= 1.24.2
* regex >= 2023.10.3

A comprehensive tutorial and demonstration of how the developed utilities in 'PEC_Parser.py' and 'temporal_projection' may be used is found in the Python notebook 'PEC_notebook.ipynb'.

A demonstration of how reinforcement learning techniques may be applied to a logistics domain in the PEC-MDP can be found in 'boxworld.ipynb'. This also demonstrates how an optimal policy may be translated back to p-propositions through the utilities in 'policy_to_pprops.py'.

This repository also contains examples of PEC domain descriptions showcasing the different properties that may be modelled into a PEC-MDP. These files are form in 'pec_domains/'.
 


# Syntax Requirements for PEC Domains

For a PEC domain to be successfully parsed using the 'PEC_Parser', the below requirements must be followed:

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