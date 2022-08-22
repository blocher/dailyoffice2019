const setCalendarDate = function ($route) {
    const now = new Date();
    const nowMonth = now.getMonth() + 1;
    const nowDay = now.getDate();
    const nowYear = now.getFullYear();
    const yyyy = parseInt($route.params.year || nowYear);
    const mm = parseInt($route.params.month || nowMonth);
    const dd = parseInt($route.params.day || nowDay);
    const calendarDate = new Date(yyyy, mm - 1, dd);
    const validDate =
        calendarDate instanceof Date &&
        !isNaN(calendarDate) &&
        !isNaN(calendarDate.getTime());
    if (validDate) {
        return calendarDate;
    }
    return null;
};

export default setCalendarDate;
