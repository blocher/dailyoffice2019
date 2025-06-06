from abc import ABCMeta
import logging

from .trace_call import trace_call


class AbstractTraceMeta(type):
    """
    An abstract metaclass for tracing classes
    """

    @classmethod
    def _filter_attribute(mcs, attribute_name, attribute_value):
        """
        decides whether the given attribute should be excluded from tracing or not
        """
        if attribute_name == '__module__':
            return True
        elif hasattr(attribute_value, '_trace_disable'):
            return True
        return False

    def __new__(mcs, name, bases, attrs, **kwargs):
        # *magic*: an educated guess is made on how the module that the
        # processed class is created in would get its logger.
        # It is assumed that the popular convention recommended by the
        # developers of standard library (`logger = logging.getLogger(__name__)`)
        # is used.
        target_logger = logging.getLogger(attrs['__module__'])

        for attribute_name in attrs:
            attribute_value = attrs[attribute_name]

            if mcs._filter_attribute(attribute_name, attribute_value):
                continue
            # attrs['__module__'] + '.' + attribute_name is worth logging

            # collect the `only` and `skip` sets from mro
            only = getattr(attribute_value, '_trace_only', None)
            skip = getattr(attribute_value, '_trace_skip', None)
            disable = False
            for base in bases:
                base_attribute_value = getattr(base, attribute_name, None)
                if base_attribute_value is None:
                    continue  # the base class did not define this
                if hasattr(base_attribute_value, '_trace_disable'):  # that's probably done by @disable_trace
                    # ex. inheriting from Abstract class, where getters are marked
                    disable = True
                    break
                only_candidates = getattr(base_attribute_value, '_trace_only', None)
                if only_candidates is not None:
                    if only is not None:
                        only.update(only_candidates)
                    else:
                        only = set(only_candidates)
                skip_candidates = getattr(base_attribute_value, '_trace_skip', None)  # is this 5 LOC clone worth refactoring?
                if skip_candidates is not None:
                    if skip is not None:
                        skip.update(skip_candidates)
                    else:
                        skip = set(skip_candidates)

            if disable:
                continue  # the base class does not wish to trace it at all

            # create a wrapper (decorator object)
            wrapper = trace_call(
                target_logger,
                only=only,
                skip=skip,
            )

            original_wrapper = None
            # Special case for staticmethod/classmethod
            if isinstance(attribute_value, staticmethod):
                attribute_value = attribute_value.__func__
                original_wrapper = staticmethod
            elif isinstance(attribute_value, classmethod):
                attribute_value = attribute_value.__func__
                original_wrapper = classmethod

            # wrap the callable in it
            wrapped_value = wrapper(attribute_value)

            # apply the original wrapper if provided
            if original_wrapper is not None:
                wrapped_value = original_wrapper(wrapped_value)
            # substitute the trace-wrapped method for the original
            attrs[attribute_name] = wrapped_value

        return super(AbstractTraceMeta, mcs).__new__(mcs, name, bases, attrs)


class TraceAllPublicCallsMeta(AbstractTraceMeta):
    """
    traces all public method calls
    """

    @classmethod
    def _filter_attribute(mcs, attribute_name, attribute_value):
        if super(TraceAllPublicCallsMeta, mcs)._filter_attribute(attribute_name, attribute_value):
            return True
        elif not callable(attribute_value):
            # Special case for staticmethod/classmethod as prior to Python 3.10
            # staticmethod/classmethod are not callable
            if not isinstance(attribute_value, (classmethod, staticmethod)):
                return True  # it is a field
        elif attribute_name.startswith('_'):
            return True  # it is a _protected or a __private method (or __magic__)

        return False


class AbstractTracePublicCallsMeta(ABCMeta, TraceAllPublicCallsMeta):
    pass


class DefaultTraceMeta(TraceAllPublicCallsMeta):
    """
    traces all public method calls, except for ones with names that begin with 'get_'
    """

    @classmethod
    def _filter_attribute(mcs, attribute_name, attribute_value):
        if super(DefaultTraceMeta, mcs)._filter_attribute(attribute_name, attribute_value):
            return True
        elif attribute_name.startswith('get_'):
            return True
        return False


class DefaultTraceAbstractMeta(ABCMeta, DefaultTraceMeta):
    pass
