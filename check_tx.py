import requests
import json
import pygsheets


hydra_decimals = 100000000

def get_hydra_decimal(hydra_value):
    return int(hydra_value)/hydra_decimals

def get_delegations():
    Headers = {'content-type': 'text/plain;'}
    rpc_params = '{"jsonrpc": "1.0", "id":"curltest", "method": "getdelegationsforstaker", "params": [ "HM6TFbbBvrJ4hcMTFT93R7DBz1FmcUTGAC" ] }'
    response = requests.post('http://192.168.0.11:3389/', headers=Headers, data=rpc_params, auth=('stray', '1'))
    json_response = json.loads(response.text)
    results = json_response["result"]
    delegation_data = []
    block_height = []
    for items in results:
        delegators = items["delegate"]
        blockHeight = items["blockHeight"]
        delegation_data.append(delegators)
        block_height.append(blockHeight)
    return delegation_data


def get_weight_delegators(del_address):
    get_balances = []
    for i in range(len(del_address)):
        endpoint = f'https://explorer.hydrachain.org/api/address/{del_address[i]}/balance-history'
        headers = {'User-Agent': '...', 'referer': 'https://...'}
        response = requests.get(endpoint, headers=headers)
        json_response = json.loads(response.text)
        transactions = json_response["transactions"][0]
        balance = get_hydra_decimal(transactions["balance"])
        get_balances.append(balance)
    return get_balances



def check_txs(current_transaction):
    final_results = []
    for i in range(len(current_transaction)):
        endpoint = f"https://explorer.hydrachain.org/api/tx/{current_transaction[i]}"  # don't forget [i] for loops
        headers = {'User-Agent': '...', 'referer': 'https://...'}
        response = requests.get(endpoint, headers=headers)
        json_response_loop = json.loads(response.text)        

        outputs = json_response_loop["outputs"]
        # outputs_zero = json_response_loop["outputs"][0].get("value") #For future use to check if [0]value == None 

        block_reward = abs(get_hydra_decimal(json_response_loop["fees"]))

        dict_delegator = []
        if len(outputs) > 3:  # This is a block won by delegator but has other transactions on it , but there are those cases where extra txs are present but the SuperStaker  won, so we need to figure out how to identify that case and discard them
            delegator = json_response_loop["outputs"][2]
            other_tx = json_response_loop["outputs"]
            
            other_values = []
            for values in other_tx:
                v = int(values["value"])
                other_values.append(v)
                    
            check_number = 500000000

            if other_values[2] > check_number:
                other_values_cut = other_values[2:]
                other_values_total = get_hydra_decimal(sum(other_values_cut))
                delegator_reward = get_hydra_decimal(delegator["value"])
                delegator_address = delegator["address"]
                super_staker_fee = block_reward - other_values_total
                dict_delegator.append(delegator_address)
                dict_delegator.append(delegator_reward)
                dict_delegator.append(super_staker_fee)
                
            else:
                correct_address_is_staker = json_response_loop["outputs"][1]
                correct_address = correct_address_is_staker["address"]
                super_staker_fee = block_reward
                delegator_reward = 0
                dict_delegator.append(correct_address)                
                dict_delegator.append(super_staker_fee)
                dict_delegator.append(delegator_reward)

        if len(outputs) == 2:  # This is a block won by super staker
            super_staker = json_response_loop["outputs"][1]
            super_staker_address = super_staker["address"]
            super_staker_reward = block_reward
            super_staker_fee = 0
            dict_delegator.append(super_staker_address)
            dict_delegator.append(super_staker_reward)
            dict_delegator.append(super_staker_fee)

        if len(outputs) == 3:  # This is a block won by delegator
            delegator_long_tx = json_response_loop["outputs"][2]
            delegator_long_tx_reward = get_hydra_decimal(delegator_long_tx["value"])
            delegator_long_tx_address = delegator_long_tx["address"]
            super_staker_fee = block_reward - delegator_long_tx_reward
            dict_delegator.append(delegator_long_tx_address)
            dict_delegator.append(delegator_long_tx_reward)
            dict_delegator.append(super_staker_fee)

        results = dict_delegator
        final_results.append(results)

    return final_results


def get_tx_id():
    wallet_address = "HM6TFbbBvrJ4hcMTFT93R7DBz1FmcUTGAC"
    endpoint = f"https://explorer.hydrachain.org/api/address/{wallet_address}/basic-txs?limit=100000000000000&offset=0"
    headers = {'User-Agent': '...', 'referer': 'https://...'}
    response = requests.get(endpoint, headers=headers)
    json_response = json.loads(response.text)
    tx_transactions = json_response["transactions"]
    # Get data from [{}] type of json : array of objects I think is called:
    tx_ids = []
    for ids in tx_transactions:
        tx_id = ids["id"]
        tx_ids.append(tx_id)
    return tx_ids


all_txs = get_tx_id()
result = check_txs(all_txs)
result = result[:-51]
print("Done!")


path = 'straypet.json'
gc = pygsheets.authorize(service_account_file=path)
sh = gc.open('StrayLiveData')
wk1 = sh[9]
wk1.clear(start = 'A2')
wk1.append_table(values = result, start = 'A2', end = None, dimension = 'ROWS', overwrite = True)


delegators = get_delegations()
balances = get_weight_delegators(delegators)


path = 'straypet.json'
gc = pygsheets.authorize(service_account_file=path)
sh = gc.open('StrayLiveData')
wk1 = sh[2]
wk1.clear(start = 'B15:C37')
wk1.append_table(values = (delegators, balances), start = 'B15', end = None, dimension = 'COLUMNS', overwrite = True)
