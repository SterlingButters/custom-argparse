import sys, os
from collections import OrderedDict
import json
import glob
import subprocess

#### NOTES: equal operator must not have a space e.g. 'test=name' not 'test= name' or 'test = name'
#           can assign params to short/long args using equal operator but there must be a space (delimiters still apply) e.g '-t= example' or '--test= example'
#           no support for combined short args e.g. must do '-a -b -c param' not '-abc param'
#                    all short args are single letter. can assume that '-' with more than one character is combined short args (treat string as a list)
#           no support for non-space delimiters e.g. must do '-A param1 param2 param3' not '-A param1,param2,param3'
#           positionals starting with '-', '--', or containing '=' must have quotes in bash "'-positional'"
#           assignment operator (=) not customizable at the moment

ARG_SET1 = OrderedDict()

ARG_SET1["nodes"] = {"invocations": ("-n", "--nodes"),
                     "required": False,
                     "n-params": 1, # or True/False for Boolean Flag
                     "n-delimiter": " ",
                     "valid-types": [int],
                     "choices": [],
                     "default": 200,
                     "description": "Submits a parallel job and specifies the number of tasks in the job.",
                     "params": None
                    }

ARG_SET1["resource"] = {"invocations": ("-R", "--req_res"),
                     "required": False,
                     "n-params": 0, # or True/False for Boolean Flag
                     "n-delimiter": " ",
                     "valid-types": [str],
                     "choices": [],
                     "default": None,
                     "description": "Runs the job on a host that meets the specified resource requirements. E.g. 'span[ptile=28]'",
                     "params": None
                    }

ARG_SET1["job-name"] = {"invocations": ("-J", "--job_name"),
                     "required": False,
                     "n-params": 0, # or True/False for Boolean Flag
                     "n-delimiter": " ",
                     "valid-types": [str],
                     "choices": [],
                     "default": None,
                     "description": "Display name of the LSF job in queue. Limit to 10 chars.",
                     "params": None
                    }

ARG_SET1["error-file"] = {"invocations": ("-eo", "--error_file"),
                     "required": False,
                     "n-params": 0, # or True/False for Boolean Flag
                     "n-delimiter": " ",
                     "valid-types": [str],
                     "choices": [],
                     "default": None,
                     "description": "Overwrites the standard error output of the job to the specified file path.",
                     "params": None
                    }

ARG_SET1["output-file"] = {"invocations": ("-oo", "--output_file"),
                     "required": False,
                     "n-params": 0, # or True/False for Boolean Flag
                     "n-delimiter": " ",
                     "valid-types": [str],
                     "choices": [],
                     "default": None,
                     "description": "Controls the propagation of the specified job submission environment variables to the execution hosts.",
                     "params": None
                    }

ARG_SET1["queue"] = {"invocations": ("-q", "--queue_name"),
                     "required": False,
                     "n-params": '?', # or True/False for Boolean Flag
                     "n-delimiter": " ",
                     "valid-types": [str],
                     "choices": ["normal", "sentinel"],
                     "default": "normal",
                     "description": "Submits the job to one of the specified queues.",
                     "params": None
                    }

# ARG_SET1["positional"] = {"invocations": (None), # Indicates positional argument
#                           "required": False,
#                           "description": "",
#                           "valid-types": [],
#                           "choices": [],
#                           "description": "",
#                          }

ARG_SET2 = OrderedDict()

ARG_SET2["name"] = {"invocations": ("name",),
                    "required": False,
                    "n-params": 0, # or True/False
                    "n-delimiter": None,
                    "valid-types": [str],
                    "choices": [],
                    "default": None,
                    "description": "Glob-compatible path to the MCNP input file",
                    "params": None
                    }

ARG_SET2["particles"] = {"invocations": ("C",),
                    "required": False,
                    "n-params": 0, # or True/False
                    "n-delimiter": None,
                    "valid-types": [str],
                    "choices": [],
                    "default": None,
                    "description": "If specified, indicates a continue-run with the total specified number of particles. (requires that the runtpe be specified)",
                    "params": None
                    }

ARG_SET2["runtpe"] = {"invocations": ("runtpe",),
                    "required": False,
                    "n-params": 0, # or True/False
                    "n-delimiter": None,
                    "valid-types": [str],
                    "choices": [],
                    "default": "input.i",
                    "description": "Glob-compatible path the the MCNP runtpe file (required for continue-run)",
                    "params": None
                    }

ARG_SET2["wwinp"] = {"invocations": ("wwinp",),
                    "required": False,
                    "n-params": 0, # or True/False
                    "n-delimiter": None,
                    "valid-types": [str],
                    "choices": [],
                    "default": "wwinp",
                    "description": "Glob-compatible path to the MCNP wwinp file",
                    "params": None
                    }


GROUP_DICT = OrderedDict()
GROUP_DICT['BSUB'] = ARG_SET1
GROUP_DICT['MCNP'] = ARG_SET2

####################################################################################

args = sys.argv[1:]

group_delimeter = "::"
group_indices = [i for i, arg in enumerate(args) if arg==group_delimeter]
group_indices = [-1] + group_indices + [len(args)]
group_dict = {}
for i in range(len(group_indices)-1):
     if i < len(group_indices):
        try:
            group_dict.update({list(GROUP_DICT.keys())[i]: args[group_indices[i]+1:group_indices[i+1]]})
        except IndexError:
            print("Arguments were provided for more than one group but only one group was specified to the parser")

# print(group_dict)

def red(text):
    return "\033[31m" + text + "\033[0m"

def arg_info(group_, var_):
    if len(GROUP_DICT[group_][var_]['invocations']) > 1:
        content = f"[{' | '.join(GROUP_DICT[group_][var_]['invocations'])} <{var_}>]"
    elif not GROUP_DICT[group_][var_]['invocations']: # Handles positional
        content = f"<{var_}>"
    else:
        content = f"[{GROUP_DICT[group_][var_]['invocations']}=<{var_}>]"
    return red(content) if GROUP_DICT[group_][var_]['required'] else content

prog = sys.argv[0]
description = "This script allows you to specify arguments for bsub and mcnp in the same execution to submit to the ASCII cluster."
usage_help = ""
variable_help = ""
for i, g in enumerate(GROUP_DICT.keys()):

    valid_invocations = [inv for ATTRIBUTES in GROUP_DICT[g].values() for inv in ATTRIBUTES['invocations']]
    required_args     = [DEST for DEST, ATTRIBUTES in GROUP_DICT[g].items() if ATTRIBUTES['required'] is True]
    optional_args     = [DEST for DEST, ATTRIBUTES in GROUP_DICT[g].items() if ATTRIBUTES['required'] is False and ATTRIBUTES['invocations']]
    positional_args   = [DEST for DEST, ATTRIBUTES in GROUP_DICT[g].items() if ATTRIBUTES['invocations'] is None]

    pos_args_help = [f"        {arg}: {' | '.join(GROUP_DICT[g][arg]['invocations'])} {GROUP_DICT[g][arg]['choices']} {'Any' if not GROUP_DICT[g][arg]['valid-types'] else ','.join([typ.__name__ for typ in GROUP_DICT[g][arg]['valid-types']])}    {GROUP_DICT[g][arg]['description']}\n" for arg in positional_args]
    opt_args_help = [f"        {arg}: {' | '.join(GROUP_DICT[g][arg]['invocations'])} {GROUP_DICT[g][arg]['choices']} {'Any' if not GROUP_DICT[g][arg]['valid-types'] else ','.join([typ.__name__ for typ in GROUP_DICT[g][arg]['valid-types']])}    {GROUP_DICT[g][arg]['description']}\n" for arg in optional_args]
    req_args_help = [f"        {arg}: {' | '.join(GROUP_DICT[g][arg]['invocations'])} {GROUP_DICT[g][arg]['choices']} {'Any' if not GROUP_DICT[g][arg]['valid-types'] else ','.join([typ.__name__ for typ in GROUP_DICT[g][arg]['valid-types']])}    {GROUP_DICT[g][arg]['description']}\n" for arg in required_args]
    variable_help += f"""\
    {g}:
        required arguments:
    {"".join(req_args_help)}
        optional arguments:
    {"".join(opt_args_help)}
        positional arguments: 
    {"".join(pos_args_help)}
    """
    for v in GROUP_DICT[g].keys():
        usage_help += (f" {arg_info(g, v)}")
    if i < len(GROUP_DICT.keys())-1:
        usage_help += (f" {group_delimeter}")

HELP_MSG = f"""\
{prog}: {description}

usage: {usage_help}

{variable_help}
"""

if sys.argv[1] in ['-h', '--help']:
    print(HELP_MSG)
    sys.exit()

####################################################################################

for GROUP, ARG_SET in GROUP_DICT.items(): 

    try:
        args = group_dict[GROUP]
    except KeyError:
        print("More than one argument group was specified but no arguments for that group were provided")
        continue

    valid_invocations = [inv for ATTRIBUTES in ARG_SET.values() for inv in ATTRIBUTES['invocations']]
    required_args     = [DEST for DEST, ATTRIBUTES in ARG_SET.items() if ATTRIBUTES['required'] is True]
    optional_args     = [DEST for DEST, ATTRIBUTES in ARG_SET.items() if ATTRIBUTES['required'] is False and ATTRIBUTES['invocations']]
    positional_args   = [DEST for DEST, ATTRIBUTES in ARG_SET.items() if ATTRIBUTES['invocations'] is None]

    ######################################################################
    # Loop through all the arguments to get the indices of confirmed args 
    tracked_args = []
    for a, arg in enumerate(args):
        for DEST, ATTRIBUTES in ARG_SET.items():
            if ATTRIBUTES['invocations']:
                if arg in ATTRIBUTES['invocations'] or arg.split("=", 1)[0] in ATTRIBUTES['invocations']:
                    num_params = ATTRIBUTES['n-params']
                    delim = ATTRIBUTES['n-delimiter']
                    tracked_args.append((DEST, arg, a, num_params, delim))

    # print(valid_invocations)
    # print(required_args)
    # print(optional_args)
    # print(positional_args)                
    # print(tracked_args)

    ######################################################################
    # Based on detected args, report if a required arg is missing
    for DEST in required_args:
        if DEST not in list(zip(*tracked_args))[0]:
            print(f"{DEST} is a required argument but was not supplied.")

    ######################################################################
    # Handle parameter allocation
    # Tracked args is created as separate variable to understand "starting indices" in the execution line
    tracked_params = []
    for t, (DEST, arg, i, look_ahead, delim) in enumerate(tracked_args): # Need delimiter type in here if needed

        ####################################
        # Go the specified number of params
        if type(look_ahead) == int:

            # TODO: Would need to add delimiter logic here to split the next arg instead of slicing all args (this applies to look_ahead > 0 and '+')
            if look_ahead > 0:
                params = args[i+1:i+1+look_ahead]
                # Check that number of params was correctly specified 
                for param in params:
                    if param in valid_invocations:
                        print(f"Missing a param for {DEST}. Unexpectedly encountered an invocation before specified number of params was provided")
                        # raise CountError(f"Missing a param for {dest}. Unexpectedly encountered an invocation before specified number of params was provided")
                        # This handles too many args - too few args has to be handled by positional logic
            
            elif look_ahead == 0: # Assume "equal" invocation
                params = GROUP_DICT[GROUP][DEST]['default'] if arg.split("=", 1)[1]=='' else [arg.split("=", 1)[1]]

        ####################################
        # go until you hit the next invocation or end of args
        elif look_ahead=="+":     # 1 or more
            print("Lookahead does equal '+'", arg)
            try:
                next_invocation = tracked_args[t+1][2]
            except IndexError:
                next_invocation = len(args)
            
            params = args[i+1:next_invocation]

        ####################################
        # go once and if you hit invocation use default (only valid for optional args)
        elif look_ahead=="?":    # 0 or 1
            if args[i+1] in valid_invocations:
                params = GROUP_DICT[GROUP][DEST]['default']
            else:
                params = args[i+2]

        ####################################
        # elif look_ahead=="*":   # 0 or more - what does an example of this even look like?

        ####################################
        elif type(look_ahead) == bool:
            params = [look_ahead]

        ####################################
        ARG_SET[DEST]['params'] = params

        tracked_params.extend(params) # Used to compare sys.argv to obtain positionals

        ####################################
        # Perform type/choice checks
        invalid_params_types = []
        invalid_params_choices = []
        for param in params:
            valid_types = ARG_SET[DEST]['valid-types']
            if valid_types:
                type_valid = False
                for typ in valid_types:
                    try:
                        typ(param)
                        type_valid = True
                    except:
                        pass
                if not type_valid:
                    invalid_params_types.append(param)

            valid_choices = ARG_SET[DEST]['choices']
            if valid_choices and param not in valid_choices:
                invalid_params_choices.append(param)
        
        for inval_param in invalid_params_types:
            print(f"Parameter {inval_param} cannot be forced to any one of the following type(s): {valid_types} for argument {DEST}")
        
        for inval_param in invalid_params_choices:
            print(f"Not a valid choice for parameter {inval_param} for argument {DEST}")
        
    # print(tracked_params)

    ######################################################################
    # Gather all non-params/non-invocations as positional args
    candidate_positionals = [arg for arg in args if arg not in list(zip(*tracked_args))[1] and arg not in tracked_params]
    new_candidate_positionals = []
    for positional in candidate_positionals:
        # Positionals should not start with "-" or "--" unless they in quotes e.g. "-test" (these should be considered invlaid args)
        if positional.startswith("-") or positional.startswith("--") or "=" in positional: # TODO: positionals starting with - or -- or containing "=" must have quotes around them otherwise they will be assumed invalid
            print(f"{positional} is not a valid argument.")
        else:
            new_candidate_positionals.append(positional)

    valid_positionals = new_candidate_positionals[:len(positional_args)]
    invalid_positionals = new_candidate_positionals[len(positional_args):]

    # print(candidate_positionals)
    # print(new_candidate_positionals)
    # print(positional_args)
    # print(valid_positionals)
    # print(invalid_positionals)

    for position in invalid_positionals:
        print(f"Positional argument with value {positional} in excess of specified positional arguments")
    for positional, DEST in zip(valid_positionals, positional_args):
        ARG_SET[DEST]['params'] = positional


##########################################################################
for v in GROUP_DICT.values():
    for v_ in v.values():
        v_['valid-types'] = [el.__name__ for el in v_['valid-types']]
print(json.dumps(GROUP_DICT, indent=4))

##### Now parse the dictionary for all the values assigned to variables

# Custom Exceptions: ArgumentError


# Some Rules
bsub_arg_params = {GROUP_DICT['BSUB'][k]['invocations'][0]: GROUP_DICT['BSUB'][k]['params'] for k in GROUP_DICT['BSUB'].keys()}
mcnp_arg_params = {GROUP_DICT['MCNP'][k]['invocations'][0]: GROUP_DICT['MCNP'][k]['params'] for k in GROUP_DICT['MCNP'].keys()}

input_files = [file for file in glob.glob(f"./**/{mcnp_arg_params['name']}", recursive=True)]

bsub_arg_params['-J'] = [f"{os.path.splitext(os.path.basename(file))[0]}"[:10] for file in input_files]
bsub_arg_params['-q'] = "normal" if bsub_arg_params['-q'] is None else bsub_arg_params['-q']

if mcnp_arg_params['C']:
    if not mcnp_arg_params['runtpe']:
        print("A runtpe file must be specified if continuing a run")
    else:
        if len(input_files) > 1:
            if (bsub_arg_params['-eo'] or bsub_arg_params['-oo']):
                raise print(None, "Can't rename err/out file since that would be ambiguous for more than one input file")
            else:
                bsub_arg_params['-eo'] = f"{mcnp_arg_params['name'].rsplit('.', 1)[0]}.err" if bsub_arg_params['eo'] is None else bsub_arg_params['eo']
                bsub_arg_params['-oo'] = f"{mcnp_arg_params['name'].rsplit('.', 1)[0]}.out" if bsub_arg_params['oo'] is None else bsub_arg_params['oo']
        elif len(input_files) == 1:
            bsub_arg_params['-eo'] = [f"{os.path.splitext(os.path.basename(file))[0]}.err"for file in input_files] 
            bsub_arg_params['-oo'] = [f"{os.path.splitext(os.path.basename(file))[0]}.out"for file in input_files] 
        elif len(input_files) == 0:
            raise FileNotFoundError(None, "Input file not found in directory recursion")    
else:
    if not mcnp_arg_params['name']:
        print(None, "An input file must be specified in the absence of specified C,runtpe")

print(bsub_arg_params)
print(mcnp_arg_params)

# Reconstruct the execution line
# execution = "bash <<-END\n" + HERE_DOCUMENT + "\nEND"
# p = subprocess.Popen(execution, shell=True) 
# p.wait()