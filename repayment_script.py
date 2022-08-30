### Repayment from cantod export for Chandra Station
### 2022-08-29 - Reece Williams

import ijson # pip install ijson
import json
import os

'''
Task:
- Get all delegators to chandra station
- get their balance

- Get 0.75% of their staked amount
- ^ debug data
- put all into a single message
'''

# CANTO / CHANDRA SPECIFIC
SLASH_REPAYMENT = 0.0075 # 0.75%
ACANTO_AMOUNT = 10**18 # std cosmos is 10**6 (1_000_000)
val_addr = "cantovaloper19e84kdf5z09u2v4gpv0m7r6dcu0p8llkf30qtv"
PAYMENT_FROM_ADDRESS = "canto12u7rpvj0hm4wq0n7gx356qxy8nw6mzmmpy9wyc" # the --from KEY address you'll be paying from, or ctrl + f in the .json file


sections = { 
    # locations within the genesis file
    # for ijson, every section MUST end with .item to grab the values
    "staked_amounts": "app_state.staking.delegations.item",
    "account_balances": "app_state.bank.balances.item",
    "total_supply": "app_state.bank.supply.item",
    "validators_info": "app_state.staking.validators.item", # useful to get like, a valudator bonded status. Is a list
}  

def stream_section(fileName, key, debug=False):
    '''
        Given a fileName and a json key location,
        it will stream the jso objects in that section 
        and yield them as:
        -> index, object
    '''
    if key not in sections:
        print(f"{key} not in sections")
        return

    key = sections[key]

    with open(fileName, 'rb') as input_file:
        parser = ijson.items(input_file, key)
        for idx, obj in enumerate(parser):
            if debug: print(f"stream_section: {idx}: {obj}")
            yield idx, obj


# Required for every chain we use
def save_staked_users(input_file="exports/chain.json", output_file="staked/chain.json") -> dict:
    '''
    Saves all Validators, some stats, and their delegators:
    {
        "osmovaloperxxxxxxxxx": {
            "stats": {
                "total_stake": "200.0",
            },
            "delegators": {
                "delegator1": 
                    {
                        "amount": 100.0,                        
                    }
                "delegator2": 100.0,
            }
        },
    }
    Returns a dict of information
    '''

    # Loads a cached version if its there
    if os.path.isfile(output_file):
        with open(output_file, 'r') as f:
            print(f"Using cached file {output_file} for staked values")
            validators = json.load(f)
        
        _totalStaked = 0
        # _numOfUniqueDelegators = set()
        for validator in validators.keys():
            _totalStaked += float(validators[validator]["stats"]["total_stake"])

        return {
            "total_staked": _totalStaked, 
            "number_of_validators": len(validators.keys()),
            # "number_of_unique_delegators": len(numberOfUniqueDelegators) # not implimented
        }
    

    print(f"Saving staked amounts to {output_file}")    
    STAKED_VALUES = {}
    numberOfUniqueDelegators = set()

    for idx, obj in stream_section(input_file, 'staked_amounts'):
        delegator = str(obj['delegator_address'])
        valaddr = str(obj['validator_address'])
        stake = float(obj['shares'])  
        bonus = 1.0 
        # if idx % 100 == 0: print(f"{idx} staking accounts processing...")

        if valaddr != val_addr:
            continue # not chandra station

        if valaddr not in STAKED_VALUES:
            STAKED_VALUES[valaddr] = {"stats": {"total_stake": 0}, "delegators": {}}

        STAKED_VALUES[valaddr]["stats"]["total_stake"] += stake
        STAKED_VALUES[valaddr]["delegators"][delegator] = {"amount": stake}
        numberOfUniqueDelegators.add(delegator) # only adds unique user addresses to set        

        # output += f"{delegator} {valaddr} {bonus} {float(stake)}\n"

    with open(output_file, 'w') as o:
        o.write(json.dumps(STAKED_VALUES))
    print(f"Saved {len(STAKED_VALUES)} validators and {len(numberOfUniqueDelegators)} delegators to {output_file}")


# save_staked_users('canto_export.json', 'canto_staked.json')
def GetUsersStakedAmounts():
    # load canto_staked.json
    with open('canto_staked.json', 'r') as f:
        staked = json.load(f)

    # get chandra total staked
    chandra_staked = staked[val_addr]["stats"]["total_stake"] 
    total_payment_should_be = chandra_staked * SLASH_REPAYMENT 
    
    # print(f"Chandra Total stake: {4.387670724281231e+24 / ACANTO_AMOUNT:.2f}")
    # print(f"Total payment: {total_payment_should_be:.2f}acanto")
    # print(f"Total payment in canto: {total_payment_should_be / ACANTO_AMOUNT:.2f} canto")

    # loop through all delegators
    paymentAmounts = {} # addr, acanto amount owed
    for address in staked[val_addr]["delegators"]:
        amount = staked[val_addr]["delegators"][address]["amount"]

        # print(address, f"{amount:.2f}acanto")
        
        paymentAmounts[address] = amount * SLASH_REPAYMENT

    # print(paymentAmounts)
    return paymentAmounts


MSG_FORMAT = {"body":{"messages":[],"memo":"","timeout_height":"0","extension_options":[],"non_critical_extension_options":[]},"auth_info":{"signer_infos":[],"fee":{"amount":[],"gas_limit":"200000","payer":"","granter":""}},"signatures":[]}

def pay_delegators():
    MSG_FORMAT["body"]["memo"] = "Slash Repayment to delegatgors"

    total_staked = 0
    for delegator_addr, amount in GetUsersStakedAmounts().items():
        MSG_FORMAT["body"]["messages"].append({
            "@type":"/cosmos.bank.v1beta1.MsgSend",
            "from_address":f"{PAYMENT_FROM_ADDRESS}",
            "to_address":f"{delegator_addr}",
            "amount":[{"denom":"acanto","amount":f"{int(amount):.0f}"}]  # does this auto convert to the correct number?
        })
        total_staked += amount

    print(f"{total_staked / ACANTO_AMOUNT:.0f}")

    # get current dir
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, "repayment_tx.json"), 'w') as file:
        file.write(json.dumps(MSG_FORMAT, indent=4))
    print("Saved repayment_tx.json, just sign & broadcast")


if __name__ == '__main__':
    pay_delegators()