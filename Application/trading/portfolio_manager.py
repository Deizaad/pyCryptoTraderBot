import sys
import httpx
import asyncio
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.user import User             # noqa: E402
from Application.utils.load_json import load       # noqa: E402
from Application.api.nobitex_api import Market     # noqa: E402
from Application.api.nobitex_api import Account    # noqa: E402
from Application.api.api_service import APIService # noqa: E402

account = Account()
market = Market(APIService())



# =================================================================================================
async def fetch_portfolio_balance() -> tuple[int, float]:
    """
    Fetches the portfolio balance of user.

    Parameters:
        user_token (str): User's API token.

    Returns:
        porfolio_balance (tuple): A tuple containing portfolio balance in 'Rials' and 'USD'.
    """
    async with httpx.AsyncClient() as http_client:
        wallets_coroutine = account.wallets(http_agent = http_client,
                                            token      = User.TOKEN,    # type: ignore
                                            drop_void  = True)

        price_rate_coroutine = await anext(market.live_fetch_market_price(src_currency = 'usdt',
                                                                    dst_currency = 'rls'))

        wallets_df, usdt_rate = await asyncio.gather(wallets_coroutine, price_rate_coroutine)

    portfolio_balance_rials = wallets_df.rial_balance.sum()
    portfolio_balance_usd = round((portfolio_balance_rials / usdt_rate), 2)

    return portfolio_balance_rials, portfolio_balance_usd
# ________________________________________________________________________________ . . .


async def get_allowed_exposure():
    """
    Returns:
        allowed_exposure (float): The allowed_exposure balance in 'USD'.
    """
    strategy_cfg = load(r'Application/configs/strategy.json')
    _, usd_portfolio_balance = await fetch_portfolio_balance()

    allowed_exposure = usd_portfolio_balance * strategy_cfg['portfolio_exposure']
    return allowed_exposure
    
# =================================================================================================



if __name__ == '__main__':
    # rls, usd = asyncio.run(fetch_portfolio_balance())
    # print(rls, usd)

    a = asyncio.run(get_allowed_exposure())
    print(a)