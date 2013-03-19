def idGenerator(maximum):
    i = 0
    while True:
        yield i
        i = (i + 1) % maximum
