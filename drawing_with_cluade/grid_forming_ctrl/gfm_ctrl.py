"""A2 drawing of the grid-forming control of TELEMA VFC0 (afe_dq_ctrl_pwm with the negative-sequence compensator).

python gfm_ctrl.py <out dir>  ->  gfm_ctrl.svg (fonts by name), gfm_ctrl_preview.html (fonts by file), gfm_ctrl.jsx
"""
import math
import os
import sys

from engine import Drawing, measure, to_svg, to_jsx

W, H = 1683.78, 1190.55           # A2 landscape [pt]
SW, SWV = 1.1, 2.4                # scalar / vector signal lines
FILL, FILL_N, SHADOW = 9, 24, 55  # block fill, compensator fill, shadow (black %)
FL, FB, FP = 16, 14, 12.5         # label, block, panel font sizes

d = Drawing(W, H)


# ---------------------------------------------------------------------------------------------- helpers
def block(x, y, w, h, lines, size=FB, fill=FILL, mode='rm', gap=1.32, shadow=True, title=None, tc=False):
    if shadow:
        d.rect(x + 3.2, y + 3.2, w, h, fill=SHADOW, stroke=None, sw=0)
    d.rect(x, y, w, h, fill=fill, stroke=100, sw=1.1)
    L = [(ln, size, mode) if isinstance(ln, str) else ln for ln in lines]
    hs = [ln[1] for ln in L]
    total = sum(hs[:-1])*gap if L else 0
    yy = y + h/2 - total/2
    for ln, s, m in L:
        d.text(ln, x + w/2, yy + 0.34*s, s, m, 'middle')
        yy += s*gap
    if title:
        d.text(title, x + w/2, y - 7, 13.5, 'bi', 'middle')
    if tc:
        tag_tc(x + w - 3, y + 3)


def tag_tc(xr, yt):
    w = measure('t_c', 10.5) + 8
    d.rect(xr - w, yt, w, 15, fill=0, stroke=100, sw=0.7, r=3)
    d.text('t_c', xr - w/2, yt + 11.3, 10.5, 'mt', 'middle')


def tblock(x, y, s, tl, br, fill=FILL):
    d.rect(x + 3.2, y + 3.2, s, s, fill=SHADOW, stroke=None, sw=0)
    d.rect(x, y, s, s, fill=fill, stroke=100, sw=1.1)
    d.path([(x, y + s), (x + s, y)], sw=0.9)
    d.text(tl, x + 6, y + 19, 15, 'mt')
    d.text(br, x + s - 6, y + s - 8, 15, 'mt', 'end')


def summ(cx, cy, signs, r=12):
    d.circle(cx, cy, r, fill=0, stroke=100, sw=1.1)
    pos = {'l': (cx - r - 8, cy - 7), 'r': (cx + r + 8, cy - 7), 't': (cx + 9, cy - r - 4), 'b': (cx + 9, cy + r + 15)}
    for side, sg in signs.items():
        px, py = pos[side]
        d.text('−' if sg == '-' else '+', px, py, 15, 'rm', 'middle')


def wire(pts, vec=False, dash=None, arrow=True, k=100):
    if arrow:
        d.arrow(pts, SWV if vec else SW, k, dash=dash)
    else:
        d.path(pts, sw=SWV if vec else SW, stroke=k, dash=dash)


def jump_v(x, y1, y2, crossings, vec=False, r=5):
    """Vertical line from y1 to y2 (y1 < y2) with jumper arcs over the horizontal lines at crossings."""
    sw = SWV if vec else SW
    pts = [(x, y1)]
    for yc in sorted(crossings):
        pts.append((x, yc - r))
        for i in range(1, 12):
            a = math.pi*i/12
            pts.append((x + r*math.sin(a), yc - r*math.cos(a)))
        pts.append((x, yc + r))
    pts.append((x, y2))
    return pts


def inductor(x1, x2, y, n=4):
    """Coil along y between x1 and x2 (humps upwards)."""
    w = (x2 - x1)/n
    pts = []
    for k in range(n):
        for i in range(13):
            a = math.pi*i/12
            pts.append((x1 + k*w + w/2 - w/2*math.cos(a), y - w/2*math.sin(a)))
    d.path(pts, sw=1.1)


def panel(x, y, w, h, title):
    d.rect(x, y, w, h, fill=5, stroke=60, sw=0.8)
    d.text(title, x + 10, y + 21, 13.5, 'bf')
    d.path([(x + 10, y + 29), (x + w - 10, y + 29)], stroke=60, sw=0.6)


def para(lines, x, y, size=FP, gap=1.5, mode='mt'):
    for ln in lines:
        if ln is None:
            y += size*gap*0.5
            continue
        if isinstance(ln, tuple):
            d.text(ln[0], x, y, ln[1] if len(ln) > 1 else size, ln[2] if len(ln) > 2 else mode)
        else:
            d.text(ln, x, y, size, mode)
        y += size*gap
    return y


# ---------------------------------------------------------------------------------------------- frame, title, legend
d.layer = 'frame'
d.rect(20, 20, W - 40, H - 40, stroke=70, sw=0.8)
d.text('Grid-forming converter control, TELEMA VFC0', 45, 70, 28, 'bf')
d.text('afe\\_dq\\_ctrl\\_pwm: MATLAB Function of the library block grid\\_forming\\_dqctrl (dev 57cdc00), as used by '
       'telema\\_vfc\\_s; GFM1 master, GFM2 slave;', 45, 96, 12.5, 'rm')
d.text('negative-sequence compensator on (nsc\\_enable = 1). Signal names as in the code, [n] = column of ctrl\\_log '
       '(grid\\_forming\\_log\\_index).', 45, 113, 12.5, 'rm')
d.text('Per unit: \\it{u}_{bez} = 326.6 V (phase peak), \\it{i}_{bez} = 777.8 A; voltages and currents of the '
       'control in pu.', 45, 130, 12.5, 'rm')

lx, ly = 1230, 42
d.rect(lx, ly, 415, 88, fill=0, stroke=60, sw=0.6)
wire([(lx + 12, ly + 18), (lx + 62, ly + 18)])
d.text('scalar signal', lx + 72, ly + 22, 12.5, 'rm')
wire([(lx + 12, ly + 40), (lx + 62, ly + 40)], vec=True)
d.text('vector: abc, \\it{αβ} or \\it{ξη} components', lx + 72, ly + 44, 12.5, 'rm')
wire([(lx + 12, ly + 62), (lx + 62, ly + 62)], dash=[5, 3])
d.text('sync link GFM1 → GFM2, trigger', lx + 72, ly + 66, 12.5, 'rm')
d.rect(lx + 250, ly + 9, 26, 17, fill=FILL_N, stroke=100, sw=0.9)
d.text('compensator', lx + 284, ly + 22, 12.5, 'rm')
tag_tc(lx + 276, ly + 34)
d.text('every \\it{t_c} = 1 µs', lx + 284, ly + 46, 12.5, 'rm')
d.text('else every \\it{t_s} = 200 µs', lx + 284, ly + 62, 12.5, 'rm')

# ---------------------------------------------------------------------------------------------- control step zone
d.layer = 'diagram'
d.begin('zone control step')
d.rect(40, 146, 1140, 560, fill=None, stroke=55, sw=0.9, dash=[7, 4], r=10)
d.text('control step: on the rising edge of TRGO, every \\it{t_s} = 1/(2\\it{f}_{\\rm{pwm}}) = 200 µs', 56, 168, 13, 'rm')
d.end()

yT, yI, yP, yN = 235, 410, 552, 650

# ---- current loop (top row)
d.begin('current loop')
summ(330, yT, {'l': '+', 'b': '-'})
wire([(342, yT), (385, yT)], vec=True)
d.dot(360, yT, 3.2)
wire([(360, yT), (360, 322), (385, 322)], vec=True)
block(385, 200, 135, 70, ['vector PI', ('k_{p,i},\\ k_{i,i}', 15, 'mt')])
block(385, 292, 135, 60, ['resonant, per axis', ('k_r s / (s^2 + (2ω)^2)', 14, 'mt')], fill=FILL_N)
d.text('\\vec{r}\\ [42,43]', 545, 345, FL)
summ(565, yT, {'l': '+', 'b': '+'})
wire([(520, yT), (553, yT)], vec=True)
wire([(520, 322), (565, 322), (565, yT + 12)], vec=True)
wire([(577, yT), (610, yT)], vec=True)
block(610, 205, 95, 60, ['limiter', ('|\\vec{m}| ≤ u_{\\rm{lim}}', 15, 'mt')])
wire([(705, yT), (750, yT)], vec=True)
d.text('\\vec{m}_{ξη}', 727, yT - 12, FL, anchor='middle')
d.text('[26,27]', 727, yT + 22, 11, 'rm', 'middle')
tblock(750, yT - 35, 70, 'ξη', 'αβ')
wire([(785, 300), (785, yT + 35)])
d.text('θ', 785, 316, FL, anchor='middle')
wire([(820, yT), (868, yT)], vec=True)
d.text('\\vec{m}_{αβ}', 844, yT - 12, FL, anchor='middle')
d.text('[29,30]', 844, yT + 22, 11, 'rm', 'middle')
# SVPWM with hexagon
block(868, 193, 120, 84, [], title='SVPWM')
cx, cy, R = 928, 235, 32
hexa = [(cx + R*math.cos(math.radians(60*i)), cy - R*math.sin(math.radians(60*i))) for i in range(6)]
d.path(hexa, True, sw=0.9)
for p in hexa:
    d.path([(cx, cy), p], sw=0.5, stroke=60)
d.arrow([(cx, cy), (cx + 19, cy - 13)], sw=1.0, head=(7, 2.6))
d.end()

d.begin('PWM and power stage')
wire([(988, yT), (1222, yT)], vec=True)
d.text('\\vec{d}_{abc}', 1105, yT - 12, FL, anchor='middle')
d.text('[31..33]', 1105, yT + 22, 11, 'rm', 'middle')
block(1222, 193, 120, 84, [], title='PWM', tc=True)
# carrier icon
px0, py0 = 1238, 258
tri = [(px0 + 22*i, py0 - (40 if i % 2 else 0)) for i in range(5)]
d.path(tri, sw=0.9)
d.path([(px0, py0 - 22), (px0 + 88, py0 - 22)], sw=0.8, dash=[3, 2])
wire([(1250, 318), (1250, 277)])
d.text('\\it{r}  (carrier)', 1258, 316, 13, 'rm')
wire([(1342, yT), (1392, yT)], vec=True)
d.text('\\it{G}_{1..6}', 1367, yT - 12, 14, 'rm', 'middle')
# bridge
block(1392, 175, 80, 120, [])
d.text('two-level bridge', 1432, 314, 12, 'rm', 'middle')
bx, by = 1432, 235
d.path([(bx - 8, by - 22), (bx - 8, by + 22)], sw=1.6)
d.path([(bx - 14, by - 14), (bx - 14, by + 14)], sw=1.1)
d.path([(bx - 22, by), (bx - 14, by)], sw=1.1)
d.path([(bx - 8, by - 10), (bx + 6, by - 20), (bx + 6, by - 32)], sw=1.1)
d.path([(bx - 8, by + 10), (bx + 6, by + 20), (bx + 6, by + 32)], sw=1.1)
d.arrow([(bx - 2, by + 14), (bx + 5, by + 19)], sw=0.8, head=(5, 2.2))
d.path([(bx + 6, by - 26), (bx + 20, by - 26), (bx + 20, by + 26), (bx + 6, by + 26)], sw=1.1)
d.path([(bx + 14, by + 5), (bx + 26, by + 5), (bx + 20, by - 5)], True, fill=100, stroke=100, sw=0.8)
d.path([(bx + 14, by - 5), (bx + 26, by - 5)], sw=1.1)
# DC link
for xx in (1412, 1452):
    d.path([(xx, 175), (xx, 150)], sw=1.1)
    d.circle(xx, 146, 3.5, fill=0, sw=0.9)
d.text('\\it{u}_{\\rm{dc}}', 1432, 148, 14, 'rm', 'middle')
# three-phase lines, LCL
ys = [207, 235, 263]
for yy in ys:
    d.path([(1472, yy), (1502, yy)], sw=1.1)
    inductor(1502, 1532, yy)
    d.path([(1532, yy), (1584, yy)], sw=1.1)
    inductor(1584, 1606, yy, n=3)
    d.path([(1606, yy), (1630, yy)], sw=1.1)
    d.circle(1633, yy, 3.2, fill=0, sw=0.9)
d.text('\\it{L_1}', 1517, 284, 13, 'rm', 'middle')
d.text('\\it{L_2}', 1595, 284, 13, 'rm', 'middle')
# filter branches (staggered, jumpers over the lower lines)
for i, xx in enumerate((1546, 1556, 1566)):
    yy = ys[i]
    d.dot(xx, yy, 2.4)
    cross = [y2 for y2 in ys if y2 > yy]
    d.path(jump_v(xx, yy, 300, cross, r=4), sw=1.0)
    # resistor (zigzag) and capacitor
    zz = [(xx, 300)] + [(xx + (4 if j % 2 else -4), 302 + 3*j) for j in range(1, 7)] + [(xx, 323), (xx, 330)]
    d.path(zz, sw=1.0)
    d.path([(xx - 7, 330), (xx + 7, 330)], sw=1.4)
    d.path([(xx - 7, 335), (xx + 7, 335)], sw=1.4)
    d.path([(xx, 335), (xx, 345)], sw=1.0)
d.path([(1546, 345), (1566, 345)], sw=1.0)
d.text('\\it{C}_{\\rm{F}}, \\it{R}_{\\rm{CF}}', 1556, 364, 12, 'rm', 'middle')
d.text('to a primary star of', 1645, 178, 12, 'rm', 'end')
d.text('the output transformer', 1645, 192, 12, 'rm', 'end')
# measurements: converter current after the bridge, terminal voltage before the terminals
for i, xx in enumerate((1480, 1486, 1492)):
    yy = ys[i]
    d.circle(xx, yy, 2.6, fill=0, sw=0.8)
    d.path(jump_v(xx, yy + 2.6, 360, [y2 for y2 in ys if y2 > yy], r=3.5), sw=0.8)
d.path([(1474, 360), (1498, 360)], sw=4)
for i, xx in enumerate((1612, 1618, 1624)):
    yy = ys[i]
    d.dot(xx, yy, 2.0)
    d.path(jump_v(xx, yy, 360, [y2 for y2 in ys if y2 > yy], r=3.5), sw=0.8)
d.path([(1606, 360), (1630, 360)], sw=4)
d.end()

# ---- current measurement (second row)
d.begin('current measurement')
wire([(1486, 360), (1486, yI), (1140, yI)], vec=True)
d.text('\\vec{i}_s^{abc}', 1310, yI - 12, FL, anchor='middle')
block(1040, yI - 25, 100, 50, ['sample', ('Q,\\ z^{−1}', 15, 'mt')])
wire([(1040, yI), (990, yI)], vec=True)
tblock(930, yI - 30, 60, 'abc', 'αβ')
wire([(930, yI), (860, yI)], vec=True)
d.text('\\vec{i}_{αβ}', 895, yI - 12, FL, anchor='middle')
tblock(800, yI - 30, 60, 'αβ', 'ξη')
wire([(830, yI + 72), (830, yI + 30)])
d.text('θ', 830, yI + 88, FL, anchor='middle')
wire([(800, yI), (330, yI), (330, yT + 12)], vec=True)
d.text('\\vec{i}_{ξη}', 600, yI - 12, FL, anchor='middle')
d.text('[24,25]', 600, yI + 22, 11, 'rm', 'middle')
d.end()

# ---- phase generator
d.begin('phase generator')
block(125, 300, 180, 62, ['phase generator', ('θ[k+1] = θ[k] + 2π f_o t_s', 13.5, 'mt')])
wire([(215, 362), (215, 388)])
d.text('θ \\rm{[5]}', 222, 388, 14)
wire([(215, 268), (215, 300)], dash=[5, 3])
d.text('slave: \\it{θ} = sync(1)', 222, 277, 11.5, 'rm')
para([('angle of all the frame transforms;', 11.5, 'rm'),
      ('\\it{f_o} = \\it{f}_{out}, free running', 11.5, 'rm')], 112, 434, 11.5, 1.35)
d.end()

# ---- voltage measurement, FHT, sequences (third and fourth rows)
d.begin('voltage measurement')
yA = 597
wire([(1618, 360), (1618, yA), (1140, yA)], vec=True)
d.text('\\vec{u}_g^{abc}', 1310, yA - 12, FL, anchor='middle')
block(1040, yA - 25, 100, 50, ['sample', ('Q,\\ z^{−1}', 15, 'mt')])
wire([(1040, yA), (1000, yA)], vec=True)
tblock(940, yA - 30, 60, 'abc', 'αβ')
ya, yb = 582, 612
wire([(940, ya), (880, ya)])
d.text('u_α', 910, ya - 6, FL, anchor='middle')
wire([(940, yb), (905, yb), (905, 642), (880, 642)])
d.text('u_β', 922, 606, FL, anchor='middle')
block(790, ya - 22, 90, 44, ['FHT', ('α', 13, 'mt')], gap=1.15)
block(790, 642 - 22, 90, 44, ['FHT', ('β', 13, 'mt')], gap=1.15)
for y0, ax in ((ya, 'α'), (642, 'β')):
    wire([(790, y0 - 10), (705, y0 - 10)])
    wire([(790, y0 + 10), (705, y0 + 10)])
    d.text('\\hat{u}_%s' % ax, 760, y0 - 14, 14.5, anchor='middle')
    d.text('\\hat{v}_%s' % ax, 760, y0 + 26, 14.5, anchor='middle')
d.text('[34,35]', 790 + 45, ya - 28, 11, 'rm', 'middle')
d.text('[36,37]', 790 + 45, 642 + 36, 11, 'rm', 'middle')
block(610, 527, 95, 148, ['sequence', 'calculation', ('½(\\hat{u} ± \\hat{v})', 14, 'mt')], gap=1.45)
d.end()

# ---- positive-sequence voltage loop
d.begin('positive-sequence voltage loop')
wire([(610, yP), (560, yP)], vec=True)
d.text('\\vec{u}^+_{αβ}', 585, yP - 12, FL, anchor='middle')
d.text('[16,17]', 585, yP + 22, 11, 'rm', 'middle')
tblock(500, yP - 30, 60, 'αβ', 'ξη')
wire([(530, yP + 60), (530, yP + 30)])
d.text('θ', 540, yP + 58, FL)
wire([(500, yP), (452, yP)], vec=True)
d.text('\\vec{u}^+_{ξη}', 476, yP - 12, FL, anchor='middle')
d.text('[19,20]', 476, yP + 22, 11, 'rm', 'middle')
summ(440, yP, {'r': '-', 't': '+'})
wire([(440, yP - 55), (440, yP - 12)], vec=True)
d.text('(u_{g,\\rm{ref}},\\ u_{η,\\rm{ref}}) = (1, 0)', 448, yP - 60, 13.5)
wire([(428, yP), (405, yP)], vec=True)
block(275, yP - 36, 130, 72, ['vector PI', ('k_{p,ug},\\ k_{i,ug}', 14, 'mt'),
                               ('|\\vec{i}^*_{\\rm{p}}| ≤ i_{\\rm{lim}}', 12.5, 'mt')], gap=1.4)
d.end()

# ---- negative-sequence voltage loop (compensator)
d.begin('negative-sequence voltage loop')
wire([(610, yN), (560, yN)], vec=True)
d.text('\\vec{u}^{−}_{αβ}', 585, yN - 12, FL, anchor='middle')
tblock(500, yN - 30, 60, 'αβ', 'ξη', fill=FILL_N)
wire([(530, yN + 52), (530, yN + 30)])
d.text('−θ', 540, yN + 52, FL)
wire([(500, yN), (452, yN)], vec=True)
d.text('\\vec{u}^{−}_{ξη}', 476, yN - 12, FL, anchor='middle')
d.text('[38,39]', 476, yN + 22, 11, 'rm', 'middle')
summ(440, yN, {'r': '-', 'b': '+'})
wire([(440, yN + 50), (440, yN + 12)], vec=True)
d.text('0', 450, yN + 50, 14, 'rm')
wire([(428, yN), (405, yN)], vec=True)
block(275, yN - 36, 130, 72, ['vector PI', ('k_{p,n},\\ k_{i,n}', 14, 'mt'),
                               ('|\\vec{i}^*_{\\rm{n}}| ≤ i_{\\rm{n,lim}}', 12.5, 'mt')], fill=FILL_N, gap=1.4)
d.end()

# ---- master/slave selection, rotation, sum of the references
d.begin('references')
for y0, nm in ((yP, '2:3'), (yN, '4:5')):
    wire([(275, y0), (245, y0)], vec=True)
    block(215, y0 - 15, 30, 30, [('M/S', 10, 'rm')], shadow=False)
wire([(230, yP + 48), (230, yP + 15)], dash=[5, 3])
d.text('slave: sync(2:3)', 238, yP + 50, 11.5, 'rm')
wire([(230, yN + 48), (230, yN + 15)], dash=[5, 3])
d.text('slave: sync(4:5)', 238, yN + 50, 11.5, 'rm')
d.text('\\vec{i}^*_{\\rm{p}}', 168, yP - 12, FL, anchor='middle')
d.text('[21,22]', 168, yP + 22, 11, 'rm', 'middle')
wire([(215, yP), (107, yP)], vec=True)
wire([(215, yN), (180, yN)], vec=True)
d.text('\\vec{i}^*_{\\rm{n}}', 198, yN - 12, FL, anchor='middle')
d.text('[40,41]', 198, yN + 22, 11, 'rm', 'middle')
block(112, yN - 25, 68, 50, [('e^{−j2θ}', 16, 'mt')], fill=FILL_N)
wire([(146, yN - 53), (146, yN - 25)])
d.text('θ', 132, yN - 34, FL, anchor='middle')
wire([(112, yN), (95, yN), (95, yP + 12)], vec=True)
summ(95, yP, {'r': '+', 'b': '+'})
wire([(95, yP - 12), (95, yT), (318, yT)], vec=True)
d.text('\\vec{i}^*_{ξη}', 150, yT - 12, FL, anchor='middle')
d.end()

# ---- master / slave note
d.begin('master slave note')
para([('GFM2 (slave = 1): \\it{θ}, \\it{i}^*_p, \\it{i}^*_n from sync,', 11, 'rm'),
      ('i.e. sync\\_out of GFM1; it runs acquisitions,', 11, 'rm'),
      ('FHT (log only), current loop and PWM; its', 11, 'rm'),
      ('phase generator and voltage PIs stay at rest.', 11, 'rm')],
     912, 652, 11, 1.32)
d.end()

# ---------------------------------------------------------------------------------------------- panels
d.layer = 'panels'
PY, PH = 725, 425
px = [40, 270, 500, 730, 960]
PW = 220
R_ = 'rm'

panel(px[0], PY, PW, PH, 'FHT, first harmonic tracker')
para([('per axis (\\it{α}, \\it{β}), resonant observer:', FP, R_),
      'A = [0, 1; −ω_0^2, −δω_0],\\ \\ C = [1, 0]',
      'ω_0 = 2π f_o,\\ \\ δ = 0.05',
      '\\rm{poles of} A − LC\\rm{:} (−1, −4)\\,ω_0',
      None,
      '\\rm{discrete (C code),} a = −ω_0^2,\\ b = −δω_0\\rm{:}',
      'a_{11} = 1 + ½ a t_s^2,\\ \\ a_{12} = t_s + ½ b t_s^2',
      'a_{21} = a t_s + ½ ab t_s^2',
      'a_{22} = 1 + b t_s + ½ (a + b^2) t_s^2',
      'e[k] = u[k] − \\hat{u}[k − 1]',
      'x_1 ← a_{11} x_1 + a_{12} x_2 + l_1 e',
      'x_2 ← a_{21} x_1 + a_{22} x_2 + l_2 e',
      '\\hat{u}[k] = x_1\\ \\rm{(before the update)}',
      '\\hat{v}[k] = x_2/ω_0\\ \\rm{(after the update)}',
      None,
      '\\hat{v}\\rm{: } \\hat{u} \\rm{ shifted by 90° (lead) at } f_o',
      '\\rm{reset (states 0) while } t < 12.5\\,\\rm{ms}'],
     px[0] + 10, PY + 52, FP - 0.5, 1.48)

panel(px[1], PY, PW, PH, 'sequences, frames, phase')
para(['u^+_α = ½ (\\hat{u}_α + \\hat{v}_β)',
      'u^+_β = ½ (\\hat{u}_β − \\hat{v}_α)',
      'u^{−}_α = ½ (\\hat{u}_α − \\hat{v}_β)',
      'u^{−}_β = ½ (\\hat{u}_β + \\hat{v}_α)',
      None,
      ('positive frame (\\it{θ}):', FP, R_),
      'u_ξ = u^+_α \\rm{cos}\\,θ + u^+_β \\rm{sin}\\,θ',
      'u_η = −u^+_α \\rm{sin}\\,θ + u^+_β \\rm{cos}\\,θ',
      ('negative frame (−\\it{θ}):', FP, R_),
      'u^{−}_ξ = u^{−}_α \\rm{cos}\\,θ − u^{−}_β \\rm{sin}\\,θ',
      'u^{−}_η = u^{−}_α \\rm{sin}\\,θ + u^{−}_β \\rm{cos}\\,θ',
      ('rotation \\it{e}^{−\\it{j}2\\it{θ}} into the positive frame:', FP, R_),
      'i^*_ξ = i^*_{ξ\\rm{p}} + c_2 i^*_{ξ\\rm{n}} + s_2 i^*_{η\\rm{n}}',
      'i^*_η = i^*_{η\\rm{p}} − s_2 i^*_{ξ\\rm{n}} + c_2 i^*_{η\\rm{n}}',
      'c_2 = \\rm{cos}\\,2θ,\\ \\ s_2 = \\rm{sin}\\,2θ',
      None,
      ('A negative sequence at \\it{f_o} is constant', FP - 1, R_),
      ('in the negative frame: the PIs see DC', FP - 1, R_),
      ('values; no average or notch filter.', FP - 1, R_)],
     px[1] + 10, PY + 52, FP - 0.5, 1.42)

panel(px[2], PY, PW, PH, 'vector PI with limiter')
mx, my = px[2] + 12, PY + 95
d.arrow([(mx, my), (mx + 26, my)], sw=1.8)
d.text('\\vec{e}', mx + 4, my - 8, 14)
d.dot(mx + 14, my, 2.6)
d.path([(mx + 14, my), (mx + 14, my + 46), (mx + 20, my + 46)], sw=1.8)
d.arrow([(mx + 19, my + 46), (mx + 26, my + 46)], sw=1.8)
d.rect(mx + 26, my - 12, 36, 24, fill=FILL, sw=0.9)
d.text('k_p', mx + 44, my + 5, 13, anchor='middle')
d.rect(mx + 26, my + 34, 36, 24, fill=FILL, sw=0.9)
d.text('k_i t_s', mx + 44, my + 51, 12, anchor='middle')
d.circle(mx + 82, my + 46, 7, fill=0, sw=0.9)
d.arrow([(mx + 62, my + 46), (mx + 75, my + 46)], sw=1.8)
d.rect(mx + 70, my + 68, 26, 20, fill=FILL, sw=0.9)
d.text('z^{−1}', mx + 83, my + 82, 11, anchor='middle')
d.path([(mx + 89, my + 46), (mx + 104, my + 46), (mx + 104, my + 78), (mx + 96, my + 78)], sw=1.8)
d.arrow([(mx + 70, my + 78), (mx + 63, my + 78), (mx + 63, my + 60), (mx + 77, my + 51)], sw=1.0, head=(6, 2.4))
d.text('x', mx + 108, my + 42, 13)
d.circle(mx + 126, my, 7, fill=0, sw=0.9)
d.arrow([(mx + 62, my), (mx + 119, my)], sw=1.8)
d.arrow([(mx + 104, my + 46), (mx + 126, my + 46), (mx + 126, my + 7)], sw=1.8)
d.arrow([(mx + 126, my - 30), (mx + 126, my - 7)], sw=1.8)
d.text('\\vec{f}', mx + 131, my - 24, 13)
d.rect(mx + 146, my - 14, 40, 28, fill=FILL, sw=0.9)
d.path([(mx + 150, my + 8), (mx + 158, my + 8), (mx + 174, my - 8), (mx + 182, my - 8)], sw=0.9)
d.arrow([(mx + 133, my), (mx + 146, my)], sw=1.8)
d.arrow([(mx + 186, my), (mx + 198, my)], sw=1.8)
d.text('\\vec{m}', mx + 188, my - 8, 13)
d.arrow([(mx + 166, my + 14), (mx + 166, my + 104), (mx + 83, my + 104), (mx + 83, my + 88)], sw=1.0, dash=[4, 2.5],
        head=(6, 2.4))
d.text('clip', mx + 172, my + 40, 11.5, 'rm')
d.text('hold', mx + 108, my + 98, 11.5, 'rm')
para(['m = k_p e + x + f',
      '\\rm{normal:}\\ \\ x ← x + k_i t_s e',
      '\\rm{clip:}\\ \\ x ← (1 − c_{\\rm{rel}} t_s)\\,x\\ \\ \\rm{(held)}',
      '|m| = \\rm{√}(m_ξ^2 + m_η^2)',
      'm ← m · lim/|m|\\ \\ \\rm{if}\\ |m| ≥ lim',
      '\\rm{clip} = (|m| ≥ thr)\\rm{, used next step}',
      None,
      ('voltage PI, compensator:', FP - 1, R_),
      ('lim = thr = 1.65\\,\\rm{pu}', FP - 1, 'mt'),
      ('current loop: \\it{lim} = \\it{thr} = \\it{u}_{lim} = 1', FP - 1, R_),
      ('\\it{f}: resonant terms in the current loop,', FP - 1, R_),
      ('0 in the voltage PIs', FP - 1, R_)],
     px[2] + 10, PY + 228, FP - 0.5, 1.42)

panel(px[3], PY, PW, PH, 'resonant term at 2\\it{f_o}')
para([('R(s) = k_r s/(s^2 + ω_r^2)', FP + 0.5, 'mt'),
      'ω_r = 2 · 2π f_o = 209.4\\,\\rm{rad/s}',
      'k_r = 2 k_{i,i} = 70\\,\\rm{s}^{−1}',
      None,
      '\\rm{discrete,} a = 2\\,\\rm{sin}(ω_r t_s/2)\\rm{:}',
      'x_1 ← x_1 + t_s k_r e − a x_2',
      'x_2 ← x_2 + a x_1\\ \\ \\rm{(new} x_1\\rm{)}',
      'r = x_1\\rm{, added to the PI output}',
      ('eigenvalues on the unit circle', FP, R_),
      ('at ±\\it{ω_r t_s}: resonance exactly at \\it{ω_r}', FP, R_),
      ('clip: input off, states × (1 − \\it{c}_{rel}\\it{t_s})', FP, R_),
      None,
      ('Why: \\it{i}^*_n \\it{e}^{−j2θ} is a sinusoid at 2\\it{f_o}', FP - 1, R_),
      ('in the positive frame; the PI alone', FP - 1, R_),
      ('would track it with an error. The PI', FP - 1, R_),
      ('tracks the DC part (positive sequence),', FP - 1, R_),
      ('the resonant term the negative', FP - 1, R_),
      ('sequence.', FP - 1, R_)],
     px[3] + 10, PY + 52, FP - 0.5, 1.45)

panel(px[4], PY, PW, PH, 'SVPWM, acquisitions')
hx, hy, HR = px[4] + 110, PY + 105, 52
hexa = [(hx + HR*math.cos(math.radians(60*i)), hy - HR*math.sin(math.radians(60*i))) for i in range(6)]
d.path(hexa, True, sw=1.0)
for i, p in enumerate(hexa):
    d.path([(hx, hy), p], sw=0.6, stroke=60)
    a = math.radians(60*i + 30)
    d.text(str(i + 1), hx + 0.74*HR*math.cos(a), hy - 0.74*HR*math.sin(a) + 4, 12, 'rm', 'middle')
d.arrow([(hx, hy), (hx + 27, hy - 8)], sw=1.4, head=(8, 3))
d.text('\\vec{m}', hx + 14, hy + 17, 13)
para(['\\rm{inputs} \\vec{m}_{αβ} · \\rm{√}3/2,\\ \\ k = (u_γ + 1)/2 = ½',
      ('sector 1:', FP, R_),
      't_1 = m_α − m_β/\\rm{√}3,\\ \\ t_2 = 2m_β/\\rm{√}3',
      't_0 = 1 − t_1 − t_2',
      'd_a = k t_0,\\ \\ d_b = d_a + t_1,\\ \\ d_c = d_b + t_2',
      ('upper switch on while \\it{r} ≥ \\it{d}', FP, R_),
      None,
      ('acquisitions on TRGO:', FP, R_),
      'x_q = q · \\rm{round}(x/q),\\ \\ q = 2^{−11}\\,\\rm{pu}',
      ('one step delay: the step uses the', FP, R_),
      ('samples of the previous TRGO;', FP, R_),
      ('\\it{i_g} with gain −1', FP, R_)],
     px[4] + 10, PY + 185, FP - 0.5, 1.45)

# timing (every tc) and parameters, right column
TX, TY, TW, TH = 1210, 622, 435, 310
panel(TX, TY, TW, TH, 'local clock, carrier, TRGO, gates (every \\it{t_c})')
para(['t_{\\rm{loc}} = t_{\\rm{master}} k_{\\rm{time}} (1 + \\rm{corr})',
      ('corr: PI 0.25, 18 s^{−1}, ±0.05 on \\it{t}_{master} − \\it{t}_{loc}, back-calculation', FP - 0.5, R_),
      'r = \\rm{asin}(\\rm{sin}(2π f_{\\rm{pwm}} t_{\\rm{loc}} − φ − π/2))/π + ½',
      ('TRGO: \\it{r} ≤ 2\\it{f}_{pwm}\\it{t_c} or \\it{r} ≥ 1 − 2\\it{f}_{pwm}\\it{t_c} (top and bottom)', FP - 0.5, R_),
      ('control step on its rising edge: \\it{t_s} = 1/(2\\it{f}_{pwm}) = 200 µs', FP - 0.5, R_),
      ('gates: upper on if \\it{r} ≥ \\it{d} + \\it{t}_{dead}\\it{f}_{pwm}, lower on if \\it{r} ≤ \\it{d} − \\it{t}_{dead}\\it{f}_{pwm}', FP - 0.5, R_),
      ('\\it{d} in [0.02, 0.98], \\it{t}_{dead} = 3 µs, gate +15 / −10 V', FP - 0.5, R_)],
     TX + 10, TY + 52, FP - 0.5, 1.42)
# timing chart: carrier, duty, TRGO, gates (two periods, dead time enlarged)
cx0, cy0, cw, ch = TX + 50, TY + 178, 330, 44
per = cw/2
dd, dt = 0.4, 0.07
def carrier(t):
    ph = t % 1.0
    return 2*ph if ph < 0.5 else 2 - 2*ph
d.path([(cx0 + i/120*cw, cy0 + ch - carrier(i/120*2)*ch) for i in range(121)], sw=1.0)
d.path([(cx0, cy0 + ch - dd*ch), (cx0 + cw, cy0 + ch - dd*ch)], sw=0.8, dash=[3, 2])
d.text('d', cx0 + cw + 5, cy0 + ch - dd*ch + 4, 12)
d.text('r', cx0 - 14, cy0 + 10, 12)
for k in range(5):
    xx = cx0 + k*per/2
    d.path([(xx, cy0 + ch + 5), (xx, cy0 + ch + 14)], sw=1.5)
d.text('TRGO', cx0 - 44, cy0 + ch + 14, 10.5, 'rm')
for lvl, name, on in ((cy0 + ch + 38, 'G^+', lambda r: r >= dd + dt), (cy0 + ch + 60, 'G^{−}', lambda r: r <= dd - dt)):
    pts = []
    for i in range(0, 1201):
        t = i/1200*2
        pts.append((cx0 + t*per, lvl - 11*(1 if on(carrier(t)) else 0)))
    q = [pts[0]]
    for p in pts[1:]:
        if abs(p[1] - q[-1][1]) > 1e-6:
            q.append((p[0], q[-1][1]))
        q.append(p)
    d.path(q, sw=1.0)
    d.text(name, cx0 - 30, lvl - 1, 12)
d.text('dead time enlarged', cx0 + cw - 2, cy0 + ch + 78, 10.5, 'rm', 'end')

PX2, PY2, PW2, PH2 = 1210, 942, 435, 208
panel(PX2, PY2, PW2, PH2, 'parameters (telema\\_vfc\\_s, GFM1 and GFM2)')
rows = [('f_o', '16.67 Hz'), ('f_{\\rm{pwm}}', '2.5 kHz, double update'), ('t_s,\\ t_c', '200 µs, 1 µs'),
        ('k_{p,ug},\\ k_{i,ug}', '0.5, 18 s^{−1}'), ('i_{\\rm{lim}}', '1.65 pu'),
        ('k_{p,n},\\ k_{i,n}', '0.5, 18 s^{−1}'), ('i_{\\rm{n,lim}}', '1.65 pu'),
        ('k_{p,i},\\ k_{i,i}', '0.4, 35 s^{−1}'), ('k_r', '70 s^{−1}'), ('u_{\\rm{lim}}', '1')]
rows2 = [('ω_0,\\ δ', '104.7 rad/s, 0.05'), ('l_1,\\ l_2', '0.100, 5.61'), ('c_{\\rm{rel}}', '0.001 s^{−1}'),
         ('q', '2^{−11} pu'), ('t_{\\rm{dead}}', '3 µs'), ('u_{g,\\rm{ref}}', '1 pu (400 V)'),
         ('u_{\\rm{bez}}', '326.6 V'), ('i_{\\rm{bez}}', '777.8 A'), ('\\rm{slave}', '0 (GFM1), 1 (GFM2)')]
for col, (xa, xb) in ((rows, (PX2 + 12, PX2 + 92)), (rows2, (PX2 + 222, PX2 + 282))):
    yy = PY2 + 50
    for (a, b) in col:
        d.text(a, xa, yy, FP - 0.5)
        d.text(b, xb, yy, FP - 0.5, 'rm')
        yy += 16


# ---------------------------------------------------------------------------------------------- output
out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
ai_base = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(out, 'gfm_ctrl')   # .ai and .pdf of the script
layers = ['frame', 'diagram', 'panels']
with open(os.path.join(out, 'gfm_ctrl.svg'), 'w', encoding='utf-8') as f:
    f.write(to_svg(d))
with open(os.path.join(out, 'gfm_ctrl_preview.html'), 'w', encoding='utf-8') as f:
    f.write('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:594mm 420mm;margin:0}'
            'html,body{margin:0;padding:0;background:#fff}svg{display:block}</style></head><body>'
            + to_svg(d, fontface=True).split('?>', 1)[1] + '</body></html>')
with open(os.path.join(out, 'gfm_ctrl.jsx'), 'w', encoding='utf-8') as f:
    f.write(to_jsx(d, ai_base, layers))
print('items', len(d.items), '->', ai_base)
