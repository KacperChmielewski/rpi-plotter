def circle(x0, y0, radius):
    f = 1 - radius
    ddf_x = 1
    ddf_y = -2 * radius
    x = 0
    y = radius
    out = []
    for i in range(8):
        out.append([])
    while x < y:
        if f >= 0:
            y -= 1
            ddf_y += 2
            f += ddf_y
        x += 1
        ddf_x += 2
        f += ddf_x
        out[0].append([x0 + x, y0 + y])
        out[1].append([x0 + y, y0 + x])
        out[2].append([x0 + y, y0 - x])
        out[3].append([x0 + x, y0 - y])
        out[4].append([x0 - x, y0 - y])
        out[5].append([x0 - y, y0 - x])
        out[6].append([x0 - y, y0 + x])
        out[7].append([x0 - x, y0 + y])

    out[1].reverse()
    out[3].reverse()
    out[5].reverse()
    out[7].reverse()

    output = open('circle.plo', 'w')

    for div in out:
        for part in div:
            com = 'GOTO {} {} 1\n'.format(str(part[0]), str(part[1]))
            output.write(com)

    output.close()


if __name__ == '__main__':
    print("executing circle(x0=37500, y0=37500, radius=2500), output=circle.plo")
    circle(x0=37500, y0=37500, radius=2500)
