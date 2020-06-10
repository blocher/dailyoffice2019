/**
 * Convert an integer to a pipe(|)-separated list of flags
 * @param {number} n 
 * @param {Object} flag_map
 */
function map(n, flag_map) {
    const flags = [];
    for (let x = n, i=1; x; x >>>= 1) {
        if (x & 1) {
            flags.push(flag_map[i]);
        }
        i <<= 1;
    }
    return flags.join('|');
}

/**
 * Convert a pipe(|)-separated list of flags to an integer
 * @param {string} flags 
 * @param {Object} flag_map
 */
function unmap(flags, flag_map) {
    if (!flags) return 0;
    return flags.split('|').reduce((bits, flag) => bits |= flag_map[flag], 0);
}

module.exports = {
    map,
    unmap,
};
