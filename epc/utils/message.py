def verify(message):
    required = ("source", "via", "payload")
    t = map(lambda k: message.get(k), required)
    return all(t)
