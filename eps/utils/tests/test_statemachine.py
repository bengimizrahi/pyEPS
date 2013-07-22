import unittest

from eps.utils.statemachine import StateMachine, State


class TestStateMachine(unittest.TestCase):

    def test_basicUsage(self):
        testcase = self
        testcase.result = False
        class State1(State):
            def handlerA(self, *args, **kwargs):
                testcase.assertEqual(args, (1, 2))
                testcase.assertEqual(kwargs, {"key": "value"})
                self.changeState(State2)
            def handlerB(self, *args, **kwargs):
                self.changeState(State2)

        class State2(State):
            def handlerC(self, *args, **kwargs):
                self.changeState(State1)
            def handlerD(self, *args, **kwargs):
                testcase.result = True

        class StateMachineX(StateMachine):
            def __init__(self):
                super(StateMachineX, self).__init__()
                self.changeState(State1)

        stateMachine = StateMachineX()
        stateMachine.handleCommand("handlerA", 1, 2, key="value")
        stateMachine.handleCommand("handlerC")
        stateMachine.handleCommand("handlerB")
        stateMachine.handleCommand("handlerD")
        self.assertTrue(self.result)

if __name__ == "__main__":
    unittest.main()