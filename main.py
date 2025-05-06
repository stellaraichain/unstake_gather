import bittensor as bt
import os
sub = bt.Subtensor(network = "finney")

to_sell = [0, 30, 44, 48] # list of netuids to unstake from
increment = 1 # amount of alpha to unstake
total_sell = 0 # total amount of alpha unstaked
stake = {} # dictionary to store the stake for each netuid

WALLETS_DIR = os.path.expanduser("~/.bittensor/wallets")

def get_wallets_and_hotkeys(wallets_dir=WALLETS_DIR):
    wallet_hotkey_map = {}
    for wallet_name in os.listdir(wallets_dir):
        wallet_path = os.path.join(wallets_dir, wallet_name)
        hotkeys_path = os.path.join(wallet_path, "hotkeys")
        if os.path.isdir(hotkeys_path):
            try:
                hotkeys = [
                    hk for hk in os.listdir(hotkeys_path)
                    if not hk.startswith('.')  # Ignore system files like .DS_Store
                ]
                wallet_hotkey_map[wallet_name] = hotkeys
            except Exception as e:
                print(f"⚠️ Failed to read hotkeys for {wallet_name}: {e}")
    return wallet_hotkey_map

# Example usage
wallet_hotkeys = get_wallets_and_hotkeys()
for wallet, hotkeys in wallet_hotkeys.items():
    print(f"� {wallet}: {hotkeys}")

def unstake(wallet, netuid, alpha_amount, alpha_decrease):
    increment = alpha_decrease # amount of alpha to unstake
    current_stake = sub.get_stake(
        coldkey_ss58 = wallet.coldkeypub.ss58_address,
        hotkey_ss58 = wallet.hotkey.ss58_address,
        netuid = netuid,
    )
    total_sell = 0 # total amount of alpha unstaked
    print(f'started to unstake from wallet {wallet} on netuid {netuid} amount of {current_stake} by {alpha_decrease} till {alpha_amount}')

    while total_sell < current_stake:
        subnet = sub.subnet(netuid)
        if current_stake.tao < increment:
            increment = current_stake.tao
        # print(f"slippage for subnet {netuid}", subnet.alpha_slippage(increment))
        sub.unstake( 
            wallet = wallet, 
            hotkey_ss58 = wallet.hotkey.ss58_address,
            netuid = netuid, 
            amount = bt.Balance.from_tao(increment)
        )
        current_stake = sub.get_stake(
            coldkey_ss58 = wallet.coldkeypub.ss58_address,
            hotkey_ss58 = wallet.hotkey.ss58_address,
            netuid = netuid,
        )
        total_sell += increment
        alpha_amount -= increment
        print (f'ustaking from wallet {wallet} on netuid {netuid} price {subnet.price} current stake is {current_stake}')
        sub.wait_for_block()
        
    print(f'finished unstake from wallet {wallet} on netuid {netuid} ongoing unstake amount is {alpha_amount}')
    return alpha_amount

if __name__ == "__main__":
    wallet_hotkeys = get_wallets_and_hotkeys()
    password = "ILoveMother1228"

    for wallet_name, hotkey_list in wallet_hotkeys.items():
        for hotkey in hotkey_list:
            print(f"✈️ Unstaking from wallet: {wallet_name}, hotkey: {hotkey}")
            try:
                wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
                # wallet = bt.wallet(name="miner3", hotkey="miner3_h3")
                wallet.coldkey_file.save_password_to_env(password)
                wallet.unlock_coldkey()
                unstake(wallet, netuid=30, alpha_amount=1000, alpha_decrease=10)
            except Exception as e:
                print(f"❌ Error with wallet={wallet_name}, hotkey={hotkey}: {e}")

    destination = "5GgpDcxpcxSZJ6VedUL8ruDb2XFXBuUdhXrnWGbaenH9PE6q"

    for wallet_name in wallet_hotkeys:
        try:
            wallet = bt.Wallet(name=wallet_name)
            wallet.coldkey_file.save_password_to_env(password)
            wallet.unlock_coldkey()
        except Exception as e:
            print(f"❌ Failed to unlock wallet '{wallet_name}': {e}")
            continue  # Skip to the next wallet

        try:
            balance = sub.get_balance(wallet.coldkey.ss58_address)
            fee_buffer = bt.Balance.from_tao(0.00016)
            amount_to_send = balance - fee_buffer
            print(f"👉Now transferring tao of wallet {wallet_name}...")

            if amount_to_send.tao <= 0:
                print("❌ Not enough balance to cover fees.")
                continue

            result = sub.transfer(
                wallet=wallet,
                dest=destination,
                amount=amount_to_send,
            )
            print(f"✅ Transfer complete for {wallet_name}. Result: {result}")
        except Exception as e:
            print(f"❌ Transfer failed for wallet '{wallet_name}': {e}")

