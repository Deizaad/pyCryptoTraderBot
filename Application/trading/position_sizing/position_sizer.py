import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load                            # noqa: E402
from Application.data.data_tools import extract_singular_strategy_setup # noqa: E402

POSITION_SIZING_APPROACH = extract_singular_strategy_setup(
    setup_name = 'position_sizing_approach',
    config = load(r'Application/configs/strategy.json'),
    functions_module_path = 'Application.trading.position_sizing.position_sizing_functions'
)



async def compute_position_margin_size(parameters):
    """
    Executes the chosen position sizing function.
    """
    position_sizing_func = POSITION_SIZING_APPROACH['function']

    await position_sizing_func(parameters)

print(POSITION_SIZING_APPROACH)