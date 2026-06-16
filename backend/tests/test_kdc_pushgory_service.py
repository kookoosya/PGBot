"""Tests for KDC Pushgory HTML parsing."""

from app.services.kdc_pushgory_service import _parse_homepage


SAMPLE_HOME = """
<div class="cms-block-news news-tile">
  <div class="row tile-news-body">
    <div class="col-md-6 news_item">
      <a class="content_block" href="/item/999001">
        <span class="bottom_block">Театральный фестиваль в Бугрово 19 и 20 июня 2026</span>
      </a>
      <h4 class="text-center"><a href="/item/999001">Бугровский гарнец</a></h4>
    </div>
  </div>
</div>
"""


def test_parse_homepage_extracts_future_event():
    events = _parse_homepage(SAMPLE_HOME)
    assert len(events) == 1
    assert "гарнец" in events[0].title.lower()
    assert events[0].starts_at.day == 19
    assert events[0].ends_at is not None
    assert events[0].ends_at.day == 20
