import cereal.messaging as messaging

sm = messaging.SubMaster(['pandaStates'])
while True:
    states = messaging.recv_one_retry(sm.sock['pandaStates']).pandaStates
    for state in states:
        print("PANDA STATE " + str(state))
