(function () {
	"use strict";
	var foo = 1 + 1;
	var thing = function() {
		foo += 1;
	};
	if (foo === null) {
		thing();
	}
}());
