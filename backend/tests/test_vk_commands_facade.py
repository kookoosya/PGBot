"""Smoke tests for vk commands package."""

from app.services.vk import commands
from app.services.vk.commands import aliases as aliases_mod
from app.services.vk.commands import handlers as handlers_mod


def test_commands_exports_handlers_map():
    assert commands.COMMAND_HANDLERS["welcome"] is handlers_mod.handle_welcome
    assert commands.COMMAND_HANDLERS["weather"] is handlers_mod.handle_weather


def test_commands_exports_aliases():
    assert commands.COMMAND_ALIASES is aliases_mod.COMMAND_ALIASES
    assert commands.COMMAND_ALIASES["погода"] == "weather"
