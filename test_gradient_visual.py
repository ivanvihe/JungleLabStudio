from visuals.presets import GradientVisual

def test_gradient_visual():
    visual = GradientVisual((4, 4))
    img = visual.render()
    assert img.shape == (4, 4)
    assert img[0, 0] == 0.0
    assert abs(img[0, 3] - 0.75) < 1e-3
