from pyte import Stream

def feed_str(self, s):
    assert isinstance(s, str)
    return self.feed(s.encode("utf-8"))

Stream.feed_str = feed_str
