import functools
import multiprocessing
from typing import Any, Callable, Dict, List, Optional, Tuple

from .dtypes import PositiveInt


def starmap_async(
    func: Callable,
    func_input: List[Tuple],
    num_workers: PositiveInt = None,
    **kwargs: Optional[Dict[str, Any]],
) -> List:
    """
    Wrapper for multiprocessing.Pool.starmap_async.

    Parameters
    ----------
    func: Callable
        Function to call.

    func_input: List[Tuple]
        Input arguments for function `:func:`. Length of tuple should
        be equal to the number of arguments of `:func:`. Can be [].

    num_workers: PisitiveInt
        Number of asynchronous processes to launch

    **kwargs: Dict[str, Any], optional
        Any keywords to pass to the function `:func:`.

    Returns
    -------
    List[Any]
        List of outputs returned by `:func:`.


    """
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    if kwargs.pop("debug", None):
        return [func(*single_input, **kwargs) for single_input in func_input]

    func_with_args = functools.partial(func, **kwargs)

    with multiprocessing.Pool(processes=num_workers) as pool:
        return pool.starmap_async(func_with_args, func_input).get()
