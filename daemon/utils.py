from datetime import datetime

def nearest_forward_ring_index(table):
    nowtime = [datetime.now().hour, datetime.now().minute]
    nearest = -1
    for i in range(len(table)):
        tsplit = table[i].split(":")
        if int(tsplit[0]) > nowtime[0] or (int(tsplit[0]) == nowtime[0] and int(tsplit[1]) > nowtime[1]):
            nearest = i
            break

    return nearest