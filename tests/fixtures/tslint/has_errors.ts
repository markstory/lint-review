function validRange (range: any) {
  if (range.min < -3) {
    return false;
  }
  return range.min <= range.middle && range.middle <= range.max;
}

// Unsorted keys
const range = {
  min: 5,
  middle: 10,
  max: 20
};
