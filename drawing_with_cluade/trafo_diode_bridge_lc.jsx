// trafo_diode_bridge_lc.jsx
// Three-phase transformer (Dyn11) -> line inductors La, Lb, Lc -> 6-pulse diode bridge -> DC LC filter.
// All symbols are duplicated from reference_1.ai (same folder); only plain wires are drawn new,
// using the stroke settings copied from the reference wires.
// Run: Illustrator > File > Scripts > Other Script..., or via COM: app.DoJavaScriptFile(<this file>)
#target illustrator

var DIR = File($.fileName).parent.fsName.replace(/\\/g, "/");
var SRC = DIR + "/reference_1.ai";
var OUT = DIR + "/trafo_diode_bridge_lc";

var src = app.open(File(SRC));
var doc = app.documents.add(DocumentColorSpace.CMYK, 2000, 1500);
var lay = doc.layers[0];
lay.name = "schematic";

// ---------- helpers ----------
function near(a, b) { return Math.abs(a - b) < 0.6; }
// find a page item in the reference by its rounded geometric bounds [l, t, r, b]
function findIn(coll, gb, type) {
    for (var i = 0; i < coll.length; i++) {
        var it = coll[i], g = it.geometricBounds;
        if ((!type || it.typename == type) && near(g[0], gb[0]) && near(g[1], gb[1]) && near(g[2], gb[2]) && near(g[3], gb[3])) return it;
        if (it.typename == "GroupItem") { var r = findIn(it.pageItems, gb, type); if (r) return r; }
    }
    return null;
}
function ref(gb, type) {
    var it = findIn(src.layers[0].pageItems, gb, type);
    if (!it) throw new Error("reference object not found: " + gb.join(","));
    return it;
}
// duplicate a reference object into the new doc and move it so that its reference point (rx, ry,
// in reference coordinates) lands on (x, y)
function place(proto, rx, ry, x, y) {
    var d = proto.duplicate(lay, ElementPlacement.PLACEATEND);
    d.translate(x - rx, y - ry);
    return d;
}

// ---------- reference prototypes (bounds as listed by an inspection pass on reference_1.ai) ----------
var P = {
    trafo:   ref([-131.5, -75.2, 410.2, -386.6], "GroupItem"),  // 3-phase Dyn11 transformer incl. input terminals, ground, output leads
    coil:    ref([-225.1, -72.5, -162.7, -83.8], "GroupItem"),  // L_line inductor coil (wire level y=-78.1)
    smallO:  ref([-229.3, -76.4, -225.8, -79.9], "PathItem"),   // small open circle at inductor ends
    core1:   ref([615.7, -588.9, 655, -588.9], "PathItem"),     // L_Fu core lines
    core2:   ref([616, -591.8, 655.3, -591.8], "PathItem"),
    diode:   ref([1187.5, -488.8, 1202.3, -577.5], "GroupItem"),// brake-chopper diode, cathode on top, wire x=1194.9
    cap:     ref([1091.2, -597.9, 1127.2, -666.7], "GroupItem"),// C_Fi capacitor, wire x=1109.2
    dot:     ref([474.2, -598.2, 479.9, -603.9], "PathItem"),   // junction dot
    term:    ref([400.5, -653.1, 406.2, -658.7], "PathItem"),   // open terminal circle
    wire:    ref([406, -655.9, 598.7, -655.9], "PathItem"),     // plain wire (style source)
    varrow:  ref([1338.1, -497.3, 1338.1, -741.7], "PathItem"), // voltage arrow u_dc
    lblL:    ref([-211.3, -26.7, -193.8, -60.8], "TextFrame"),  // "L"  (main letter style)
    lblSub:  ref([-195.5, -44.9, -169.7, -64.7], "TextFrame"),  // "line" (subscript style)
    lblTr:   ref([-102.3, -7.9, 121, -58.2], "TextFrame")       // "Pn - Dyn11 ..." transformer caption
};

// duplicates keep their reference position, but absolute coordinates written into the new doc
// (setEntirePath, anchors) use the new doc's origin: measure the offset once and apply it there
var OFF = (function () {
    var t = P.dot.duplicate(lay, ElementPlacement.PLACEATEND);
    var o = [t.geometricBounds[0] - P.dot.geometricBounds[0], t.geometricBounds[1] - P.dot.geometricBounds[1]];
    t.remove();
    return o;
})();
function abs(x, y) { return [x + OFF[0], y + OFF[1]]; }

function wire(pts) {
    var w = P.wire.duplicate(lay, ElementPlacement.PLACEATEND);
    var q = [];
    for (var i = 0; i < pts.length; i++) q.push(abs(pts[i][0], pts[i][1]));
    w.setEntirePath(q);
    return w;
}
function dot(x, y) { return place(P.dot, 477.05, -601.05, x, y); }
function term(x, y) { return place(P.term, 403.35, -655.9, x, y); }
// label = main letter + subscript, same relative offset as "L_line" in the reference;
// (x, y) = top-left of the main letter
function label(main, sub, x, y) {
    var m = place(P.lblL, -211.3, -26.7, x, y);
    var r0 = m.geometricBounds[2];
    m.contents = main;
    var s = place(P.lblSub, -211.3, -26.7, x, y);
    s.contents = sub;
    // keep the subscript against the right edge of the (possibly wider) main letter
    s.translate(m.geometricBounds[2] - r0, 0);
    var g = lay.groupItems.add();
    s.move(g, ElementPlacement.PLACEATEND); m.move(g, ElementPlacement.PLACEATEND);
    return g;
}

// ---------- geometry ----------
// transformer kept at its reference coordinates; its secondary leads are at these levels
var YA = -78.7, YB = -107.8, YC = -134.1;
var X_COIL = 150;                       // left end of La/Lb/Lc coils
var COIL_W = 62.4;
var XL = [330, 410, 490];               // bridge legs a, b, c
var Y_RAIL_P = 50, Y_RAIL_N = -262.8;   // DC rails
var D_H = 88.7;                         // diode symbol height
var Y_UP_BOT = YA + 20, Y_UP_TOP = Y_UP_BOT + D_H;   // upper diodes
var Y_LO_TOP = YC - 20, Y_LO_BOT = Y_LO_TOP - D_H;   // lower diodes
var X_LDC = 560, X_CDC = 700, X_OUT = 780, X_VARR = 820;

// ---------- transformer ----------
var tr = place(P.trafo, 0, 0, 0, 0);
// shorten the three secondary output leads (they run to x=410.2 in the reference) to the coil inputs
(function trimLeads(g) {
    for (var i = 0; i < g.pageItems.length; i++) {
        var it = g.pageItems[i];
        if (it.typename == "GroupItem") { trimLeads(it); continue; }
        if (it.typename != "PathItem" || !near(it.geometricBounds[2], 410.2 + OFF[0])) continue;
        var pp = it.pathPoints;
        for (var k = 0; k < pp.length; k++) {
            var a = pp[k].anchor;
            if (near(a[0], 410.2 + OFF[0])) {
                var nx = X_COIL - 3.5 + OFF[0];
                pp[k].anchor = [nx, a[1]]; pp[k].leftDirection = [nx, a[1]]; pp[k].rightDirection = [nx, a[1]];
            }
        }
    }
})(tr);
var trLbl = place(P.lblTr, -102.3, -7.9, -60, -2);
trLbl.contents = "Dyn11";

// ---------- line inductors La, Lb, Lc ----------
var ys = [YA, YB, YC];
for (var i = 0; i < 3; i++) {
    place(P.coil, -225.1, -78.1, X_COIL, ys[i]);
    place(P.smallO, -229.3, -78.15, X_COIL - 3.5, ys[i]);
    place(P.smallO, -229.3, -78.15, X_COIL + COIL_W, ys[i]);
    // coil output -> its bridge leg
    wire([[X_COIL + COIL_W + 3.5, ys[i]], [XL[i], ys[i]]]);
    dot(XL[i], ys[i]);
}
label("L", "a,b,c", X_COIL + 14, YA + 44);

// ---------- 6-pulse diode bridge ----------
// upper diodes D1, D3, D5 (cathodes to + rail), lower diodes D4, D6, D2 (anodes to - rail)
var upN = ["1", "3", "5"], loN = ["4", "6", "2"];
for (var i = 0; i < 3; i++) {
    var x = XL[i];
    place(P.diode, 1194.9, -488.8, x, Y_UP_TOP);
    place(P.diode, 1194.9, -488.8, x, Y_LO_TOP);
    wire([[x, Y_RAIL_P], [x, Y_UP_TOP]]);
    wire([[x, Y_UP_BOT], [x, Y_LO_TOP]]);       // leg midpoint wire (phase lines tap here)
    wire([[x, Y_LO_BOT], [x, Y_RAIL_N]]);
    label("D", upN[i], x + 12, Y_UP_TOP - 22);
    label("D", loN[i], x + 12, Y_LO_TOP - 22);
    if (i > 0) { dot(x, Y_RAIL_P); dot(x, Y_RAIL_N); }
}

// ---------- DC rails, Ldc, Cdc, output ----------
wire([[XL[0], Y_RAIL_P], [X_LDC - 3.5, Y_RAIL_P]]);
place(P.coil, -225.1, -78.1, X_LDC, Y_RAIL_P);
place(P.smallO, -229.3, -78.15, X_LDC - 3.5, Y_RAIL_P);
place(P.smallO, -229.3, -78.15, X_LDC + COIL_W, Y_RAIL_P);
place(P.core1, 615.7, -588.9, X_LDC + 32 - 19.65, Y_RAIL_P + 13);
place(P.core2, 616, -591.8, X_LDC + 32 - 19.65, Y_RAIL_P + 10);
label("L", "dc", X_LDC + 18, Y_RAIL_P + 52);
wire([[X_LDC + COIL_W + 3.5, Y_RAIL_P], [X_OUT - 2.85, Y_RAIL_P]]);
wire([[XL[0], Y_RAIL_N], [X_OUT - 2.85, Y_RAIL_N]]);

var yMid = (Y_RAIL_P + Y_RAIL_N) / 2, CAP_H = 68.8;
place(P.cap, 1109.2, -597.9, X_CDC, yMid + CAP_H / 2);
wire([[X_CDC, Y_RAIL_P], [X_CDC, yMid + CAP_H / 2 - 3.5]]);
wire([[X_CDC, yMid - CAP_H / 2 + 3.5], [X_CDC, Y_RAIL_N]]);
dot(X_CDC, Y_RAIL_P); dot(X_CDC, Y_RAIL_N);
label("C", "dc", X_CDC + 22, yMid + 18);

term(X_OUT, Y_RAIL_P); term(X_OUT, Y_RAIL_N);
var tp = place(P.lblL, -211.3, -26.7, X_OUT - 8, Y_RAIL_P + 38); tp.contents = "+";
var tn = place(P.lblL, -211.3, -26.7, X_OUT - 6, Y_RAIL_N - 8); tn.contents = String.fromCharCode(0x2013);
var va = P.varrow.duplicate(lay, ElementPlacement.PLACEATEND);
va.pathPoints[0].anchor = abs(X_VARR, Y_RAIL_P - 8);
va.pathPoints[1].anchor = abs(X_VARR, Y_RAIL_N + 8);
for (var k = 0; k < 2; k++) { va.pathPoints[k].leftDirection = va.pathPoints[k].anchor; va.pathPoints[k].rightDirection = va.pathPoints[k].anchor; }
label("V", "dc", X_VARR + 10, yMid + 18);

// ---------- finish: fit artboard, save, export ----------
src.close(SaveOptions.DONOTSAVECHANGES);
app.activeDocument = doc;
var vb = doc.visibleBounds, M = 30;
doc.artboards[0].artboardRect = [vb[0] - M, vb[1] + M, vb[2] + M, vb[3] - M];

doc.saveAs(File(OUT + ".ai"), new IllustratorSaveOptions());
var eo = new EPSSaveOptions(); eo.embedAllFonts = true; eo.preview = EPSPreview.TRANSPARENTCOLORTIFF;
doc.saveAs(File(OUT + ".eps"), eo);
var po = new ExportOptionsPNG24(); po.antiAliasing = true; po.transparency = false; po.artBoardClipping = true;
po.horizontalScale = 150; po.verticalScale = 150;
doc.exportFile(File(OUT + ".png"), ExportType.PNG24, po);
doc.close(SaveOptions.DONOTSAVECHANGES);
"ok";
