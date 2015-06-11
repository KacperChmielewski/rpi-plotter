import math


def sign(num):
    """Returns -1 or 1 depending on sign of passed number"""
    return int(math.copysign(1, float(num)))


def afb(a, b, c):
    """Returns the angle from border"""
    alfa = (b ** 2 + c ** 2 - a ** 2) / (2 * b * c)
    alfa = math.acos(alfa)
    alfa *= (180 / math.pi)
    return alfa


def ctl(c, m1p, m2p):
    """Converts coordinates to length"""
    m1 = math.sqrt((c[0] - m1p[0]) ** 2 + (c[1] - m1p[1]) ** 2)
    m2 = math.sqrt((c[0] - m2p[0]) ** 2 + (c[1] - m2p[1]) ** 2)
    return [m1, m2]


def ltc(l, m1p, m2p):
    """Converts length to coordinates"""
    nround = 99
    c = math.sqrt((m1p[0] - m2p[0]) ** 2 + (m1p[1] - m2p[1]) ** 2)
    alfa = afb(l[1], c, l[0])
    beta = afb(math.fabs(m2p[1] - m1p[1]), c, math.fabs(m2p[0] - m1p[0]))
    if m1p[1] <= m2p[1]:
        gamma = 90 - alfa - beta
    else:
        gamma = 90 - alfa + beta
    rgamma = gamma * math.pi / 180
    pa = math.cos(rgamma) * l[0]
    pb = math.sqrt(l[0] ** 2 - pa ** 2)
    return round(pb + m1p[0], nround), round(pa + m1p[1], nround)


def distance(p1, p2):
    return math.sqrt(((p2[0] - p1[0]) ** 2) + ((p2[1] - p1[1]) ** 2))


def pol(*points, threshold=5):
    """Checks if all points are on single line"""
    if len(points) < 3:
        return
    d_sum = 0
    for i in range(0, len(points) - 1):
        d_sum += distance(points[i], points[i + 1])
    return abs(d_sum - distance(points[0], points[-1])) < threshold
