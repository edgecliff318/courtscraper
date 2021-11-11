import concurrent.futures
import logging
import os
from multiprocessing import Pool

logger = logging.Logger(__name__)


class Processor:
    def __init__(self, workers=None):
        if workers is not None:
            self.workers = workers
        elif os.environ.get('PYLT_NUM_WORKERS', None) is not None:
            self.workers = int(os.environ.get('PYLT_NUM_WORKERS'))
        else:
            self.workers = 10

    def parallelize_multithread(self, mapfunc):
        """
        Parallelize the mapfunc with multithreading. mapfunc calls will be
        partitioned by the provided list of arguments. Each item in the list
        will represent one call's arguments. They can be tuples if the function
        takes multiple arguments, but one-tupling is not necessary.

        If workers argument is not provided, workers will be pulled from an
        environment variable PYLT_NUM_WORKERS. If the environment variable is not
        found, it will default to 10 workers.
        :param mapfunc:
        :type mapfunc:
        :return: func(args_list: list[arg]) => dict[arg -> result]
        :rtype:
        """
        workers = self.workers

        def wrapper(args_list):
            result = {}
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=workers) as executor:
                tasks = {}
                for args in args_list:
                    if isinstance(args, tuple):
                        task = executor.submit(mapfunc, *args)
                    else:
                        task = executor.submit(mapfunc, args)
                    tasks[task] = args

                for task in concurrent.futures.as_completed(tasks):
                    args = tasks[task]
                    task_result = task.result()
                    if isinstance(args, list) or isinstance(args, dict):
                        args = str(args)
                    result[args] = task_result
            return result

        return wrapper

    def parallelize_multiprocess(self, mapfunc):
        """
        Parallelize the mapfunc with multiprocessing. Multi-process can make better
        use of multi-core than multi-thread
        Attention: the mapfun and args_list must be pickled， which means the
        mapfun can not be Closure or lambda
        Example:
        result = Processor().parallelize_multiprocess(function_1)(args)
        :param mapfunc:
        :type mapfunc:
        :return: func(args_list) => list[func[arg]]
        :rtype:
        """

        def wrapper(args_list):
            with Pool(self.workers) as pool:
                return pool.map(mapfunc, args_list)

        return wrapper
