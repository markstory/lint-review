function validRange (range: any) {
  return range.min <= range.middle && range.middle <= range.max;
}

const range = {
  middle: 10,
  min: 5,
  max: 20
};
