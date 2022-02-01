const setCalendarDate = function ($route) {
  const yyyy = parseInt($route.params.year);
  const mm = parseInt($route.params.month);
  const dd = parseInt($route.params.day);
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
