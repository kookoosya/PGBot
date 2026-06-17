"""Smoke tests for vk.flows package exports."""

import app.services.vk.flows as pkg
from app.services.vk.flows import classified as classified_mod
from app.services.vk.flows import listings as listings_mod
from app.services.vk.flows import map_report as map_report_mod
from app.services.vk.flows import router as router_mod
from app.services.vk.flows import wish as wish_mod
from app.services.vk.flows.common import clear_flow as clear_flow_fn


def test_package_exports_flow_starters():
    assert pkg.start_classified_flow is classified_mod.start_classified_flow
    assert pkg.start_wish_flow is wish_mod.start_wish_flow
    assert pkg.start_map_report_flow is map_report_mod.start_map_report_flow


def test_package_exports_router():
    assert pkg.handle_flow_message is router_mod.handle_flow_message


def test_package_exports_listings():
    assert pkg.format_jobs_message is listings_mod.format_jobs_message
    assert pkg.format_routes_message is listings_mod.format_routes_message


def test_package_exports_common():
    assert pkg.clear_flow is clear_flow_fn
    assert pkg.get_flow is not None
