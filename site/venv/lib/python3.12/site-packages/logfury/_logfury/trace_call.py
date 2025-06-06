from collections import OrderedDict
from functools import wraps

import logging

from inspect import isclass, signature


class trace_call:
    """
    A decorator which causes the function execution to be logged using a passed logger
    """

    LEVEL = logging.DEBUG

    def __init__(self, logger, only=None, skip=None):
        """
            only - if not None, contains a whitelist (tuple of names) of arguments
                   that are safe to be logged. All others can not be logged.
            skip - if not None, contains a whitelist (tuple of names) of arguments
                   that are not safe to be logged.
        """
        self.logger = logger
        self.only = only
        self.skip = skip

    def __call__(self, callable_obj):
        is_class = isclass(callable_obj)
        if is_class:
            function = callable_obj.__init__
        else:
            function = callable_obj

        @wraps(function)
        def wrapper(*wrapee_args, **wrapee_kwargs):
            if self.logger.isEnabledFor(self.LEVEL):
                args_dict = OrderedDict()
                sig = signature(function)
                bound = sig.bind(*wrapee_args, **wrapee_kwargs)

                for param in sig.parameters.values():
                    if param.name not in bound.arguments:
                        args_dict[param.name] = param.default
                    else:
                        args_dict[param.name] = bound.arguments[param.name]

                if is_class:
                    args_dict.popitem(last=False)  # remove "self"

                # filter arguments
                output_arg_names = []
                skipped_arg_names = []
                if self.skip is not None and self.only is not None:
                    for arg in args_dict.keys():
                        if arg in self.only and arg not in self.skip:
                            output_arg_names.append(arg)
                        else:
                            skipped_arg_names.append(arg)
                elif self.only is not None:
                    for arg in args_dict.keys():
                        if arg in self.only:
                            output_arg_names.append(arg)
                        else:
                            skipped_arg_names.append(arg)
                elif self.skip is not None:
                    for arg in args_dict.keys():
                        if arg in self.skip:
                            skipped_arg_names.append(arg)
                        else:
                            output_arg_names.append(arg)
                else:
                    output_arg_names = args_dict

                # format output
                suffix = ''
                if skipped_arg_names:
                    suffix = ' (hidden args: {})'.format(', '.join(skipped_arg_names))
                arguments = ', '.join('{}={}'.format(k, repr(args_dict[k])) for k in output_arg_names)

                function_name = getattr(function, '__qualname__', function.__name__)
                if is_class:
                    function_name, *_ = function_name.rpartition('.')  # remove "__init__"

                # actually log the call
                self.logger.log(self.LEVEL, 'calling %s(%s)%s', function_name, arguments, suffix)
            return function(*wrapee_args, **wrapee_kwargs)

        if is_class:
            callable_obj.__init__ = wrapper
            return callable_obj
        else:
            return wrapper
