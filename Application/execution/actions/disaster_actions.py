import sys
import httpx
import asyncio
import logging
import importlib
import pandas as pd
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.user import User    # noqa: E402
from Application.utils.load_json import load    # noqa: E402
from Application.api.nobitex_api import Trade    # noqa: E402
from Application.utils.event_channels import Event    # noqa: E402
from Application.api.api_service import APIService    # noqa: E402
from Application.data.exchange import Nobitex as nb    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402

jarchi = EventHandler()



# =================================================================================================
jarchi.register_event(Event.RECOVERY_MECHANISM_ACCOMPLISHED, [])
# =================================================================================================



# =================================================================================================
async def recovery_mechanism() -> None:
    """
    
    """
    try:
        # Extract function names from strategy.json file
        strategy_cfg = load(r'Application/configs/strategy.json')
        strategy_mechanisms = strategy_cfg['recovery_mechanisms']

        # Extract function objects from disaster_actions.py module
        funcs_set = set()
        for mechanism in strategy_mechanisms:
            funcs_set.add(getattr(
                importlib.import_module('Application.execution.actions.disaster_actions'),
                mechanism['name']))

        # Execute functions synchronously
        # for func in funcs_set:
        #     await func()

        # Execute functions asynchronously
        coroutines: list = [func() for func in funcs_set]
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # logic to exit recovery mechanism in case all results are successful
        if all(result == 'succeeded' for result in results):
            logging.info('Recovery mechanisms performed successfully.')
            logging.info(f'Broadcasting "{Event.RECOVERY_MECHANISM_ACCOMPLISHED}" event from '\
                         '"disaster_actions.recovery_mechanism()" function.')

            await jarchi.emit(Event.RECOVERY_MECHANISM_ACCOMPLISHED)

    except asyncio.CancelledError as err:
        logging.error('asyncio.CancelledError occurred inside recovery_mechanism() function: ',err)
    except Exception as err:
        logging.error(f'Inside recovery_mechanism() function: {err}')
# ________________________________________________________________________________ . . .


async def close_all_positions():
    """
    
    """
    trade = Trade(APIService())

    logging.info('Executing "close_all_positions()" recovery mechanism')
    success = await trade.close_all_positions(User.TOKEN)    # type: ignore
    return 'succeeded' if success == 'succeeded' else 'failed'
# ________________________________________________________________________________ . . .


async def omit_all_orders():
    """
    
    """
    trade = Trade(APIService())

    logging.info('Executing "omit_all_orders()" recovery mechanism')
    success = await trade.cancel_all_orders(client=httpx.AsyncClient(), token=User.TOKEN)    # type: ignore
    return 'succeeded' if success == 'succeeded' else 'failed'
# ________________________________________________________________________________ . . .


async def fetch_gadabouts():
    """
    
    """
    gadabouts_df = pd.DataFrame()

    api_service = APIService()
    trade = Trade(api_service)

    # populating positions Dataframe
    positions_df = await anext(trade.fetch_open_positions(
        client       = httpx.AsyncClient(),
        token        = User.TOKEN,    # type: ignore
        req_interval = nb.Endpoint.POSITIONS_MI,
        max_rate     = nb.Endpoint.POSITIONS_RL,
        rate_period  = nb.Endpoint.POSITIONS_RP
    ))

    if not positions_df.empty:
        pair_df = positions_df[['srcCurrency', 'dstCurrency']].drop_duplicates()
        pairs = [tuple(pair) for pair in pair_df.to_numpy()]
        print(pairs)


        # populating orders DataFrame
        orders_df = pd.DataFrame()
        for srcCurrency, dstCurrecy in pairs:
            this_pairs_orders_df = await anext(trade.fetch_orders(
                client       = httpx.AsyncClient(),
                token        = User.TOKEN,    # type: ignore
                req_interval = nb.Endpoint.ORDERS_MI,
                max_rate     = nb.Endpoint.ORDERS_RL,
                rate_period  = nb.Endpoint.ORDERS_RP,
                src_currency = srcCurrency,
                dst_currency = dstCurrecy
            ))

            orders_df = pd.concat([orders_df, this_pairs_orders_df])


        # In case there is no orders at all, then all positions are gadabout
        if orders_df.empty:
            gadabouts_df = positions_df
            return gadabouts_df
        # ________________________________________________________________________ . . .


        # In case there are orders for some of positions, positions that has no order are gadabouts
        orders_pairs_set = set(zip(orders_df['srcCurrency'], orders_df['dstCurrency']))
        poss_unq_pairs = [pair for pair in pairs if pair not in orders_pairs_set]

        gadabouts_df = positions_df[
            positions_df[['srcCurrency', 'dstCurrency']].apply(tuple, axis=1).isin(poss_unq_pairs)
        ]
        # ________________________________________________________________________ . . .


        # In case of remaining positions, check whether available orders are valid for them or not
        remaining_pairs = [pair for pair in pairs if pair in orders_pairs_set]
        for srcCurrency, dstCurrency in remaining_pairs:
            pair_orders_df = orders_df[(orders_df['srcCurrency'] == srcCurrency) & 
                                       (orders_df['dstCurrency'] == dstCurrency)]

            position_df = positions_df[(positions_df['srcCurrency'] == srcCurrency) & 
                                       (positions_df['dstCurrency'] == dstCurrency)]

            # Calculate total position size
            total_position_size = position_df['size'].sum()

            # Calculate SL and TP coverage
            sl_coverage = pair_orders_df[pair_orders_df['type'] == 'stop_loss']['size'].sum()
            tp_coverage = pair_orders_df[pair_orders_df['type'] == 'take_profit']['size'].sum()

            if sl_coverage < total_position_size or tp_coverage < total_position_size:
                gadabouts_df = pd.concat([gadabouts_df, position_df])
        # ________________________________________________________________________ . . .

    
    return gadabouts_df   
# ________________________________________________________________________________ . . .

# =================================================================================================

if __name__ == '__main__':
    asyncio.run(recovery_mechanism())