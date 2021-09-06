import {Options} from 'p-map';

/**
Test whether *all* promises pass a testing function. Fulfills when *all* promises in `input` and ones returned from `testFunction` are fulfilled, or rejects if any of the promises reject.

@param input - Iterated over concurrently in the `testFunction` function.
@param testFunction - Predicate function, expected to return a `Promise<boolean>` or `boolean`.
@returns `true` if all promises passed the test and `false` otherwise.
 */
export default function pEvery<ValueType>(
	input: Iterable<PromiseLike<ValueType> | ValueType>,
	testFunction: (element: ValueType, index: number) => boolean | PromiseLike<boolean>,
	options?: Options
): Promise<boolean>;
