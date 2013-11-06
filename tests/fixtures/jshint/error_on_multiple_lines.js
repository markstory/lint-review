"use strict";
// This file has undefined globals errors on two lines.
// This makes xml like line="x,y"
window.derp = function () {
	go = arguments[0];
	with (this) {
		boo = go;
	}
}
