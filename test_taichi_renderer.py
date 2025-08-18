import taichi as ti
from render.taichi_renderer import TaichiRenderer

@ti.kernel
def fill_gradient(img: ti.template()):
    for i, j in img:
        img[i, j] = i / img.shape[0]

def test_gradient_render():
    renderer = TaichiRenderer(resolution=(4, 4))
    renderer.add_pass("gradient", fill_gradient)
    result = renderer.render()
    assert result.shape == (4, 4)
    assert result[0, 0] == 0.0
    assert abs(result[3, 0] - 0.75) < 1e-3
