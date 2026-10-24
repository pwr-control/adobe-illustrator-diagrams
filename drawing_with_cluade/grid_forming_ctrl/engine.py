"""Small drawing engine: primitives in pt (y down), math-like labels with CMU Serif, SVG and Illustrator JSX output.

Labels use a small markup: _x / _{..} subscript, ^x / ^{..} superscript, \\hat{x}, \\vec{x}, \\bar{x} accents,
\\rm{..} upright, \\it{..} italic, \\bf{..} bold, \\, thin space, \\quad. In math mode letters are italic and the
rest upright; characters missing in CMU Serif (minus, arrows, <=, x) come from Times New Roman.
"""
import math
import os
from fontTools.ttLib import TTFont

FD = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")
FONTS = {   # key: (PostScript name, family, style, weight, file)
    'rm': ('CMUSerif-Roman', 'CMU Serif', 'normal', 'normal', os.path.join(FD, 'cmunrm.ttf')),
    'it': ('CMUSerif-Italic', 'CMU Serif', 'italic', 'normal', os.path.join(FD, 'cmunti.ttf')),
    'bf': ('CMUSerif-Bold', 'CMU Serif', 'normal', 'bold', os.path.join(FD, 'cmunbx.ttf')),
    'bi': ('CMUSerif-BoldItalic', 'CMU Serif', 'italic', 'bold', os.path.join(FD, 'cmunbi.ttf')),
    'sy': ('TimesNewRomanPSMT', 'Times New Roman', 'normal', 'normal', r'C:\Windows\Fonts\times.ttf'),
    'si': ('TimesNewRomanPS-ItalicMT', 'Times New Roman', 'italic', 'normal', r'C:\Windows\Fonts\timesi.ttf'),
}
ITALIC_SLANT = math.tan(math.radians(14.04))


class Metrics:
    def __init__(self, path):
        t = TTFont(path)
        self.upm = t['head'].unitsPerEm
        self.cmap = t.getBestCmap()
        self.hmtx = t['hmtx'].metrics
        self.glyf = t['glyf']

    def has(self, ch):
        return ord(ch) in self.cmap

    def adv(self, ch, size):
        return self.hmtx[self.cmap[ord(ch)]][0]/self.upm*size

    def bbox(self, ch, size):
        g = self.glyf[self.cmap[ord(ch)]]
        if not hasattr(g, 'xMin'):
            return (0.0, 0.0, 0.0, 0.0)
        s = size/self.upm
        return (g.xMin*s, g.yMin*s, g.xMax*s, g.yMax*s)


MET = {k: Metrics(v[4]) for k, v in FONTS.items()}


# ---------------------------------------------------------------------------------------------- markup
def parse(s):
    pos = [0]

    def seq(end=None):
        items = []
        while pos[0] < len(s):
            c = s[pos[0]]
            if end is not None and c == end:
                pos[0] += 1
                return items
            if c == '\\':
                j = pos[0] + 1
                while j < len(s) and s[j].isalpha():
                    j += 1
                cmd = s[pos[0] + 1:j]
                pos[0] = j
                if cmd == '':
                    ch = s[pos[0]]
                    pos[0] += 1
                    if ch == ',':
                        items.append(('space', 0.17))
                    elif ch == ' ':
                        items.append(('space', 0.3))
                    else:
                        items.append(('char', ch))
                elif cmd in ('rm', 'it', 'bf', 'bi', 'mt'):
                    assert s[pos[0]] == '{', s
                    pos[0] += 1
                    items.append(('style', cmd, seq('}')))
                elif cmd in ('hat', 'vec', 'bar'):
                    assert s[pos[0]] == '{', s
                    pos[0] += 1
                    items.append(('accent', cmd, seq('}')))
                elif cmd == 'quad':
                    items.append(('space', 1.0))
                else:
                    raise ValueError('unknown command \\%s in %r' % (cmd, s))
            elif c in '_^':
                pos[0] += 1
                if s[pos[0]] == '{':
                    pos[0] += 1
                    arg = seq('}')
                else:
                    arg = [('char', s[pos[0]])]
                    pos[0] += 1
                prev = items.pop() if items else ('char', '')
                if prev[0] == 'script':
                    base, sub, sup = prev[1], prev[2], prev[3]
                else:
                    base, sub, sup = prev, None, None
                if c == '_':
                    sub = arg
                else:
                    sup = arg
                items.append(('script', base, sub, sup))
            else:
                items.append(('char', c))
                pos[0] += 1
        return items
    return seq()


GREEK_LC = set('αβγδεζηθικλμνξοπρστυφχψωϑϕ')


def char_font(ch, mode):
    if mode == 'mt':                       # math
        f = 'it' if (ch.isalpha() and ch not in 'ΔΣΩΓΘΛΞΠΦΨ') else 'rm'
    else:
        f = mode
    if ch in GREEK_LC and f in ('it', 'bi'):
        return 'si'                        # the italic alpha of CMU Serif looks like an a: Times New Roman Italic
    if ch == 'µ':
        return 'rm'
    if not MET[f].has(ch):
        f = 'si' if f in ('it', 'bi') and MET['si'].has(ch) else 'sy'
        if not MET[f].has(ch):
            raise ValueError('no glyph for %r (U+%04X)' % (ch, ord(ch)))
    return f


class Layout:
    """Runs (text pieces) and accent paths of one label, positions relative to the start of the baseline."""

    def __init__(self):
        self.runs = []      # [x, y, text, font, size]
        self.paths = []     # (points, stroke width, filled)
        self.x = 0.0
        self.acc_right = None   # right end of the last accent, to keep a superscript clear of it

    def put(self, ch, y, size, font):
        r = self.runs[-1] if self.runs else None
        if r and r[3] == font and r[4] == size and abs(r[1] - y) < 1e-9 and abs(r[0] + r[5] - self.x) < 1e-6:
            r[2] += ch
            r[5] += MET[font].adv(ch, size)
        else:
            self.runs.append([self.x, y, ch, font, size, MET[font].adv(ch, size)])
        self.x += MET[font].adv(ch, size)

    def items(self, items, y, size, mode):
        for it in items:
            k = it[0]
            if k == 'char':
                if it[1]:
                    self.put(it[1], y, size, char_font(it[1], mode))
            elif k == 'space':
                self.x += it[1]*size
            elif k == 'style':
                self.items(it[2], y, size, it[1])
            elif k == 'accent':
                x0 = self.x
                n0 = len(self.runs)
                self.items(it[2], y, size, mode)
                ch = it[2][0][1] if it[2] and it[2][0][0] == 'char' else 'x'
                font = self.runs[n0][3] if len(self.runs) > n0 else 'it'
                xmin, ymin, xmax, ymax = MET[font].bbox(ch, size)
                slant = ITALIC_SLANT if font in ('it', 'bi', 'si') else 0.0
                top = y - max(ymax, 0.45*size)
                cx = x0 + (xmin + xmax)/2 + slant*max(ymax, 0.45*size)*0.9
                sw = 0.055*size
                if it[1] == 'hat':
                    w, h, g = 0.36*size, 0.14*size, 0.07*size
                    self.paths.append(([(cx - w/2, top - g), (cx, top - g - h), (cx + w/2, top - g)], sw, False))
                elif it[1] == 'bar':
                    w, g = 0.5*size, 0.1*size
                    self.paths.append(([(cx - w/2, top - g), (cx + w/2, top - g)], sw, False))
                else:   # vec
                    w, g, ah = 0.62*size, 0.16*size, 0.13*size
                    yy = top - g
                    self.paths.append(([(cx - w/2, yy), (cx + w/2 - 0.5*ah, yy)], sw, False))
                    self.paths.append(([(cx + w/2, yy), (cx + w/2 - ah, yy - 0.42*ah), (cx + w/2 - ah, yy + 0.42*ah)], 0, True))
                self.acc_right = cx + w/2
            elif k == 'script':
                base, sub, sup = it[1], it[2], it[3]
                self.acc_right = None
                self.items([base], y, size, mode)
                acc_right = self.acc_right if base[0] == 'accent' else None
                base_font = self.runs[-1][3] if self.runs else 'rm'
                ss = 0.7*size
                x0 = self.x
                w = 0.0
                if sup is not None:
                    self.x = x0 + (0.04*size if base_font in ('it', 'bi', 'si') else 0.0)
                    if acc_right is not None:
                        self.x = max(self.x, acc_right + 0.04*size)
                    self.items(sup, y - 0.42*size, ss, mode)
                    w = max(w, self.x - x0)
                if sub is not None:
                    self.x = x0 - (0.03*size if base_font in ('it', 'bi') else 0.0)
                    self.items(sub, y + 0.24*size, ss, mode)
                    w = max(w, self.x - x0)
                self.x = x0 + w + 0.02*size


def measure(s, size, mode='mt'):
    lay = Layout()
    lay.items(parse(s), 0.0, size, mode)
    return lay.x


# ---------------------------------------------------------------------------------------------- drawing
class Drawing:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.items = []
        self.layer = 'diagram'
        self.group = None
        self.ngroup = 0

    def begin(self, name):
        self.ngroup += 1
        self.group = '%03d %s' % (self.ngroup, name)

    def end(self):
        self.group = None

    def add(self, **kw):
        kw.setdefault('layer', self.layer)
        kw.setdefault('group', self.group)
        self.items.append(kw)

    # ---- primitives (k = black percentage, None = none)
    def path(self, pts, closed=False, stroke=100, sw=1.0, fill=None, dash=None, cap='butt', join='miter'):
        # Illustrator refuses consecutive equal anchors (setEntirePath: Illegal Argument): drop them, and the middle
        # points of straight runs, which only make the paths long
        q = []
        for x, y in pts:
            p = (round(float(x), 3), round(float(y), 3))
            if q and abs(p[0] - q[-1][0]) < 1e-3 and abs(p[1] - q[-1][1]) < 1e-3:
                continue
            if len(q) >= 2:
                (ax, ay), (bx, by) = q[-2], q[-1]
                cross = (bx - ax)*(p[1] - by) - (by - ay)*(p[0] - bx)
                dot = (bx - ax)*(p[0] - bx) + (by - ay)*(p[1] - by)
                if abs(cross) < 1e-6 and dot > 0:
                    q[-1] = p
                    continue
            q.append(p)
        if closed and len(q) > 2 and abs(q[0][0] - q[-1][0]) < 1e-3 and abs(q[0][1] - q[-1][1]) < 1e-3:
            q.pop()
        if len(q) < 2:
            return
        self.add(type='path', pts=q, closed=closed, stroke=stroke, sw=sw, fill=fill, dash=dash, cap=cap, join=join)

    def rect(self, x, y, w, h, fill=None, stroke=100, sw=1.0, dash=None, r=0):
        if r <= 0:
            self.path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True, stroke, sw, fill, dash)
        else:
            pts = []
            for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
                for i in range(7):
                    a = math.radians(a0 + 15*i)
                    pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
            self.path(pts, True, stroke, sw, fill, dash)

    def circle(self, cx, cy, r, fill=None, stroke=100, sw=1.0, n=40):
        self.path([(cx + r*math.cos(2*math.pi*i/n), cy + r*math.sin(2*math.pi*i/n)) for i in range(n)], True, stroke, sw, fill)

    def text(self, s, x, y, size=15, mode='mt', anchor='start', k=100):
        lay = Layout()
        lay.items(parse(s), 0.0, size, mode)
        dx = {'start': 0.0, 'middle': -lay.x/2, 'end': -lay.x}[anchor]
        for rx, ry, txt, font, sz, _ in lay.runs:
            self.add(type='text', x=x + dx + rx, y=y + ry, text=txt, font=font, size=sz, k=k)
        for pts, sw, filled in lay.paths:
            q = [(x + dx + px, y + py) for px, py in pts]
            if filled:
                self.path(q, True, None, 0, k)
            else:
                self.path(q, False, k, sw, None, cap='round', join='round')
        return lay.x

    # ---- symbols
    def arrow(self, pts, sw=1.1, k=100, head=None, dash=None, start_head=False):
        hl, hw = head if head else (9.0 + 1.6*sw, 3.2 + 1.0*sw)
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1)/L, (y2 - y1)/L
        q = list(pts[:-1]) + [(x2 - ux*hl*0.8, y2 - uy*hl*0.8)]
        self.path(q, False, k, sw, None, dash)
        self.path([(x2, y2), (x2 - ux*hl - uy*hw, y2 - uy*hl + ux*hw), (x2 - ux*hl + uy*hw, y2 - uy*hl - ux*hw)], True, None, 0, k)

    def dot(self, x, y, r=2.6, k=100):
        self.circle(x, y, r, fill=k, stroke=None, sw=0, n=24)


def gray(k):
    v = round(255*(1 - k/100))
    return 'rgb(%d,%d,%d)' % (v, v, v)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def to_svg(d, fontface=False):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="%.2fpt" height="%.2fpt" viewBox="0 0 %.2f %.2f">'
           % (d.w, d.h, d.w, d.h)]
    if fontface:
        out.append('<style>')
        for k, (ps, fam, st, wt, f) in FONTS.items():
            out.append("@font-face{font-family:'%s';font-style:%s;font-weight:%s;src:url('file:///%s');}"
                       % (fam, st, wt, f.replace('\\', '/')))
        out.append('</style>')
    out.append('<rect x="0" y="0" width="%.2f" height="%.2f" fill="white"/>' % (d.w, d.h))
    layer = None
    group = None
    for it in d.items:
        if it['layer'] != layer or it['group'] != group:
            if group is not None:
                out.append('</g>')
            if it['layer'] != layer:
                if layer is not None:
                    out.append('</g>')
                out.append('<g id="%s">' % esc(it['layer']))
                layer = it['layer']
            group = it['group']
            if group is not None:
                out.append('<g id="%s">' % esc(group.replace(' ', '_')))
        if it['type'] == 'path':
            pts = it['pts']
            dd = 'M ' + ' L '.join('%.2f %.2f' % p for p in pts) + (' Z' if it['closed'] else '')
            attr = ['d="%s"' % dd, 'fill="%s"' % (gray(it['fill']) if it['fill'] is not None else 'none')]
            if it['stroke'] is not None and it['sw'] > 0:
                attr += ['stroke="%s"' % gray(it['stroke']), 'stroke-width="%.2f"' % it['sw'],
                         'stroke-linecap="%s"' % it['cap'], 'stroke-linejoin="%s"' % it['join']]
                if it['dash']:
                    attr.append('stroke-dasharray="%s"' % ' '.join('%.1f' % v for v in it['dash']))
            out.append('<path %s/>' % ' '.join(attr))
        else:
            ps, fam, st, wt, _ = FONTS[it['font']]
            out.append('<text x="%.2f" y="%.2f" font-family="%s" font-style="%s" font-weight="%s" font-size="%.2f" '
                       'fill="%s" xml:space="preserve">%s</text>'
                       % (it['x'], it['y'], fam, st, wt, it['size'], gray(it['k']), esc(it['text'])))
    if group is not None:
        out.append('</g>')
    if layer is not None:
        out.append('</g>')
    out.append('</svg>')
    return '\n'.join(out)


def js_str(s):
    return '"' + ''.join(c if 32 <= ord(c) < 127 and c not in '"\\' else '\\u%04x' % ord(c) for c in s) + '"'


def to_jsx(d, out_base, layers):
    """Illustrator script: new CMYK document of the drawing size, one layer per entry of layers, one group per
    group of the drawing; saves out_base.ai (PDF compatible) and out_base.pdf and closes the new document. The other
    open documents are not touched; the alert level and coordinate system of the user come back also after an error.
    """
    head = ['#target illustrator',
            '// generated by gfm_ctrl.py: coordinates in pt, y up from the top of the artboard (y of the drawing negated)',
            'var UIL = app.userInteractionLevel, CS = app.coordinateSystem;',
            'var doc = null, LAY = {}, GR = {}, FONT = {}, RESULT = "done", NP = 0, NT = 0;',
            'function K(k){ var c = new CMYKColor(); c.cyan = 0; c.magenta = 0; c.yellow = 0; c.black = k; return c; }',
            'function F(n){ if(!FONT[n]){ FONT[n] = app.textFonts.getByName(n); } return FONT[n]; }',
            'function G(lay, g){ if(g === null){ return LAY[lay]; } var key = lay + "|" + g;',
            '  if(!GR[key]){ GR[key] = LAY[lay].groupItems.add(); GR[key].name = g; } return GR[key]; }',
            'function P(c, pts, closed, sk, sw, fk, dash, cap, join){',
            '  NP++; var p = c.pathItems.add(), q = [];',
            '  for(var i = 0; i < pts.length; i += 2){ q.push([pts[i], -pts[i + 1]]); }',
            '  try { p.setEntirePath(q); } catch (e) { throw new Error("path " + NP + " of " + q.length + " points from " + q[0] + ": " + e); }',
            '  p.closed = closed;',
            '  if(fk === null){ p.filled = false; } else { p.filled = true; p.fillColor = K(fk); }',
            '  if(sk === null || sw <= 0){ p.stroked = false; } else { p.stroked = true; p.strokeColor = K(sk); p.strokeWidth = sw;',
            '    p.strokeCap = cap == "round" ? StrokeCap.ROUNDENDCAP : StrokeCap.BUTTENDCAP;',
            '    p.strokeJoin = join == "round" ? StrokeJoin.ROUNDENDJOIN : StrokeJoin.MITERENDJOIN;',
            '    if(dash){ p.strokeDashes = dash; } }',
            '  return p; }',
            'function T(c, s, x, y, font, size, k){',
            '  NT++; try {',
            '  var t = c.textFrames.pointText([x, -y]); t.contents = s;',
            '  var a = t.textRange.characterAttributes; a.textFont = F(font); a.size = size; a.fillColor = K(k);',
            '  a.tracking = 0; a.kerningMethod = AutoKernType.NOAUTOKERN;',
            '  } catch (e) { throw new Error("text " + NT + " (" + s + ", " + font + "): " + e); }',
            '  return t; }']
    body = ['app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;',
            'doc = app.documents.add(DocumentColorSpace.CMYK, %.2f, %.2f);' % (d.w, d.h),
            'app.coordinateSystem = CoordinateSystem.ARTBOARDCOORDINATESYSTEM;',
            'doc.layers[0].name = %s; LAY[%s] = doc.layers[0];' % (js_str(layers[0]), js_str(layers[0]))]
    for name in layers[1:]:
        body.append('LAY[%s] = doc.layers.add(); LAY[%s].name = %s;' % (js_str(name), js_str(name), js_str(name)))
    for it in d.items:
        c = 'G(%s, %s)' % (js_str(it['layer']), 'null' if it['group'] is None else js_str(it['group']))
        if it['type'] == 'path':
            pts = ','.join('%.2f,%.2f' % p for p in it['pts'])
            body.append('P(%s, [%s], %s, %s, %.2f, %s, %s, "%s", "%s");' % (
                c, pts, 'true' if it['closed'] else 'false',
                'null' if it['stroke'] is None else '%g' % it['stroke'], it['sw'],
                'null' if it['fill'] is None else '%g' % it['fill'],
                'null' if not it['dash'] else '[%s]' % ','.join('%g' % v for v in it['dash']), it['cap'], it['join']))
        else:
            body.append('T(%s, %s, %.2f, %.2f, "%s", %.2f, %g);' % (c, js_str(it['text']), it['x'], it['y'],
                                                                    FONTS[it['font']][0], it['size'], it['k']))
    ob = out_base.replace('\\', '/')
    body += ['var ai = new IllustratorSaveOptions(); ai.pdfCompatible = true; ai.embedICCProfile = false;',
             'doc.saveAs(new File(%s), ai);' % js_str(ob + '.ai'),
             'var pdf = new PDFSaveOptions(); pdf.preserveEditability = false; pdf.viewAfterSaving = false;',
             'doc.saveAs(new File(%s), pdf);' % js_str(ob + '.pdf'),
             'doc.close(SaveOptions.DONOTSAVECHANGES); doc = null;']
    out = head + ['try {'] + ['  ' + ln for ln in body] + \
        ['} catch (e) {',
         '  RESULT = "error: " + e + " (line " + e.line + ")";',
         '  try { if (doc) { doc.close(SaveOptions.DONOTSAVECHANGES); } } catch (e2) {}',
         '}',
         'app.coordinateSystem = CS; app.userInteractionLevel = UIL;',
         'RESULT;']
    return '\n'.join(out) + '\n'
