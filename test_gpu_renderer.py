import unittest
import moderngl

class TestGPURenderer(unittest.TestCase):
    def test_not_llvmpipe(self):
        ctx = moderngl.create_standalone_context(require=330)
        renderer = ctx.info.get('GL_RENDERER', '').lower()
        ctx.release()
        self.assertNotIn('llvmpipe', renderer, f'Software renderer detected: {renderer}')

if __name__ == '__main__':
    unittest.main()
