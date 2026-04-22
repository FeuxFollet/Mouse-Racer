import math


def _catmull_chain(pts, steps=18):
    result = []
    n = len(pts)
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        for s in range(steps):
            t  = s / steps
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                2 * p1[0]
                + (-p0[0] + p2[0]) * t
                + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2
                + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                2 * p1[1]
                + (-p0[1] + p2[1]) * t
                + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2
                + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3
            )
            result.append((x, y))
    return result


def _seg_intersect(p1, p2, p3, p4):
    def cross2d(a, b):
        return a[0] * b[1] - a[1] * b[0]

    r  = (p2[0] - p1[0], p2[1] - p1[1])
    s  = (p4[0] - p3[0], p4[1] - p3[1])
    rxs = cross2d(r, s)
    if abs(rxs) < 1e-9:
        return False
    qp = (p3[0] - p1[0], p3[1] - p1[1])
    t  = cross2d(qp, s) / rxs
    u  = cross2d(qp, r) / rxs
    return 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0
