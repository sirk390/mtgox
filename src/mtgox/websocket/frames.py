"""
Frames implemented as in:
    http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-76
Note: a new (very different) version of this spec was published at
      http://tools.ietf.org/html/rfc6455
"""

class MissingDataException(Exception):
    pass

def read_text_frame(buffer):
    """ return (frame, remaining)"""
    if len(buffer) and  0x00 <= ord(buffer[0]) <= 0x7F and "\xff" in buffer:
        frame_end = buffer.index("\xff")
        return buffer[1:frame_end], buffer[frame_end+1:]
    return None, buffer

def read_length(buffer):
    length = 0
    i = 0
    while i < len(buffer) and (ord(buffer[i]) & 0x80):
        b = ord(buffer[i])
        length = length * 128 + (b & 0x7f)
        i += 1
    return length, buffer[i:]

def read_binary_frame(buffer):
    length, buffer_bin = read_length(buffer)
    if length < len(buffer_bin):
        return None, buffer
    return buffer_bin[:length], buffer_bin[length:]

def read_frame(buffer):
    """ return (frame, remaining), raises MissingDataException """
    if len(buffer) > 0:
        frame_type = ord(buffer[0])
        if frame_type == 0x00:
            return read_text_frame(buffer)
        if  frame_type  & 0x80: # see section 4.2 Data framing
            return read_binary_frame(buffer)
    return (None, buffer)

def read_frames(buffer):
    """ return (frames, remaining) """
    frames = []
    frame, buffer = read_frame(buffer)
    while (frame is not None):
        frames.append(frame)
        frame, buffer = read_frame(buffer)
    return frames, buffer