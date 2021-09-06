'use strict';
const pMap = require('p-map');

class EndError extends Error {}

const test = testFunction => async (element, index) => {
	const result = await testFunction(element, index);
	if (!result) {
		throw new EndError();
	}

	return result;
};

const pEvery = async (iterable, testFunction, opts) => {
	try {
		await pMap(iterable, test(testFunction), opts);
		return true;
	} catch (error) {
		if (error instanceof EndError) {
			return false;
		}

		throw error;
	}
};

module.exports = pEvery;
module.exports.default = pEvery;
