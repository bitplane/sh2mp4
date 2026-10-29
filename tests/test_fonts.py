import pytest

from sh2mp4.fonts import FontMetrics, calculate_window_dimensions


async def test_custom_font_uses_supplied_display(monkeypatch):
    calls = []

    async def measure(name, size, display):
        calls.append((name, size, display))
        return FontMetrics(size, size * 2)

    monkeypatch.setattr("sh2mp4.fonts.measure_font", measure)
    small = await calculate_window_dimensions(80, 24, "Liberation Mono", 8, ":123")
    large = await calculate_window_dimensions(80, 24, "Liberation Mono", 20, ":123")
    assert large[0] > small[0]
    assert calls[-1] == ("Liberation Mono", 20, ":123")


async def test_measurement_failure_is_not_silently_substituted(monkeypatch):
    async def fail(*args):
        raise RuntimeError("font measurement failed")

    monkeypatch.setattr("sh2mp4.fonts.measure_font", fail)
    with pytest.raises(RuntimeError, match="measurement failed"):
        await calculate_window_dimensions(80, 24, "Liberation Mono", 20, ":123")
