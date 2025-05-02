__vhfront_msgs = {}

def load(vhfront_msgs_file):
    global __vhfront_msgs
    with open(vhfront_msgs_file+'.json',encoding='utf-8') as _front_msgs_file:
        import json
        __vhfront_msgs = json.load(_front_msgs_file)

def vhfront_msg(msg):
    return __vhfront_msgs.get(msg,msg)
