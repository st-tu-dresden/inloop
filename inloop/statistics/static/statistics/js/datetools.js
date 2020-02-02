
Date.prototype.plusHours = function(hours) {
  return new Date(this.getTime() + (hours * 60 * 60 * 1000));
};

Date.prototype.minusHours = function(hours) {
  return this.plusHours(-hours);
};

Date.prototype.startOfDay = function() {
  return new Date(
    this.getFullYear(),
    this.getMonth(),
    this.getDate(),
    0, 0, 0
  );
};

Date.prototype.endOfDay = function() {
  return new Date(
    this.getFullYear(),
    this.getMonth(),
    this.getDate(),
    23, 59, 59
  );
};
