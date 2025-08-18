from visuals.presets import AbstractLinesVisualizer

def test_abstract_lines_visual():
    vis = AbstractLinesVisualizer((40, 8))
    img = vis.render()
    assert img.shape == (40, 8)
    assert img.max() == 1.0 and img.min() == 0.0
