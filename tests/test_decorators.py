from enum import Enum

from statewire.core import StateMachine
from statewire.decorators import MachineConfig, on_enter, on_exit


class TestDecoratorBasic:
    def test_on_enter_marks_method(self) -> None:
        @on_enter("ON")
        def handler(**_kwargs: object) -> None:
            pass

        assert handler._on_enter_state == "ON"  # type: ignore[attr-defined]

    def test_on_exit_marks_method(self) -> None:
        @on_exit("OFF")
        def handler(**_kwargs: object) -> None:
            pass

        assert handler._on_exit_state == "OFF"  # type: ignore[attr-defined]

    def test_on_enter_with_enum(self) -> None:
        class S(Enum):
            ON = "on"

        @on_enter(S.ON)
        def handler(**_kwargs: object) -> None:
            pass

        assert handler._on_enter_state == "on"  # type: ignore[attr-defined]

    def test_on_exit_with_enum(self) -> None:
        class S(Enum):
            OFF = "off"

        @on_exit(S.OFF)
        def handler(**_kwargs: object) -> None:
            pass

        assert handler._on_exit_state == "off"  # type: ignore[attr-defined]


class TestMachineConfigBuild:
    def test_build_returns_state_machine(self) -> None:
        class LightConfig(MachineConfig):
            name = "Light"
            states = ["OFF", "ON"]
            events = ["TOGGLE"]
            initial = "OFF"
            transitions = [
                {"source": "OFF", "event": "TOGGLE", "target": "ON"},
                {"source": "ON", "event": "TOGGLE", "target": "OFF"},
            ]

        config = LightConfig()
        sm = config.build()

        assert isinstance(sm, StateMachine)
        assert sm.name == "Light"
        assert sm.state == "OFF"

    def test_build_transitions_work(self) -> None:
        class LightConfig(MachineConfig):
            name = "Light"
            states = ["OFF", "ON"]
            events = ["TOGGLE"]
            initial = "OFF"
            transitions = [
                {"source": "OFF", "event": "TOGGLE", "target": "ON"},
                {"source": "ON", "event": "TOGGLE", "target": "OFF"},
            ]

        sm = LightConfig().build()
        sm.trigger("TOGGLE")
        assert sm.state == "ON"
        sm.trigger("TOGGLE")
        assert sm.state == "OFF"

    def test_build_with_enum_states(self) -> None:
        class S(Enum):
            OFF = "off"
            ON = "on"

        class E(Enum):
            TOGGLE = "toggle"

        class LightConfig(MachineConfig):
            name = "Light"
            states = S
            events = E
            initial = S.OFF
            transitions = [
                {"source": S.OFF, "event": E.TOGGLE, "target": S.ON},
                {"source": S.ON, "event": E.TOGGLE, "target": S.OFF},
            ]

        sm = LightConfig().build()
        assert sm.state == "off"
        sm.trigger(E.TOGGLE)
        assert sm.state == "on"


class TestMachineConfigHooks:
    def test_on_enter_hook_called(self) -> None:
        log: list[str] = []

        class LightConfig(MachineConfig):
            name = "Light"
            states = ["OFF", "ON"]
            events = ["TOGGLE"]
            initial = "OFF"
            transitions = [
                {"source": "OFF", "event": "TOGGLE", "target": "ON"},
            ]

            @on_enter("ON")
            def entered_on(self, **_kwargs: object) -> None:
                log.append("entered_ON")

        sm = LightConfig().build()
        sm.trigger("TOGGLE")
        assert "entered_ON" in log

    def test_on_exit_hook_called(self) -> None:
        log: list[str] = []

        class LightConfig(MachineConfig):
            name = "Light"
            states = ["OFF", "ON"]
            events = ["TOGGLE"]
            initial = "OFF"
            transitions = [
                {"source": "OFF", "event": "TOGGLE", "target": "ON"},
            ]

            @on_exit("OFF")
            def exited_off(self, **_kwargs: object) -> None:
                log.append("exited_OFF")

        sm = LightConfig().build()
        sm.trigger("TOGGLE")
        assert "exited_OFF" in log

    def test_hook_execution_order(self) -> None:
        log: list[str] = []

        class LightConfig(MachineConfig):
            name = "Light"
            states = ["OFF", "ON"]
            events = ["TOGGLE"]
            initial = "OFF"
            transitions = [
                {"source": "OFF", "event": "TOGGLE", "target": "ON"},
            ]

            @on_exit("OFF")
            def exited_off(self, **_kwargs: object) -> None:
                log.append("exited_OFF")

            @on_enter("ON")
            def entered_on(self, **_kwargs: object) -> None:
                log.append("entered_ON")

        sm = LightConfig().build()
        sm.trigger("TOGGLE")
        assert log == ["exited_OFF", "entered_ON"]
